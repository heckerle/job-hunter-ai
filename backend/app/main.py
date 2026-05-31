from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv("backend/.env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
