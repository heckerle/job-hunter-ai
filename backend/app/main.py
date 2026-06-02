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
    matches = supabase.table("matches").select("*").order("match_score", desc=True).execute()
    return matches.data

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
