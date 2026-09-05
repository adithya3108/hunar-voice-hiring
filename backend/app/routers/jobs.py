from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.hunar_client import HunarClient
from app.models import Job
from app.schemas import JobCreate, JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _build_result_schema(questions: list[str]) -> dict:
    questions = questions or ["General impression of the candidate"]
    return {
        "type": "object",
        "properties": {
            f"answer_{i}": {"type": "string", "description": f"Candidate's answer to: {q}"}
            for i, q in enumerate(questions)
        },
    }


def _build_agent_fields(job: JobCreate) -> dict:
    if job.kind.value == "interview":
        questions_block = "\n".join(f"- {q}" for q in job.questions)
        return {
            "objective": f"Screen a candidate over the phone for the {job.title} role.",
            "introduction": (
                f"Hi, this is an AI recruiting assistant calling about your application "
                f"for the {job.title} role. Do you have a few minutes to answer some "
                f"screening questions?"
            ),
            "agent_prompt": (
                f"You are an AI recruiter screening a candidate for the role of {job.title}. "
                f"Ask the following questions one at a time, listening fully to each answer "
                f"before moving on:\n{questions_block}\n"
                f"Be friendly and professional. End the call by thanking the candidate."
            ),
            "result_prompt": (
                "Extract a concise summary of the candidate's answer to each screening "
                "question, in the same order they were asked."
            ),
        }
    return {
        "objective": f"Gauge a sourced candidate's interest in the {job.title} role and collect basic screening info.",
        "introduction": (
            f"Hi, this is an AI recruiting assistant reaching out about an opportunity "
            f"for the {job.title} role that might be a good fit for your background."
        ),
        "agent_prompt": (
            f"You are an AI recruiter reaching out to a candidate about the role of {job.title}. "
            f"Job description: {job.description}\n"
            f"Briefly pitch the role, gauge interest, and ask about their current notice period "
            f"and salary expectations. Be concise and respectful of their time."
        ),
        "result_prompt": (
            "Extract whether the candidate is interested, their notice period, and their "
            "salary expectations, if mentioned."
        ),
    }


@router.post("/", response_model=JobOut)
async def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    job = Job(
        title=payload.title,
        kind=payload.kind,
        description=payload.description,
        questions=payload.questions,
    )
    try:
        client = HunarClient()
        agent_fields = _build_agent_fields(payload)
        agent = await client.create_agent(
            name=f"{payload.kind.value}: {payload.title}"[:64],
            result_schema=_build_result_schema(payload.questions),
            **agent_fields,
        )
        job.hunar_agent_id = agent.get("id")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Failed to create Hunar agent: {exc}")

    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).order_by(Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
