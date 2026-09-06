from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class ManagerLoginRequest(BaseModel):
    password: str

class CandidateRegisterRequest(BaseModel):
    full_name: str
    email: str
    phone: str
    applied_role: str
    years_of_experience: Optional[float] = 0.0
    current_company: Optional[str] = ""

class QuestionPublic(BaseModel):
    id: str
    question_number: int
    category: str
    topic: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    selected_option: Optional[str] = None
    is_flagged: Optional[bool] = False
    is_resume_based: Optional[bool] = False

class AssessmentStartResponse(BaseModel):
    session_id: str
    candidate_name: str
    applied_role: str
    total_questions: int
    duration_minutes: int
    remaining_seconds: int
    questions: List[QuestionPublic]

class AnswerAutoSaveRequest(BaseModel):
    question_id: str
    selected_option: Optional[str] = None
    is_flagged: Optional[bool] = False
    time_spent_seconds: Optional[int] = 0

class ProctoringLogRequest(BaseModel):
    session_id: str
    event_type: str
    details: Optional[str] = ""
    timestamp_seconds: int
    client_time: Optional[str] = ""   # candidate's local wall-clock time at the event

class CandidateSummary(BaseModel):
    session_id: str
    candidate_id: str
    full_name: str
    email: str
    phone: str
    applied_role: str
    years_of_experience: float
    status: str
    total_score: float
    max_score: float
    percentage: float
    role_fit_verdict: Optional[str]
    integrity_score: float
    created_at: datetime
