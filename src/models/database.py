"""Database models for PrepAIr Interview Simulator."""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class QuestionType(str, Enum):
    OPEN = "open"
    CODE = "code"


class InterviewMode(str, Enum):
    DIRECT = "direct"
    AFTER_CV = "after_cv"


# User Model
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    sessions: List["InterviewSession"] = Relationship(back_populates="user")
    question_history: List["QuestionHistory"] = Relationship(back_populates="user")
    skill_state: Optional["UserSkillState"] = Relationship(back_populates="user")


# Question Bank
class QuestionBank(SQLModel, table=True):
    __tablename__ = "question_bank"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: str = Field(index=True, unique=True)
    question_type: QuestionType
    question_text: str
    topics: str = Field(default="[]")  # JSON array as string
    difficulty: Optional[str] = None  # Easy, Medium, Hard for code questions
    category: Optional[str] = None
    solution: Optional[str] = None
    solution_url: Optional[str] = None
    metadata: Optional[str] = None  # JSON string for additional data
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Job Specifications
class JobSpec(SQLModel, table=True):
    __tablename__ = "job_specs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    jd_hash: str = Field(index=True, unique=True)  # Hash of JD text
    jd_text: str
    role_profile: Optional[str] = None  # JSON string of RoleProfile
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    sessions: List["InterviewSession"] = Relationship(back_populates="job_spec")


# Interview Sessions
class InterviewSession(SQLModel, table=True):
    __tablename__ = "interview_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    job_spec_id: int = Field(foreign_key="job_specs.id")
    mode: InterviewMode
    cv_text: Optional[str] = None
    cv_version_id: Optional[str] = None
    plan: Optional[str] = None  # JSON string of interview plan
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    status: str = Field(default="active")  # active, completed, abandoned
    
    # Relationships
    user: User = Relationship(back_populates="sessions")
    job_spec: JobSpec = Relationship(back_populates="sessions")
    turns: List["InterviewTurn"] = Relationship(back_populates="session")


# Interview Turns (Q&A pairs)
class InterviewTurn(SQLModel, table=True):
    __tablename__ = "interview_turns"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="interview_sessions.id")
    question_id: Optional[int] = Field(foreign_key="question_bank.id")
    question_text: str
    user_transcript: str
    user_code: Optional[str] = None
    interviewer_message: Optional[str] = None
    followup_question: Optional[str] = None
    score_json: Optional[str] = None  # JSON string of score data
    turn_number: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    client_metrics: Optional[str] = None  # JSON string for client-side metrics
    
    # Relationships
    session: InterviewSession = Relationship(back_populates="turns")
    question: Optional[QuestionBank] = Relationship()


# Question History (track what questions were asked to which user for which JD)
class QuestionHistory(SQLModel, table=True):
    __tablename__ = "question_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    jd_hash: str = Field(index=True)
    question_id: int = Field(foreign_key="question_bank.id", index=True)
    session_id: int = Field(foreign_key="interview_sessions.id")
    asked_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User = Relationship(back_populates="question_history")


# User Skill State (for adaptive questioning)
class UserSkillState(SQLModel, table=True):
    __tablename__ = "user_skill_state"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, unique=True)
    skill_scores: Optional[str] = None  # JSON string mapping topics to scores
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="skill_state")
