import os
import sys
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from supabase import create_client
import time

sys.path.append("backend/app/matching")
from resume_parser import extract_resume_text
from scorer import score_job

load_dotenv("backend/.env")

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
model = SentenceTransformer("all-MiniLM-L6-v2")

EXCLUDE_KEYWORDS = [
    "clearance", "secret", "top secret", "ts/sci", "security clearance",
    "senior", "sr.", "sr ", "principal", "staff ", "manager", "director",
    "lead ", "architect", "head of"
]


MIDWEST_STATE_ABBRS = {
    "IL", "WI", "MN", "IA", "MO", "IN", "OH", "MI", "ND", "SD", "NE", "KS"
}


MIDWEST_STATES = {
    "Illinois", "Wisconsin", "Minnesota", "Iowa", "Missouri",
    "Indiana", "Ohio", "Michigan", "North Dakota", "South Dakota",
    "Nebraska", "Kansas"
}

def is_midwest(job):
    state = job.get("state") or ""
    return state in MIDWEST_STATES

def is_remote(job):
    location = (job.get("location") or "").lower()
    title = (job.get("title") or "").lower()
    description = (job.get("description") or "").lower()
    return "remote" in location or "remote" in title or "remote" in description[:500]

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def meets_salary(job):
    salary_min = job.get("salary_min")
    if salary_min is None:
        return True
    return salary_min >= 75000

def compute_and_store_matches():
    print("Parsing resume...")
    resume_text = extract_resume_text("backend/resume.pdf")
    resume_embedding = model.encode(resume_text).tolist()

    print("Fetching jobs...")
    jobs = supabase.table("jobs").select(
        "id, title, company, location, state, salary_min, salary_max, url, description, embedding"
    ).eq("status", "active").execute().data

    print("Computing similarity scores...")
    scored = []
    for job in jobs:
        if not job.get("embedding"):
            continue
        embedding = [float(x) for x in job["embedding"].strip("[]").split(",")]
        score = cosine_similarity(resume_embedding, embedding)
        scored.append((score, job))

    scored.sort(key=lambda x: x[0], reverse=True)

    seen = set()
    midwest_jobs = []
    other_jobs = []

    for score, job in scored:
        title_lower = job['title'].lower()
        if any(kw in title_lower for kw in EXCLUDE_KEYWORDS):
            continue
        if not meets_salary(job):
            continue
        key = f"{job['company']}_{job['title']}"
        if key in seen:
            continue
        seen.add(key)
        if is_midwest(job):
            midwest_jobs.append((score, job))
        else:
            other_jobs.append((score, job))

    top_midwest = midwest_jobs[:20]
    top_other = other_jobs[:10]
    top_jobs = top_midwest + top_other

    print(f"Found {len(top_midwest)} Midwest matches and {len(top_other)} other matches")
    print("Running Claude analysis...")

    supabase.table("matches").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    results = []
    for i, (sim_score, job) in enumerate(top_jobs):
        region = "midwest" if (sim_score, job) in top_midwest else "other"
        print(f"Scoring {i+1}/{len(top_jobs)}: {job['title']} at {job['company']} ({region})...")
        analysis = score_job(resume_text, job)
        
        if analysis["match_score"] < 50:
            print(f"  → {analysis['match_score']}% {analysis['recommendation']} (skipped)")
            continue

        record = {
            "job_id": job["id"],
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
            "gaps": analysis["gaps"],
            "region": region,
            "state": job.get("state"),
            "is_remote": is_remote(job),
        }
        supabase.table("matches").insert(record).execute()
        results.append(record)
        print(f"  → {analysis['match_score']}% {analysis['recommendation']}")

    print(f"\nDone! Stored {len(results)} matches in Supabase.")

if __name__ == "__main__":
    compute_and_store_matches()
