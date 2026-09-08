import os
import json
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Candidate, AssessmentSession
from ..config import UPLOAD_DIR, MAX_RESUME_BYTES
from ..services.resume_parser import ResumeParser
from ..services.ai_engine import AIEngine

router = APIRouter(prefix="/api/candidate", tags=["Candidate"])

@router.post("/register")
async def register_candidate(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    applied_role: str = Form(...),
    years_of_experience: float = Form(...),
    current_company: str = Form(""),
    resume: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Years of experience is compulsory and must be a non-negative number entered by the
    # candidate (a fresher enters 0). It is never predicted from the resume.
    if years_of_experience is None or years_of_experience < 0:
        raise HTTPException(status_code=400, detail="Total relevant experience (years) is required and cannot be negative.")

    resume_filename = None
    resume_text = ""
    extracted_skills = []
    resume_bytes = None
    resume_mime = None

    if resume and resume.filename:
        # Strip any path components from the client-supplied filename before joining it
        # to UPLOAD_DIR, so a crafted name like "../../x" cannot escape the uploads dir.
        safe_name = os.path.basename(resume.filename.replace("\\", "/"))
        unique_filename = f"{uuid.uuid4().hex}_{safe_name}"
        saved_path = os.path.join(UPLOAD_DIR, unique_filename)

        resume_bytes = await resume.read()
        if len(resume_bytes) > MAX_RESUME_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Resume is too large. The maximum size is {MAX_RESUME_BYTES // (1024 * 1024)} MB.",
            )
        resume_mime = resume.content_type or "application/octet-stream"

        # Written to disk as well because the resume parser reads from a path, and a local
        # copy is a useful cache. The bytes stored on the candidate row are the durable
        # copy: on a host with an ephemeral filesystem the file below does not survive a
        # restart, but the database row does.
        with open(saved_path, "wb") as buffer:
            buffer.write(resume_bytes)

        resume_filename = unique_filename
        resume_text = ResumeParser.extract_text(saved_path)
        analysis = ResumeParser.analyze_resume(resume_text)
        extracted_skills = analysis["detected_skills"]
        # Experience is taken ONLY from what the candidate entered on the form — never
        # predicted/guessed from the resume.

    candidate = Candidate(
        full_name=full_name.strip(),
        email=email.strip().lower(),
        phone=phone.strip(),
        applied_role=applied_role,
        years_of_experience=years_of_experience,
        current_company=current_company.strip(),
        resume_filename=resume_filename,
        resume_data=resume_bytes,
        resume_mime=resume_mime,
        resume_size=len(resume_bytes) if resume_bytes else None,
        resume_text=resume_text,
        extracted_skills=str(extracted_skills)
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    # -------------------------------------------------------------
    # ADAPTIVE EXAM: questions are NOT pre-generated. Finance (48) and IQ (16) are
    # served in batches of 5 by the adaptive engine as the candidate progresses.
    # Only the 16 resume-verification questions are prepared now (from the uploaded
    # resume) and stashed on the session; they are served last, unchanged.
    # Section/tier state starts at finance / Basic.
    # -------------------------------------------------------------
    resume_questions = AIEngine.generate_resume_questions(resume_text, extracted_skills, applied_role)

    session = AssessmentSession(
        candidate_id=candidate.id,
        applied_role=applied_role,
        status="registered",
        current_section="finance",
        current_tier="Basic",
        current_batch_size=0,
        finance_served=0,
        iq_served=0,
        resume_served=0,
        pending_resume=json.dumps(resume_questions),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "success": True,
        "session_id": session.id,
        "candidate_id": candidate.id,
        "full_name": candidate.full_name,
        "applied_role": candidate.applied_role,
        "total_questions": 80,
        "duration_minutes": 60
    }


@router.post("/parse-resume-preview")
async def parse_resume_preview(resume: UploadFile = File(...)):
    """Instantly parses uploaded resume and returns extracted name, email, phone, skills, and degree for form auto-population."""
    if not resume or not resume.filename:
        raise HTTPException(status_code=400, detail="No resume uploaded")
        
    unique_filename = f"temp_{uuid.uuid4().hex}_{resume.filename}"
    temp_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)
        
    resume_text = ResumeParser.extract_text(temp_path)
    analysis = ResumeParser.analyze_resume(resume_text)
    
    # Clean up temp file
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except:
        pass

    return {
        "success": True,
        "full_name": analysis.get("full_name", ""),
        "email": analysis.get("email", ""),
        "phone": analysis.get("phone", ""),
        "primary_domain": analysis.get("primary_domain", "General"),
        "detected_degrees": analysis.get("detected_degrees", []),
        "cgpa": analysis.get("cgpa", ""),
        "estimated_years": analysis.get("estimated_years", 0.0),
        "detected_skills": analysis.get("detected_skills", [])
    }
