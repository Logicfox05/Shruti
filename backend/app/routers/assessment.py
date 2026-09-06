from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AssessmentSession, SessionQuestion, ProctoringEvent
from ..schemas import AssessmentStartResponse, QuestionPublic, AnswerAutoSaveRequest
from ..services.scoring import ScoringService
from ..services.ai_engine import AIEngine
from ..services.adaptive_engine import AdaptiveService, SECTION_QUOTA

router = APIRouter(prefix="/api/assessment", tags=["Assessment"])

TOTAL_QUESTIONS = sum(SECTION_QUOTA.values())  # 80


def _public(q: SessionQuestion) -> QuestionPublic:
    return QuestionPublic(
        id=q.id,
        question_number=q.question_number,
        category=q.category,
        topic=q.topic,
        question_text=q.question_text,
        option_a=q.option_a,
        option_b=q.option_b,
        option_c=q.option_c,
        option_d=q.option_d,
        selected_option=q.selected_option,
        is_flagged=q.is_flagged,
        is_resume_based=q.is_resume_based,
    )


def _served(session_id: str, db: Session):
    return db.query(SessionQuestion).filter(
        SessionQuestion.session_id == session_id
    ).order_by(SessionQuestion.question_number).all()


def _active_batch_start(served, session) -> int:
    """1-based question_number of the first question in the current (outstanding)
    batch. Everything before it is locked/read-only."""
    if not served:
        return 1
    k = session.current_batch_size or 0
    return served[-1].question_number - k + 1 if k else served[-1].question_number


@router.get("/{session_id}/start")
async def start_assessment(session_id: str, db: Session = Depends(get_db)):
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "registered":
        session.status = "in_progress"
        session.start_time = datetime.utcnow()
        session.end_time = session.start_time + timedelta(minutes=session.duration_minutes)
        db.commit()

    # Serve the opening batch if this is a fresh start; otherwise (reload) we simply
    # return whatever has already been served so the client can rebuild its state.
    AdaptiveService.ensure_first_batch(session, db)

    remaining_seconds = session.duration_minutes * 60
    if session.start_time:
        elapsed = (datetime.utcnow() - session.start_time).total_seconds()
        remaining_seconds = max(0, int((session.duration_minutes * 60) - elapsed))

    served = _served(session_id, db)
    return {
        "session_id": session.id,
        "candidate_name": session.candidate.full_name,
        "applied_role": session.applied_role,
        "total_questions": TOTAL_QUESTIONS,
        "duration_minutes": session.duration_minutes,
        "remaining_seconds": remaining_seconds,
        "status": session.status,
        "questions": [_public(q) for q in served],
        "active_batch_start": _active_batch_start(served, session),
        "finished": session.current_section == "complete",
    }


@router.post("/{session_id}/submit-batch")
async def submit_batch(session_id: str, db: Session = Depends(get_db)):
    """Grade the outstanding batch of 5 (answers were autosaved), let the adaptive
    engine pick the next tier/section, and return the next batch (or finished=true)."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="Assessment is not in progress")

    new_rows = AdaptiveService.grade_and_advance(session, db)
    served = _served(session_id, db)
    return {
        "success": True,
        "new_questions": [_public(q) for q in new_rows],
        "active_batch_start": _active_batch_start(served, session),
        "served_count": len(served),
        "total_questions": TOTAL_QUESTIONS,
        "finished": session.current_section == "complete",
    }

@router.post("/{session_id}/autosave")
async def autosave_answer(session_id: str, payload: AnswerAutoSaveRequest, db: Session = Depends(get_db)):
    question = db.query(SessionQuestion).filter(
        SessionQuestion.id == payload.question_id,
        SessionQuestion.session_id == session_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    question.selected_option = payload.selected_option
    question.is_flagged = payload.is_flagged or False
    if payload.time_spent_seconds:
        question.time_spent_seconds += payload.time_spent_seconds
    question.answered_at = datetime.utcnow()
    db.commit()

    return {"success": True, "question_number": question.question_number}

@router.post("/{session_id}/submit")
async def submit_assessment(session_id: str, db: Session = Depends(get_db)):
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.status = "submitted"
    session.end_time = datetime.utcnow()

    questions = db.query(SessionQuestion).filter(SessionQuestion.session_id == session_id).all()
    proctoring_events = db.query(ProctoringEvent).filter(ProctoringEvent.session_id == session_id).all()

    # Calculate objective score
    ScoringService.calculate_session_score(session, questions)

    # Generate full Manager Intelligence Report
    report = AIEngine.generate_hiring_report(session.candidate, session, questions, proctoring_events)
    session.role_fit_verdict = report["hiring_verdict"]
    session.integrity_score = report["integrity_score"]
    
    import json
    session.summary_report = json.dumps(report)
    db.commit()

    # Return CLEAN response with zero scores exposed to the candidate
    return {
        "success": True,
        "message": "Your assessment has been submitted successfully. Management will review your submission and contact you regarding the next steps."
    }
