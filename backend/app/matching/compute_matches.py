import os
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from supabase import create_client

sys.path.append("backend/app/matching")
from resume_parser import extract_resume_text
from scorer import score_job

load_dotenv("backend/.env")

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
model = SentenceTransformer("all-MiniLM-L6-v2")

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def compute_and_store_matches():
    print("Parsing resume...")
    resume_text = extract_resume_text("backend/resume.pdf")
    resume_embedding = model.encode(resume_text).tolist()

    print("Fetching jobs...")
    jobs = supabase.table("jobs").select(
        "id, title, company, location, salary_min, salary_max, url, description, embedding"
    ).execute().data

    print("Computing similarity scores...")
    scored = []
    for job in jobs:
        if not job.get("embedding"):
            continue
        embedding = [float(x) for x in job["embedding"].strip("[]").split(",")]
        score = cosine_similarity(resume_embedding, embedding)
        scored.append((score, job))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_jobs = scored[:10]

    print("Running Claude analysis on top 10...")
    
    # Clear old matches first
    supabase.table("matches").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    results = []
    for i, (sim_score, job) in enumerate(top_jobs):
        print(f"Scoring {i+1}/10: {job['title']} at {job['company']}...")
        analysis = score_job(resume_text, job)
        
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
            "gaps": analysis["gaps"]
        }
        supabase.table("matches").insert(record).execute()
        results.append(record)
        print(f"  → {analysis['match_score']}% {analysis['recommendation']}")

    print(f"\nDone! Stored {len(results)} matches in Supabase.")

if __name__ == "__main__":
    compute_and_store_matches()
