import os
import sys
import json
import anthropic
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from dotenv import load_dotenv
from supabase import create_client

print ("Starting File")

load_dotenv("backend/.env")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def search_company(company: str) -> list:
    results = []
    with DDGS() as ddgs:
        hits = list(ddgs.text(f"{company} company software tech news", max_results=3))
        for hit in hits:
            results.append({
                "title": hit.get("title"),
                "snippet": hit.get("body"),
                "url": hit.get("href")
            })
    return results

def scrape_page(url: str) -> str:
    try:
        response = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs[:10]])
        return text[:1500]
    except:
        return ""

def generate_briefing(company: str, job_title: str, search_results: list) -> str:
    context = ""
    for r in search_results:
        context += f"Title: {r['title']}\nSnippet: {r['snippet']}\n\n"

    prompt = f"""You are a job application research assistant. Based on the search results below, write a concise company briefing for a job applicant.

Company: {company}
Role being applied for: {job_title}

Search results:
{context}

Write a briefing with these sections (keep each to 2-3 sentences max):
1. What they do
2. Recent news
3. Why this role likely exists
4. Two suggested talking points for the application

Be concise and practical. Total response should be under 200 words."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()

def research_company(company: str, job_title: str) -> str:
    existing = supabase.table("company_research").select("briefing").eq("company", company).execute().data
    if existing:
        print(f"  Using cached research for {company}")
        return existing[0]["briefing"]

    print(f"  Searching for {company}...")
    search_results = search_company(company)

    print(f"  Generating briefing...")
    briefing = generate_briefing(company, job_title, search_results)

    supabase.table("company_research").insert({
        "company": company,
        "briefing": briefing
    }).execute()

    return briefing

if __name__ == "__main__":
    sys.path.append("backend/app/matching")
    from sentence_transformers import SentenceTransformer
    from resume_parser import extract_resume_text
    from scorer import score_job
    import numpy as np

    model = SentenceTransformer("all-MiniLM-L6-v2")
    resume_text = extract_resume_text("backend/resume.pdf")
    resume_embedding = model.encode(resume_text).tolist()

    jobs = supabase.table("jobs").select("id, title, company, location, url, description, embedding").execute().data

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
    top_jobs = scored[:5]

    print("Running research agent on top 5 matches...\n")

    for i, (sim_score, job) in enumerate(top_jobs):
        company = job["company"]
        title = job["title"]
        print(f"\n{'='*60}")
        print(f"#{i+1} {title} at {company}")
        print(f"{'='*60}")
        briefing = research_company(company, title)
        print(briefing)
