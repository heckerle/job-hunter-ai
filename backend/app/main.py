from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv("backend/.env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://job-hunter-ai-nine.vercel.app",
        "https://job-hunter-ai-umber.vercel.app"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

@app.get("/")
def root():
    return {"status": "Job Hunter AI API is running"}

@app.get("/jobs")
def get_jobs():
    jobs = supabase.table("jobs").select(
        "id, title, company, location, salary_min, salary_max, url, status, fetched_at"
    ).order("fetched_at", desc=True).limit(50).execute()
    return jobs.data

@app.get("/jobs/matches")
def get_matches():
    import sys
    import numpy as np
    from sentence_transformers import SentenceTransformer

    sys.path.append("backend/app/matching")
    from resume_parser import extract_resume_text
    from scorer import score_job

    model = SentenceTransformer("all-MiniLM-L6-v2")
    resume_text = extract_resume_text("backend/resume.pdf")
    resume_embedding = model.encode(resume_text).tolist()

    jobs = supabase.table("jobs").select(
        "id, title, company, location, salary_min, salary_max, url, description, embedding"
    ).execute().data

    def cosine_similarity(a, b):
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    scored = []
    for job in jobs:
        if not job.get("embedding"):
            continue
        embedding = [float(x) for x in job["embedding"].strip("[]").split(",")]
        score = cosine_similarity(resume_embedding, embedding)
        scored.append((score, job))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_jobs = scored[:10]

    results = []
    for sim_score, job in top_jobs:
        analysis = score_job(resume_text, job)
        results.append({
            "id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "salary_min": job["salary_min"],
            "salary_max": job["salary_max"],
            "url": job["url"],
            "sim_score": round(sim_score * 100, 1),
            "match_score": analysis["match_score"],
            "recommendation": analysis["recommendation"],
            "match_reasons": analysis["match_reasons"],
            "gaps": analysis["gaps"]
        })

    return results

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = supabase.table("jobs").select("*").eq("id", job_id).execute().data
    if not job:
        return {"error": "Job not found"}
    job = job[0]

    research = supabase.table("company_research").select("briefing, researched_at").eq("company", job["company"]).execute().data

    return {
        **job,
        "briefing": research[0]["briefing"] if research else None
    }

@app.post("/research/{company}")
def research_company_endpoint(company: str, job_title: str = "Software Engineer"):
    import sys
    sys.path.append("backend/app/agents")
    from research_agent import research_company
    briefing = research_company(company, job_title)
    return {"briefing": briefing}
