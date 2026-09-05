from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.hunar_client import HunarClient
from app.models import Call, CallStatus, Candidate, Job
from app.schemas import CandidateCreate, CandidateOut, CandidateUpdate, CallOut

router = APIRouter(tags=["candidates"])
settings = get_settings()


@router.post("/jobs/{job_id}/candidates", response_model=CandidateOut)
def add_candidate(job_id: str, payload: CandidateCreate, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    candidate = Candidate(
        job_id=job_id,
        name=payload.name,
        phone_number=payload.phone_number,
        email=payload.email,
        source="manual",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateOut])
def list_candidates(job_id: str, db: Session = Depends(get_db)):
    return db.query(Candidate).filter(Candidate.job_id == job_id).all()


@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.patch("/candidates/{candidate_id}", response_model=CandidateOut)
def update_candidate(candidate_id: str, payload: CandidateUpdate, db: Session = Depends(get_db)):
    """Used to swap a mock/sourced candidate's placeholder phone number for a real,
    consented one before triggering an outbound call."""
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if payload.phone_number is not None:
        candidate.phone_number = payload.phone_number
    if payload.email is not None:
        candidate.email = payload.email
    db.commit()
    db.refresh(candidate)
    return candidate


@router.post("/candidates/{candidate_id}/call", response_model=CallOut)
async def trigger_call(candidate_id: str, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    job = db.get(Job, candidate.job_id)
    if not job or not job.hunar_agent_id:
        raise HTTPException(status_code=400, detail="Job has no associated Hunar agent")

    call = Call(candidate_id=candidate.id, status=CallStatus.queued)
    db.add(call)
    db.commit()
    db.refresh(call)

    try:
        client = HunarClient()
        result = await client.create_call(
            agent_id=job.hunar_agent_id,
            callee_name=candidate.name,
            mobile_number=candidate.phone_number,
            custom_data={"job_title": job.title},
            callback_base_url=settings.public_base_url,
        )
        call.hunar_call_id = result.get("id")
        call.status = CallStatus.in_progress
        db.commit()
        db.refresh(call)
    except Exception as exc:  # noqa: BLE001
        call.status = CallStatus.failed
        db.commit()
        raise HTTPException(status_code=502, detail=f"Failed to initiate call: {exc}")

    return call


@router.get("/candidates/{candidate_id}/calls", response_model=list[CallOut])
def list_calls(candidate_id: str, db: Session = Depends(get_db)):
    return db.query(Call).filter(Call.candidate_id == candidate_id).all()
