import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean, DateTime, ForeignKey, LargeBinary, Index
)
from sqlalchemy.orm import relationship
from .database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    applied_role = Column(String(50), nullable=False) # Accountant, Senior Accountant, Finance Manager
    years_of_experience = Column(Float, default=0.0)
    current_company = Column(String(100), nullable=True)
    resume_filename = Column(String(255), nullable=True)
    # The resume file itself is stored in the database so it survives on hosts with an
    # ephemeral filesystem. `resume_filename` is kept for display and legacy disk reads.
    resume_data = Column(LargeBinary, nullable=True)
    resume_mime = Column(String(128), nullable=True)
    resume_size = Column(Integer, nullable=True)
    resume_text = Column(Text, nullable=True)
    extracted_skills = Column(Text, nullable=True) # JSON list
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    assessments = relationship("AssessmentSession", back_populates="candidate", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_candidates_email", "email"),)


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    applied_role = Column(String(50), nullable=False)
    status = Column(String(20), default="registered") # registered, in_progress, submitted, expired
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=60)
    
    total_score = Column(Float, default=0.0)
    max_score = Column(Float, default=80.0)
    percentage = Column(Float, default=0.0)
    
    role_fit_verdict = Column(String(50), nullable=True) # Strong Hire, Hire, Needs Training, Do Not Hire
    integrity_score = Column(Float, default=100.0) # 0-100 proctoring integrity
    summary_report = Column(Text, nullable=True) # JSON full report
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # ---- Adaptive assessment state (questions are served in batches of 5) ----
    current_section = Column(String(20), default="finance")   # finance -> iq -> resume -> complete
    current_tier = Column(String(20), default="Basic")        # Basic / Intermediate / Advanced (per-section ladder)
    current_batch_size = Column(Integer, default=0)           # size of the outstanding (last-served) batch
    finance_served = Column(Integer, default=0)               # count of finance questions served so far (max 48)
    iq_served = Column(Integer, default=0)                    # count of IQ questions served so far (max 16)
    resume_served = Column(Integer, default=0)                # count of resume questions served so far (max 16)
    pending_resume = Column(Text, nullable=True)              # JSON list of the 16 resume questions, generated at register

    candidate = relationship("Candidate", back_populates="assessments")
    questions = relationship("SessionQuestion", back_populates="session", cascade="all, delete-orphan")
    proctoring_events = relationship("ProctoringEvent", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_sessions_status", "status"),)


class SessionQuestion(Base):
    __tablename__ = "session_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_number = Column(Integer, nullable=False) # 1 to 80
    category = Column(String(100), nullable=False) # SAP B1 AP, GST, Cost Accounting, Excel, Resume Verification, etc.
    topic = Column(String(100), nullable=False)
    cognitive_level = Column(String(20), default="Intermediate") # Basic, Intermediate, Advanced
    is_resume_based = Column(Boolean, default=False)
    
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_option = Column(String(5), nullable=False) # A, B, C, D
    explanation = Column(Text, nullable=True)
    
    # Candidate Answer
    selected_option = Column(String(5), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    is_flagged = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer, default=0)
    answered_at = Column(DateTime, nullable=True)

    session = relationship("AssessmentSession", back_populates="questions")


class ProctoringEvent(Base):
    __tablename__ = "proctoring_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False) # tab_switch, window_blur, fullscreen_exit, copy_paste_attempt, idle
    details = Column(Text, nullable=True)
    timestamp_seconds = Column(Integer, default=0) # Seconds elapsed from test start
    client_time = Column(String(20), nullable=True) # candidate's local wall-clock time at the event
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("AssessmentSession", back_populates="proctoring_events")


class Manager(Base):
    """A person who can sign in to the Manager Intelligence Portal.

    Passwords are never stored: only a bcrypt hash. Accounts are deactivated rather than
    deleted so the audit trail keeps pointing at a real person.
    """
    __tablename__ = "managers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, unique=True, index=True)
    full_name = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="recruiter")  # admin | recruiter
    is_active = Column(Boolean, nullable=False, default=True)
    must_change_password = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class AuditLog(Base):
    """Record of privileged actions on candidate data (PII access and deletions).

    `manager_email` is denormalised on purpose: the entry must remain meaningful even if
    the manager account is later removed.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    manager_id = Column(String(36), ForeignKey("managers.id", ondelete="SET NULL"), nullable=True)
    manager_email = Column(String(255), nullable=True)
    action = Column(String(50), nullable=False)       # login, delete_candidate, download_resume, ...
    target_type = Column(String(50), nullable=True)   # candidate | session | manager
    target_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
