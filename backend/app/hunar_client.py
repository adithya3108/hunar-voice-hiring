import hashlib
import hmac

import httpx

from app.config import get_settings

settings = get_settings()


class HunarClient:
    """Client for the Hunar Voice Agents external API (base path /external/v1)."""

    def __init__(self) -> None:
        self.base_url = settings.hunar_api_base_url.rstrip("/") + "/external/v1"
        self.headers = {"X-API-Key": settings.hunar_api_key}

    async def create_agent(
        self,
        name: str,
        agent_prompt: str,
        objective: str,
        introduction: str,
        result_prompt: str,
        result_schema: dict,
        voice_persona: str = "NEHA",
        language: str = "ENGLISH",
    ) -> dict:
        payload = {
            "name": name,
            "language": language,
            "voice_persona": voice_persona,
            "agent_prompt": agent_prompt,
            "objective": objective,
            "introduction": introduction,
            "result_prompt": result_prompt,
            "result_schema": result_schema,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{self.base_url}/agents/", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def create_call(
        self,
        agent_id: str,
        callee_name: str,
        mobile_number: str,
        custom_data: dict[str, str],
        callback_base_url: str,
    ) -> dict:
        payload = {
            "agent_id": agent_id,
            "callee_name": callee_name,
            "mobile_number": mobile_number,
            "custom_data": custom_data,
            "from_phone_number": settings.hunar_from_phone_number or None,
            "callback_config": {
                "call_status_callback_url": f"{callback_base_url}/webhooks/hunar/status",
                "call_recording_callback_url": f"{callback_base_url}/webhooks/hunar/recording",
                "call_result_callback_url": f"{callback_base_url}/webhooks/hunar/result",
                "call_summary_callback_url": f"{callback_base_url}/webhooks/hunar/summary",
            },
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{self.base_url}/calls/", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def get_call(self, call_id: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{self.base_url}/calls/{call_id}/", headers=self.headers)
            resp.raise_for_status()
            return resp.json()


def verify_webhook_signature(raw_body: bytes, signature: str, timestamp: str) -> bool:
    """Verify X-Hunar-Signature (HMAC-SHA256 over timestamp + body) against the webhook secret."""
    if not settings.hunar_webhook_secret:
        return True  # allow local dev without a configured secret
    signed_payload = f"{timestamp}.".encode() + raw_body
    expected = hmac.new(
        settings.hunar_webhook_secret.encode(), signed_payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
