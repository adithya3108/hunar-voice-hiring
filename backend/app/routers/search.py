from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.hunar_client import HunarClient
from app.llm import parse_job_description
from app.models import Call, CallStatus, Candidate, Job, JobKind
from app.pdl_client import search_people
from app.schemas import CallOut, SearchRequest, TriggerReachoutRequest

router = APIRouter(prefix="/search", tags=["search"])
settings = get_settings()


@router.post("/jobs")
async def create_job_from_jd(payload: SearchRequest, db: Session = Depends(get_db)):
    """Parse a JD, create a reachout Job + Hunar agent, run a PDL search, and store candidates."""
    try:
        parsed = parse_job_description(payload.job_description)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"JD parsing failed: {exc}")

    job = Job(
        title=parsed.get("title", "Untitled Role"),
        kind=JobKind.reachout,
        description=payload.job_description,
        questions=["Are you currently open to new opportunities?", "What are your salary expectations?"],
    )

    try:
        client = HunarClient()
        agent = await client.create_agent(
            name=f"reachout: {job.title}"[:64],
            objective=f"Gauge a sourced candidate's interest in the {job.title} role and collect basic screening info.",
            introduction=(
                f"Hi, this is an AI recruiting assistant reaching out about an opportunity "
                f"for the {job.title} role that might be a good fit for your background."
            ),
            agent_prompt=(
                f"You are an AI recruiter reaching out to a candidate about the role of {job.title}. "
                f"Job description: {job.description}\n"
                "Briefly pitch the role, gauge interest, and ask about their notice period and "
                "salary expectations. Be concise and respectful of their time."
            ),
            result_prompt=(
                "Extract whether the candidate is interested, their notice period, and their "
                "salary expectations, if mentioned."
            ),
            result_schema={
                "type": "object",
                "properties": {
                    "interested": {"type": "string"},
                    "notice_period": {"type": "string"},
                    "salary_expectation": {"type": "string"},
                },
            },
        )
        job.hunar_agent_id = agent.get("id")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Failed to create Hunar agent: {exc}")

    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        profiles = await search_people(
            parsed.get("pdl_query", {}),
            limit=payload.limit,
            title=parsed.get("title", ""),
            skills=parsed.get("skills", []),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"People search failed: {exc}")

    candidates = []
    for profile in profiles:
        phone = (profile.get("phone_numbers") or [None])[0]
        if not phone:
            continue
        candidate = Candidate(
            job_id=job.id,
            name=profile.get("full_name", "Unknown"),
            phone_number=phone,
            email=(profile.get("emails") or [None])[0],
            source="pdl",
            profile=profile,
        )
        db.add(candidate)
        candidates.append(candidate)

    db.commit()
    for c in candidates:
        db.refresh(c)

    return {
        "job_id": job.id,
        "parsed": parsed,
        "candidates_found": len(candidates),
    }


@router.post("/jobs/{job_id}/reachout", response_model=list[CallOut])
async def trigger_reachout(job_id: str, payload: TriggerReachoutRequest, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job or not job.hunar_agent_id:
        raise HTTPException(status_code=400, detail="Job has no associated Hunar agent")

    client = HunarClient()
    calls = []
    for candidate_id in payload.candidate_ids:
        candidate = db.get(Candidate, candidate_id)
        if not candidate:
            continue
        call = Call(candidate_id=candidate.id, status=CallStatus.queued)
        db.add(call)
        db.commit()
        db.refresh(call)

        try:
            result = await client.create_call(
                agent_id=job.hunar_agent_id,
                callee_name=candidate.name,
                mobile_number=candidate.phone_number,
                custom_data={"job_title": job.title},
                callback_base_url=settings.public_base_url,
            )
            call.hunar_call_id = result.get("id")
            call.status = CallStatus.in_progress
        except Exception:  # noqa: BLE001
            call.status = CallStatus.failed
        db.commit()
        db.refresh(call)
        calls.append(call)

    return calls
