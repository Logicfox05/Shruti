import os
import re
import json
import hmac
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AssessmentSession, Candidate, SessionQuestion, ProctoringEvent
from ..config import UPLOAD_DIR, MANAGER_PASSWORD
from ..schemas import ManagerLoginRequest
from ..auth import manager_token, require_manager
from ..services.ai_engine import AIEngine
from ..services.scoring import ScoringService

router = APIRouter(prefix="/api/manager", tags=["Manager Dashboard"])


@router.post("/login")
async def manager_login(payload: ManagerLoginRequest):
    """Exchange the manager password for a session token. This is the only manager
    endpoint that does NOT require the token; every other one does."""
    supplied = payload.password or ""
    if not MANAGER_PASSWORD or not hmac.compare_digest(supplied, MANAGER_PASSWORD):
        raise HTTPException(status_code=401, detail="Incorrect manager password.")
    return {"success": True, "token": manager_token(MANAGER_PASSWORD)}

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

@router.get("/candidates", dependencies=[Depends(require_manager)])
async def get_all_candidates(
    role: Optional[str] = None,
    verdict: Optional[str] = None,
    db: Session = Depends(get_db)
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

@router.get("/candidate/{session_id}/report", dependencies=[Depends(require_manager)])
async def get_candidate_report(session_id: str, db: Session = Depends(get_db)):
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

    # Always recalculate score dynamically to guarantee 100% precision based on candidate actual answers
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

@router.get("/candidate/{session_id}/download-resume", dependencies=[Depends(require_manager)])
async def download_resume(session_id: str, db: Session = Depends(get_db)):
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session or not session.candidate.resume_filename:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    file_path = os.path.join(UPLOAD_DIR, session.candidate.resume_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Resume file missing on server")

    return FileResponse(file_path, filename=session.candidate.resume_filename)


@router.delete("/candidate/{session_id}", dependencies=[Depends(require_manager)])
async def delete_candidate(session_id: str, db: Session = Depends(get_db)):
    """Permanently delete one candidate's submission (and their answers + proctoring log).
    If the candidate has no other submissions, the candidate record and their uploaded
    resume file are removed too."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    candidate = session.candidate
    candidate_id = candidate.id if candidate else None
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

    if removed_resume and resume_name:
        try:
            os.remove(os.path.join(UPLOAD_DIR, resume_name))
        except OSError:
            pass
    return {"success": True}


@router.delete("/candidates", dependencies=[Depends(require_manager)])
async def delete_all_candidates(db: Session = Depends(get_db)):
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
    return {"success": True, "deleted": deleted}
