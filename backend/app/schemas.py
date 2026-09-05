import datetime

from pydantic import BaseModel

from app.models import CallStatus, JobKind


class JobCreate(BaseModel):
    title: str
    kind: JobKind
    description: str = ""
    questions: list[str] = []


class JobOut(BaseModel):
    id: str
    title: str
    kind: JobKind
    description: str
    questions: list[str]
    hunar_agent_id: str | None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class CandidateCreate(BaseModel):
    name: str
    phone_number: str
    email: str | None = None


class CandidateUpdate(BaseModel):
    phone_number: str | None = None
    email: str | None = None


class CandidateOut(BaseModel):
    id: str
    job_id: str
    name: str
    phone_number: str
    email: str | None
    source: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class CallOut(BaseModel):
    id: str
    candidate_id: str
    hunar_call_id: str | None
    status: CallStatus
    recording_url: str | None
    transcript: str | None
    structured_result: dict
    ai_summary: str | None
    ai_score: dict
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    job_description: str
    limit: int = 10


class TriggerReachoutRequest(BaseModel):
    candidate_ids: list[str]
