# Hunar AI Hiring Assistant

Monorepo for the Hunar.AI assignment: an AI-driven hiring assistant using voice
agents (Task 1), a people-search + voice reachout pipeline (Task 2), and a
written design for attendance tracking without smartphones (Task 3).

## Structure

- `backend/` — FastAPI (Python) service: Hunar.AI voice agent orchestration,
  webhook handling, People Data Labs search, Postgres/SQLite storage, and
  Claude-based JD parsing/transcript scoring.
- `frontend/` — Next.js (TypeScript) + shadcn/ui recruiter dashboard.
- `docs/task3-attendance.md` — Task 3 write-up.

## Task 1 — AI Hiring Assistant

1. Recruiter creates a job with screening questions (`POST /jobs/`) — this
   provisions a Hunar.AI voice agent with a matching prompt + result schema.
2. Recruiter adds candidates and triggers outbound calls
   (`POST /candidates/{id}/call`).
3. Hunar.AI calls the candidate, conducts the screening, and posts results
   back via webhooks (`/webhooks/hunar/*`).
4. Backend runs an additional Claude-based qualitative scoring pass on the
   transcript and stores it alongside Hunar's structured extraction.
5. Dashboard shows call status, transcript, recording, and scores per
   candidate.

## Task 2 — People Search & Reachout

1. Recruiter pastes a JD (`POST /search/jobs`).
2. Backend uses Claude to extract role/skills/seniority and build a People
   Data Labs search query, creates a matching Hunar.AI reachout agent, and
   stores the resulting candidate list.
3. Recruiter selects candidates and triggers bulk reachout calls
   (`POST /search/jobs/{id}/reachout`).
4. Same webhook/dashboard pipeline as Task 1 surfaces responses.

## Task 3

See [`docs/task3-attendance.md`](docs/task3-attendance.md).

## Running locally

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # or source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env  # fill in real keys — never commit this file
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local  # set NEXT_PUBLIC_API_BASE_URL
npm run dev
```

## Security notes

- The Hunar.AI API key is **only** read from backend environment variables
  (`HUNAR_API_KEY`) and is never sent to or bundled into the frontend.
- Webhook requests from Hunar.AI are verified via HMAC-SHA256
  (`X-Hunar-Signature` / `X-Hunar-Timestamp`) before being trusted.
- `.env`, `.env.local`, and all secret files are gitignored.

## Deployment

- Frontend → Vercel (`frontend/`, set `NEXT_PUBLIC_API_BASE_URL` to the
  Railway backend URL).
- Backend → Railway (`backend/`, set all vars from `.env.example`, plus
  `DATABASE_URL` pointing at a Railway Postgres instance and
  `PUBLIC_BASE_URL` set to the Railway-assigned backend URL so Hunar.AI
  webhooks resolve correctly).
