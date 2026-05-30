import os
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from supabase import create_client

sys.path.append("backend/app/matching")
from resume_parser import extract_resume_text

load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
model = SentenceTransformer("all-MiniLM-L6-v2")

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def match_resume_to_jobs(resume_path: str, top_n: int = 10):
    print("Parsing resume...")
    resume_text = extract_resume_text(resume_path)
    resume_embedding = model.encode(resume_text).tolist()

    print("Fetching jobs...")
    jobs = supabase.table("jobs").select("id, title, company, location, salary_min, salary_max, url, embedding").execute().data

    print("Scoring matches...")
    scored = []
    for job in jobs:
        if not job.get("embedding"):
            continue
        embedding = [float(x) for x in job["embedding"].strip("[]").split(",")]
        score = cosine_similarity(resume_embedding, embedding)
        scored.append((score, job))

    scored.sort(key=lambda x: x[0], reverse=True)

    print(f"\n{'='*60}")
    print(f"TOP {top_n} MATCHES FOR YOUR RESUME")
    print(f"{'='*60}\n")

    for i, (score, job) in enumerate(scored[:top_n]):
        salary = ""
        if job.get("salary_min") and job.get("salary_max"):
            salary = f" | ${job['salary_min']:,} - ${job['salary_max']:,}"
        print(f"#{i+1} — {score*100:.1f}% match")
        print(f"     {job['title']} at {job['company']}")
        print(f"     {job['location']}{salary}")
        print(f"     {job['url']}")
        print()

if __name__ == "__main__":
    match_resume_to_jobs("backend/resume.pdf", top_n=10)
