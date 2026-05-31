import os
import sys
import json
import anthropic
from dotenv import load_dotenv

sys.path.append("backend/app/matching")
from resume_parser import extract_resume_text

load_dotenv("backend/.env")

print("Script started")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def summarize_job(job: dict) -> str:
    desc = job.get("description", "")
    words = desc.split()[:200]
    return " ".join(words)

def summarize_resume(resume_text: str) -> str:
    return resume_text

def score_job(resume_text: str, job: dict) -> dict:
    resume_summary = summarize_resume(resume_text)
    job_summary = summarize_job(job)

    prompt = f"""You are a job fit analyzer. Given a resume summary and job description, return ONLY a JSON object with no extra text.

RESUME:
{resume_summary}

JOB: {job.get('title')} at {job.get('company')}
{job_summary}

Return this exact JSON format:
{{
  "match_score": <integer 0-100>,
  "match_reasons": [<up to 3 short strings of what aligns>],
  "gaps": [<up to 2 short strings of what's missing>],
  "recommendation": "<strong_match|good_match|weak_match|poor_match>"
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

if __name__ == "__main__":
    from supabase import create_client
    from sentence_transformers import SentenceTransformer
    import numpy as np

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    resume_text = extract_resume_text("backend/resume.pdf")
    resume_embedding = model.encode(resume_text).tolist()

    jobs = supabase.table("jobs").select("id, title, company, location, salary_min, salary_max, url, description, embedding").execute().data

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

    print(f"Sending top 10 matches to Claude for analysis...\n")

    results = []
    for i, (sim_score, job) in enumerate(top_jobs):
        print(f"Scoring #{i+1}: {job['title']} at {job['company']}...")
        analysis = score_job(resume_text, job)
        results.append((sim_score, job, analysis))

    print(f"\n{'='*60}")
    print("CLAUDE'S FIT ANALYSIS — TOP 10 MATCHES")
    print(f"{'='*60}\n")

    for i, (sim_score, job, analysis) in enumerate(results):
        print(f"#{i+1} — Claude score: {analysis['match_score']}% | {analysis['recommendation'].upper()}")
        print(f"     {job['title']} at {job['company']}")
        print(f"     {job.get('location')}")
        print(f"     Strengths: {', '.join(analysis.get('match_reasons', []))}")
        print(f"     Gaps: {', '.join(analysis.get('gaps', []))}")
        print(f"     {job['url']}")
        print()
