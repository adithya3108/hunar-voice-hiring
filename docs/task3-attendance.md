# Task 3 — Attendance for 1000 people across 100 locations, no smartphones, LLMs exist

## Constraint recap
No smartphones, no apps. LLMs, telephony, and "everything else" (regular phones,
landlines, basic feature phones, internet backends) still exist.

## Core idea: voice is the interface, not a screen

Without an app, the only device guaranteed to be at every one of the 100 locations
is **a phone** (feature phone, landline, or one shared site phone). So attendance
becomes a **voice-first, LLM-driven roll call**, not a tap-to-check-in flow.

## Design

1. **One phone number per location** (or one shared organizational line with an
   IVR that first asks "which location code are you at?").
2. **Twice-daily automated voice agent calls** to each location's phone at
   fixed windows (e.g. 9:10am check-in, 6:10pm check-out) — the same
   call-orchestration pattern as Task 1/2 (outbound call, LLM-driven
   conversation, structured result extraction).
3. At each site, whoever picks up (a site supervisor or a designated point
   person) puts the call on speaker. The voice agent asks each worker in turn
   to state their name and employee ID out loud ("Please say your name and ID
   to check in").
4. The LLM-backed agent does real-time speech-to-text, matches each spoken
   name/ID against that location's roster (fuzzy-matching handles
   mispronunciation/accents), and confirms back verbally ("Got it, Ramesh,
   ID 4021, checked in").
5. If a call isn't answered, or fewer than the expected headcount check in
   within the call window, the system automatically retries the call, then
   escalates via SMS/voice alert to the site supervisor and flags it in the
   dashboard.
6. All results land in the same central dashboard used for Tasks 1/2:
   per-location attendance %, no-shows, late check-ins, roster mismatches,
   trends over time.

## Why this works within the constraint

- Every location already has *a* phone — no new hardware to distribute or
  train 1000 people on.
- The LLM replaces the "app UI" entirely: instead of tapping a button, a
  worker just says their name — zero literacy or device-skill requirement,
  which also makes this more inclusive than an app would have been anyway.
- Reuses the exact voice-agent infrastructure already built for Tasks 1 and 2
  (outbound call, structured extraction, webhook-driven dashboard update) —
  no separate system needed.

## Fallback / edge cases

- **Poor signal locations:** fall back to SMS-based check-in (worker/site
  supervisor texts a code), parsed by the same backend.
  Voice agent skipped for these locations if a `no_answer` status recurs.
- **Roster changes:** synced centrally so the agent's matching logic always
  has the current site roster before each call window.
- **Fraud/proxy check-ins:** mitigated by requiring ID + name (not just a
  headcount), spot-check callbacks to individual workers' personal phones
  (if available) on a random sample basis, and flagging locations whose
  supervisor always reports 100% attendance for manual audit.

## What I'd explicitly avoid

- Building a companion "app-like" web page for workers to visit — that
  reintroduces the smartphone/browser dependency the constraint rules out.
- IVR-only (no LLM) — traditional DTMF ("press 1 for present") doesn't scale
  to calling out 1000 individual names per day; the LLM is what makes
  free-form spoken roll call parseable at this scale.
