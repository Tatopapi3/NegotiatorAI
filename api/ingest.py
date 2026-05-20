import io
from typing import Optional
import pdfplumber
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from core.embeddings import embed
from core.database import insert_job_description, insert_candidate_profile

router = APIRouter(prefix="/ingest", tags=["ingest"])


# ── Job Description ────────────────────────────────────────────────────────────

class JDInput(BaseModel):
    title: str
    company: str
    location: str = "New York, NY"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    content: str


@router.post("/jd", summary="Ingest a job description (text)")
async def ingest_jd(body: JDInput):
    embedding = embed(f"{body.title} {body.company} {body.location} {body.content}")
    record = insert_job_description(
        title=body.title,
        company=body.company,
        location=body.location,
        salary_min=body.salary_min,
        salary_max=body.salary_max,
        content=body.content,
        embedding=embedding,
    )
    return {"id": record["id"], "message": "Job description ingested."}


@router.post("/jd/pdf", summary="Ingest a job description from PDF")
async def ingest_jd_pdf(
    file: UploadFile = File(...),
    title: str = Form(...),
    company: str = Form(...),
    location: str = Form("New York, NY"),
    salary_min: Optional[int] = Form(None),
    salary_max: Optional[int] = Form(None),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    raw = await file.read()
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        content = "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
    if not content:
        raise HTTPException(400, "Could not extract text from PDF.")
    embedding = embed(f"{title} {company} {location} {content}")
    record = insert_job_description(
        title=title, company=company, location=location,
        salary_min=salary_min, salary_max=salary_max,
        content=content, embedding=embedding,
    )
    return {"id": record["id"], "message": "PDF job description ingested."}


# ── Candidate Profile ──────────────────────────────────────────────────────────

class ProfileInput(BaseModel):
    name: Optional[str] = None
    title: str
    years_exp: int
    skills: list[str] = []
    content: str   # resume text or structured bio


@router.post("/profile", summary="Ingest a candidate profile")
async def ingest_profile(body: ProfileInput):
    skills_str = ", ".join(body.skills)
    embedding = embed(f"{body.title} {body.years_exp} years {skills_str} {body.content}")
    record = insert_candidate_profile(
        name=body.name,
        title=body.title,
        years_exp=body.years_exp,
        skills=body.skills,
        content=body.content,
        embedding=embedding,
    )
    return {"id": record["id"], "message": "Candidate profile ingested."}


@router.post("/profile/pdf", summary="Ingest a candidate profile from PDF resume")
async def ingest_profile_pdf(
    file: UploadFile = File(...),
    title: str = Form(...),
    years_exp: int = Form(...),
    skills: str = Form(""),  # comma-separated
    name: Optional[str] = Form(None),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    raw = await file.read()
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        content = "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
    if not content:
        raise HTTPException(400, "Could not extract text from PDF.")
    skills_list = [s.strip() for s in skills.split(",") if s.strip()]
    embedding = embed(f"{title} {years_exp} years {skills} {content}")
    record = insert_candidate_profile(
        name=name, title=title, years_exp=years_exp,
        skills=skills_list, content=content, embedding=embedding,
    )
    return {"id": record["id"], "message": "PDF resume ingested."}
