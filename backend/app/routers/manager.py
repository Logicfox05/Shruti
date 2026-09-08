import os
import re
import io as _io
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AssessmentSession, Candidate, SessionQuestion, ProctoringEvent, Manager, AuditLog
from ..config import UPLOAD_DIR
from ..schemas import ManagerLoginRequest, ManagerCreateRequest, PasswordChangeRequest
from ..auth import (
    require_manager, require_admin, create_token, verify_password, hash_password, record_audit,
)
from ..services.ai_engine import AIEngine
from ..services.scoring import ScoringService

router = APIRouter(prefix="/api/manager", tags=["Manager Dashboard"])

# A syntactically valid bcrypt hash that no password can match. Used so a login attempt
# for an unknown email still performs a hash comparison and takes a similar amount of
# time as a real one, instead of returning instantly and revealing that the email is
# not registered.
_DUMMY_HASH = "$2b$12$" + "." * 53


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
@router.post("/login")
async def manager_login(payload: ManagerLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Exchange manager credentials for a session token. This is the only manager
    endpoint that does not require a token; every other one does."""
    email = (payload.email or "").strip().lower()
    if email:
        manager = db.query(Manager).filter(Manager.email == email).first()
    else:
        # A client that sends only a password (older frontend) is treated as signing in
        # to the bootstrap administrator account.
        manager = (db.query(Manager).filter(Manager.role == "admin")
                   .order_by(Manager.created_at.asc()).first())

    password_ok = verify_password(payload.password or "",
                                  manager.password_hash if manager else _DUMMY_HASH)

    if not manager or not password_ok:
        record_audit(db, None, "login_failed", details="email=" + (email or "(none)"), request=request)
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not manager.is_active:
        raise HTTPException(status_code=403, detail="This manager account has been deactivated.")

    manager.last_login_at = datetime.utcnow()
    db.commit()
    record_audit(db, manager, "login", request=request)

    return {
        "success": True,
        "token": create_token(manager),
        "manager": {
            "id": manager.id, "email": manager.email, "full_name": manager.full_name,
            "role": manager.role, "must_change_password": manager.must_change_password,
        },
    }


@router.get("/me")
async def whoami(manager: Manager = Depends(require_manager)):
    return {
        "id": manager.id, "email": manager.email, "full_name": manager.full_name,
        "role": manager.role, "must_change_password": manager.must_change_password,
        "last_login_at": manager.last_login_at,
    }


@router.post("/change-password")
async def change_password(payload: PasswordChangeRequest, request: Request,
                          manager: Manager = Depends(require_manager),
                          db: Session = Depends(get_db)):
    if not verify_password(payload.current_password or "", manager.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    if len(payload.new_password or "") < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters.")
    manager.password_hash = hash_password(payload.new_password)
    manager.must_change_password = False
    db.commit()
    record_audit(db, manager, "change_password", "manager", manager.id, request=request)
    return {"success": True}


# ---------------------------------------------------------------------------
# Manager accounts (administrators only)
# ---------------------------------------------------------------------------
@router.get("/managers")
async def list_managers(admin: Manager = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Manager).order_by(Manager.created_at.asc()).all()
    return [{
        "id": m.id, "email": m.email, "full_name": m.full_name, "role": m.role,
        "is_active": m.is_active, "must_change_password": m.must_change_password,
        "created_at": m.created_at, "last_login_at": m.last_login_at,
    } for m in rows]


@router.post("/managers")
async def create_manager(payload: ManagerCreateRequest, request: Request,
                         admin: Manager = Depends(require_admin), db: Session = Depends(get_db)):
    email = (payload.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email address is required.")
    if len(payload.password or "") < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if payload.role not in ("admin", "recruiter"):
        raise HTTPException(status_code=400, detail="Role must be admin or recruiter.")
    if db.query(Manager).filter(Manager.email == email).first():
        raise HTTPException(status_code=409, detail="A manager with that email already exists.")

    manager = Manager(
        email=email, full_name=(payload.full_name or "").strip() or email,
        password_hash=hash_password(payload.password), role=payload.role, is_active=True,
    )
    db.add(manager)
    db.commit()
    record_audit(db, admin, "create_manager", "manager", manager.id, details=email, request=request)
    return {"success": True, "id": manager.id}


@router.patch("/managers/{manager_id}/active")
async def set_manager_active(manager_id: str, active: bool, request: Request,
                             admin: Manager = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.query(Manager).filter(Manager.id == manager_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Manager not found")
    if target.id == admin.id and not active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account.")
    if not active and target.role == "admin":
        remaining = db.query(Manager).filter(
            Manager.role == "admin", Manager.is_active.is_(True), Manager.id != target.id
        ).count()
        if remaining == 0:
            raise HTTPException(status_code=400, detail="At least one active administrator must remain.")
    target.is_active = active
    db.commit()
    record_audit(db, admin, "activate_manager" if active else "deactivate_manager",
                 "manager", target.id, details=target.email, request=request)
    return {"success": True}


@router.get("/audit-log")
async def read_audit_log(limit: int = 200, admin: Manager = Depends(require_admin),
                         db: Session = Depends(get_db)):
    rows = (db.query(AuditLog).order_by(AuditLog.created_at.desc())
            .limit(max(1, min(limit, 1000))).all())
    return [{
        "created_at": r.created_at, "manager_email": r.manager_email, "action": r.action,
        "target_type": r.target_type, "target_id": r.target_id,
        "details": r.details, "ip_address": r.ip_address,
    } for r in rows]


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------
# Matches a trailing "... at 5:04:08 pm" style wall-clock in a proctoring message.
_TRAILING_TIME = re.compile(r"\s*\bat\s+(\d{1,2}:\d{2}(?::\d{2})?\s*[ap]\.?m\.?)\s*$", re.IGNORECASE)


def _clean_details_and_clock(details, client_time, created_at):
    """Return (clean message, single wall-clock time). The clock is the candidate's own
    local time: prefer the stored client_time, else the time embedded in the message,
    else the server time. The embedded time is stripped from the message so it is never
    shown twice."""
    details = details or ""
    embedded = ""
    m = _TRAILING_TIME.search(details)
    if m:
        embedded = m.group(1).strip()
        details = _TRAILING_TIME.sub("", details).strip()
    clock = (client_time or "").strip() or embedded or created_at.strftime("%I:%M:%S %p")
    return details, clock


@router.get("/candidates")
async def get_all_candidates(
    role: Optional[str] = None,
    verdict: Optional[str] = None,
    manager: Manager = Depends(require_manager),
    db: Session = Depends(get_db),
):
    query = db.query(AssessmentSession).join(Candidate)
    if role:
        query = query.filter(AssessmentSession.applied_role == role)
    if verdict:
        query = query.filter(AssessmentSession.role_fit_verdict == verdict)

    sessions = query.order_by(AssessmentSession.created_at.desc()).all()

    results = []
    for s in sessions:
        results.append({
            "session_id": s.id,
            "candidate_id": s.candidate.id,
            "full_name": s.candidate.full_name,
            "email": s.candidate.email,
            "phone": s.candidate.phone,
            "applied_role": s.applied_role,
            "years_of_experience": s.candidate.years_of_experience,
            "current_company": s.candidate.current_company or "N/A",
            "status": s.status,
            "total_score": round(s.total_score, 1),
            "max_score": s.max_score,
            "percentage": round(s.percentage, 1),
            "role_fit_verdict": s.role_fit_verdict or "Pending Review",
            "integrity_score": s.integrity_score,
            "created_at": s.created_at.strftime("%d %b %Y, %I:%M %p")
        })
    return results


@router.get("/candidate/{session_id}/report")
async def get_candidate_report(session_id: str, manager: Manager = Depends(require_manager),
                               db: Session = Depends(get_db)):
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # The intelligence report is only meaningful once the candidate has actually
    # submitted. Until then the row stays "Pending Review" and the analysis is locked.
    if session.status != "submitted":
        raise HTTPException(
            status_code=409,
            detail="This candidate has not submitted the assessment yet — the analysis is available only after submission."
        )

    questions = db.query(SessionQuestion).filter(
        SessionQuestion.session_id == session_id
    ).order_by(SessionQuestion.question_number).all()

    proctoring_logs = db.query(ProctoringEvent).filter(
        ProctoringEvent.session_id == session_id
    ).order_by(ProctoringEvent.created_at.asc()).all()

    # Always recalculate score dynamically to guarantee precision based on actual answers
    ScoringService.calculate_session_score(session, questions)

    # Generate fresh, dynamic 3-Tier Multi-Level intelligence report
    report_data = AIEngine.generate_hiring_report(session.candidate, session, questions, proctoring_logs)

    session.role_fit_verdict = report_data["hiring_verdict"]
    session.integrity_score = report_data["integrity_score"]
    session.percentage = report_data["overall_score"]
    session.summary_report = json.dumps(report_data)
    db.commit()

    logs_list = []
    for e in proctoring_logs:
        det, clock = _clean_details_and_clock(e.details, getattr(e, "client_time", ""), e.created_at)
        logs_list.append({
            "event_type": e.event_type,
            "details": det,
            "timestamp_seconds": e.timestamp_seconds,
            # Elapsed time from exam start (unambiguous) + a single wall-clock in the
            # candidate's own local time.
            "time_str": f"{e.timestamp_seconds // 60:02d}:{e.timestamp_seconds % 60:02d}",
            "created_at": clock,
        })

    return {
        "session_id": session.id,
        "candidate": {
            "id": session.candidate.id,
            "full_name": session.candidate.full_name,
            "email": session.candidate.email,
            "phone": session.candidate.phone,
            "applied_role": session.applied_role,
            "years_of_experience": session.candidate.years_of_experience,
            "current_company": session.candidate.current_company,
            "resume_filename": session.candidate.resume_filename
        },
        "assessment": {
            "status": session.status,
            "total_score": session.total_score,
            "max_score": session.max_score,
            "percentage": session.percentage,
            "role_fit_verdict": session.role_fit_verdict,
            "integrity_score": session.integrity_score
        },
        "report": report_data,
        "proctoring_logs": logs_list
    }


@router.get("/candidate/{session_id}/download-resume")
async def download_resume(session_id: str, request: Request,
                          manager: Manager = Depends(require_manager),
                          db: Session = Depends(get_db)):
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session or not session.candidate.resume_filename:
        raise HTTPException(status_code=404, detail="Resume not found")

    candidate = session.candidate
    record_audit(db, manager, "download_resume", "candidate", candidate.id,
                 details=candidate.email, request=request)

    # Preferred source: the bytes held in the database, which survive a restart on a host
    # with an ephemeral filesystem. Older records that predate this fall back to disk.
    if candidate.resume_data:
        disposition = 'attachment; filename="' + candidate.resume_filename + '"'
        return StreamingResponse(
            _io.BytesIO(candidate.resume_data),
            media_type=candidate.resume_mime or "application/octet-stream",
            headers={"Content-Disposition": disposition},
        )

    file_path = os.path.join(UPLOAD_DIR, candidate.resume_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Resume file missing on server")
    return FileResponse(file_path, filename=candidate.resume_filename)


@router.delete("/candidate/{session_id}")
async def delete_candidate(session_id: str, request: Request,
                           manager: Manager = Depends(require_manager),
                           db: Session = Depends(get_db)):
    """Permanently delete one candidate's submission (and their answers + proctoring log).
    If the candidate has no other submissions, the candidate record and their uploaded
    resume file are removed too."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    candidate = session.candidate
    candidate_id = candidate.id if candidate else None
    candidate_email = candidate.email if candidate else None
    resume_name = candidate.resume_filename if candidate else None

    db.delete(session)  # cascades session_questions + proctoring_events
    db.flush()

    removed_resume = False
    if candidate_id:
        remaining = db.query(AssessmentSession).filter(AssessmentSession.candidate_id == candidate_id).count()
        if remaining == 0:
            cand = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if cand:
                db.delete(cand)
                removed_resume = True
    db.commit()
    record_audit(db, manager, "delete_candidate", "candidate", candidate_id,
                 details=candidate_email, request=request)

    if removed_resume and resume_name:
        try:
            os.remove(os.path.join(UPLOAD_DIR, resume_name))
        except OSError:
            pass
    return {"success": True}


@router.delete("/candidates")
async def delete_all_candidates(request: Request,
                                manager: Manager = Depends(require_manager),
                                db: Session = Depends(get_db)):
    """Permanently delete every candidate record (submissions, answers, proctoring logs)
    and their uploaded resumes. Used by the 'Delete All' action."""
    for c in db.query(Candidate).all():
        if c.resume_filename:
            try:
                os.remove(os.path.join(UPLOAD_DIR, c.resume_filename))
            except OSError:
                pass
    deleted = db.query(Candidate).count()
    # Bulk deletes bypass ORM cascade, so clear children first in FK-safe order.
    db.query(ProctoringEvent).delete()
    db.query(SessionQuestion).delete()
    db.query(AssessmentSession).delete()
    db.query(Candidate).delete()
    db.commit()
    record_audit(db, manager, "delete_all_candidates", "candidate", None,
                 details=str(deleted) + " candidate(s) removed", request=request)
    return {"success": True, "deleted": deleted}
