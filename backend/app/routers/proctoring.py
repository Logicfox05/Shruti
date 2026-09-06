from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ProctoringEvent, AssessmentSession
from ..schemas import ProctoringLogRequest

router = APIRouter(prefix="/api/proctoring", tags=["Proctoring"])

@router.post("/log")
async def log_proctoring_event(payload: ProctoringLogRequest, db: Session = Depends(get_db)):
    session = db.query(AssessmentSession).filter(AssessmentSession.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    event = ProctoringEvent(
        session_id=payload.session_id,
        event_type=payload.event_type,
        details=payload.details,
        timestamp_seconds=payload.timestamp_seconds,
        client_time=payload.client_time or ""
    )
    db.add(event)
    db.commit()

    return {"success": True, "event_id": event.id}
