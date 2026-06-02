import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("backend/.env")

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SEARCH_QUERIES = [
    "entry level software developer",
    "junior software engineer",
    "junior frontend developer",
    "junior full stack developer",
    "new grad software engineer",
]

def fetch_jobs_from_adzuna(query, pages=5):
    jobs = []
    for page in range(1, pages + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/us/search/{page}"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_API_KEY,
            "what": query,
            "results_per_page": 20,
            "content-type": "application/json"
        }
        response = requests.get(url, params=params)
        data = response.json()
        jobs.extend(data.get("results", []))
    return jobs

def sync():
    print("Starting job sync...")
    now = datetime.now(timezone.utc).isoformat()

    # Get all existing URLs from DB
    existing = supabase.table("jobs").select("id, url").execute().data
    existing_urls = {job["url"]: job["id"] for job in existing}
    print(f"Existing jobs in DB: {len(existing_urls)}")

    # Fetch fresh jobs from all queries
    all_fetched_urls = set()
    new_jobs = []

    for query in SEARCH_QUERIES:
        print(f"Fetching: '{query}'...")
        jobs = fetch_jobs_from_adzuna(query, pages=5)
        for job in jobs:
            url = job.get("redirect_url")
            if not url:
                continue
            all_fetched_urls.add(url)
            if url not in existing_urls:
                new_jobs.append({
                    "title": job.get("title"),
                    "company": job.get("company", {}).get("display_name"),
                    "location": job.get("location", {}).get("display_name"),
                    "url": url,
                    "description": job.get("description"),
                    "source": "adzuna",
                    "salary_min": int(job.get("salary_min")) if job.get("salary_min") else None,
                    "salary_max": int(job.get("salary_max")) if job.get("salary_max") else None,
                    "status": "active",
                    "last_seen_at": now
                })

    # Insert new jobs
    added = 0
    for job in new_jobs:
        try:
            supabase.table("jobs").insert(job).execute()
            added += 1
        except Exception as e:
            pass

    # Mark unseen jobs as expired
    expired = 0
    for url, job_id in existing_urls.items():
        if url not in all_fetched_urls:
            supabase.table("jobs").update({
                "status": "expired"
            }).eq("id", job_id).execute()
            expired += 1

    # Update last_seen_at for active jobs
    for url in all_fetched_urls:
        if url in existing_urls:
            supabase.table("jobs").update({
                "status": "active",
                "last_seen_at": now
            }).eq("url", url).execute()

    print(f"\nSync complete!")
    print(f"  New jobs added: {added}")
    print(f"  Jobs marked expired: {expired}")
    print(f"  Total active jobs: {len(all_fetched_urls)}")

if __name__ == "__main__":
    sync()
