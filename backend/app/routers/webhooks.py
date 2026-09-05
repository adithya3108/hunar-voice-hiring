import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.hunar_client import verify_webhook_signature
from app.llm import score_call_result
from app.models import Call, CallStatus

router = APIRouter(prefix="/webhooks/hunar", tags=["webhooks"])
logger = logging.getLogger("hunar_webhooks")

# Maps Hunar's CallStatus / CallLifecycleStatus values to our simplified CallStatus.
_HUNAR_STATUS_MAP = {
    "NOT_STARTED": CallStatus.queued,
    "SCHEDULED": CallStatus.queued,
    "INITIATED": CallStatus.in_progress,
    "RINGING": CallStatus.in_progress,
    "IN_PROGRESS": CallStatus.in_progress,
    "COMPLETED": CallStatus.completed,
    "NOT_CONNECTED": CallStatus.failed,
    "CANCELLED": CallStatus.failed,
    "FAILED": CallStatus.failed,
}


def _find_call(db: Session, payload: dict) -> Call | None:
    call_id = payload.get("id") or payload.get("call_id")
    if not call_id:
        return None
    return db.query(Call).filter(Call.hunar_call_id == call_id).first()


async def _verify(request: Request, x_hunar_signature: str | None, x_hunar_timestamp: str | None) -> bytes:
    raw_body = await request.body()
    if not verify_webhook_signature(raw_body, x_hunar_signature or "", x_hunar_timestamp or ""):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    return raw_body


def _run_scoring(db: Session, call: Call) -> None:
    """Best-effort qualitative scoring on top of Hunar's structured result."""
    job = call.candidate.job if call.candidate else None
    if not (job and job.questions and call.structured_result):
        return
    try:
        call.ai_score = score_call_result(job.questions, call.structured_result)
        call.ai_summary = call.ai_score.get("summary")
        db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("LLM scoring failed for call %s", call.id)


@router.post("/status")
async def call_status(
    request: Request,
    db: Session = Depends(get_db),
    x_hunar_signature: str | None = Header(default=None),
    x_hunar_timestamp: str | None = Header(default=None),
):
    await _verify(request, x_hunar_signature, x_hunar_timestamp)
    payload = await request.json()
    call = _find_call(db, payload)
    if not call:
        logger.warning("status webhook for unknown call: %s", payload)
        return {"ok": True}

    raw_status = payload.get("status") or payload.get("lifecycle_status") or ""
    call.status = _HUNAR_STATUS_MAP.get(raw_status.upper(), call.status)
    db.commit()
    return {"ok": True}


@router.post("/recording")
async def call_recording(
    request: Request,
    db: Session = Depends(get_db),
    x_hunar_signature: str | None = Header(default=None),
    x_hunar_timestamp: str | None = Header(default=None),
):
    await _verify(request, x_hunar_signature, x_hunar_timestamp)
    payload = await request.json()
    call = _find_call(db, payload)
    if not call:
        return {"ok": True}

    call.recording_url = payload.get("recording_url")
    db.commit()
    return {"ok": True}


@router.post("/result")
async def call_result(
    request: Request,
    db: Session = Depends(get_db),
    x_hunar_signature: str | None = Header(default=None),
    x_hunar_timestamp: str | None = Header(default=None),
):
    await _verify(request, x_hunar_signature, x_hunar_timestamp)
    payload = await request.json()
    call = _find_call(db, payload)
    if not call:
        return {"ok": True}

    call.structured_result = payload.get("result", {})
    db.commit()
    _run_scoring(db, call)
    return {"ok": True}


@router.post("/summary")
async def call_summary(
    request: Request,
    db: Session = Depends(get_db),
    x_hunar_signature: str | None = Header(default=None),
    x_hunar_timestamp: str | None = Header(default=None),
):
    await _verify(request, x_hunar_signature, x_hunar_timestamp)
    payload = await request.json()
    call = _find_call(db, payload)
    if not call:
        return {"ok": True}

    call.recording_url = payload.get("recording_url") or call.recording_url
    if payload.get("result"):
        call.structured_result = payload["result"]
    raw_status = payload.get("status") or payload.get("lifecycle_status") or ""
    if raw_status:
        call.status = _HUNAR_STATUS_MAP.get(raw_status.upper(), call.status)
    db.commit()
    _run_scoring(db, call)
    return {"ok": True}
