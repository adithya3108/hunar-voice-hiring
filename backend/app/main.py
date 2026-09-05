from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Base, engine
from app.routers import candidates, jobs, search, webhooks

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hunar AI Hiring Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(search.router)
app.include_router(webhooks.router)


@app.get("/health")
def health():
    return {"status": "ok"}
