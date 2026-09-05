import datetime
import enum
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def gen_id() -> str:
    return uuid.uuid4().hex


class JobKind(str, enum.Enum):
    interview = "interview"       # Task 1: AI hiring assistant screening
    reachout = "reachout"         # Task 2: sourced-candidate reachout


class CallStatus(str, enum.Enum):
    queued = "queued"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    title: Mapped[str] = mapped_column(String)
    kind: Mapped[JobKind] = mapped_column(Enum(JobKind))
    description: Mapped[str] = mapped_column(Text, default="")
    questions: Mapped[list] = mapped_column(JSON, default=list)  # list[str]
    hunar_agent_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    candidates: Mapped[list["Candidate"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    name: Mapped[str] = mapped_column(String)
    phone_number: Mapped[str] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, default="manual")  # manual | pdl
    profile: Mapped[dict] = mapped_column(JSON, default=dict)  # raw PDL profile, if any
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    job: Mapped["Job"] = relationship(back_populates="candidates")
    calls: Mapped[list["Call"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_id)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"))
    hunar_call_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[CallStatus] = mapped_column(Enum(CallStatus), default=CallStatus.queued)
    recording_url: Mapped[str | None] = mapped_column(String, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_result: Mapped[dict] = mapped_column(JSON, default=dict)  # Hunar result schema output
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_score: Mapped[dict] = mapped_column(JSON, default=dict)  # optional LLM-derived scoring
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    candidate: Mapped["Candidate"] = relationship(back_populates="calls")
