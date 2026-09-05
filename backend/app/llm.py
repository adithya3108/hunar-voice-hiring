import json

import httpx

from app.config import get_settings

settings = get_settings()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _chat(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
    }
    resp = httpx.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def parse_job_description(jd_text: str) -> dict:
    """Extract role, seniority, skills, and a PDL Elasticsearch query from a raw JD."""
    prompt = f"""Given this job description, extract:
- "title": role title
- "skills": list of 3-8 key skills/keywords
- "seniority": one of "entry", "mid", "senior", "lead"
- "pdl_query": a People Data Labs Elasticsearch-style query object (bool/must on job_title_role,
  skills, job_title_levels) suitable for POST /v5/person/search

Return ONLY valid JSON with keys: title, skills, seniority, pdl_query. No markdown, no commentary.

Job description:
{jd_text}
"""
    return _extract_json(_chat(prompt))


def score_call_result(questions: list[str], structured_result: dict) -> dict:
    """Produce a qualitative rubric score + summary from Hunar's structured call result.

    Hunar's API returns extracted answers (per the agent's result_schema) rather than a
    raw transcript, so this reasons over that structured data instead of free text.
    """
    prompt = f"""A candidate was screened by phone against these questions:
{json.dumps(questions, indent=2)}

The voice agent extracted these structured answers from the call:
{json.dumps(structured_result, indent=2)}

Return ONLY valid JSON with keys (no markdown, no commentary):
- "summary": 2-3 sentence overall summary of the candidate
- "communication_score": 1-5
- "relevance_score": 1-5
- "confidence_score": 1-5
- "per_question": list of {{"question": str, "answer_summary": str}}
"""
    return _extract_json(_chat(prompt))
