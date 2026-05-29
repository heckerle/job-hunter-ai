import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("backend/.env")

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_jobs(query="software engineer", location="us", pages=5):
    jobs = []
    for page in range(1, pages + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/{location}/search/{page}"
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
        print(f"Fetched page {page} — {len(data.get('results', []))} jobs")
    return jobs

def save_jobs(jobs):
    saved = 0
    skipped = 0
    for job in jobs:
        record = {
            "title": job.get("title"),
            "company": job.get("company", {}).get("display_name"),
            "location": job.get("location", {}).get("display_name"),
            "url": job.get("redirect_url"),
            "description": job.get("description"),
            "source": "adzuna",
            "salary_min": int(job.get("salary_min")) if job.get("salary_min") else None,
            "salary_max": int(job.get("salary_max")) if job.get("salary_max") else None,
        }
        try:
            supabase.table("jobs").insert(record).execute()
            saved += 1
        except Exception as e:
            print(f"Error: {e}")
            skipped += 1
    print(f"Done — {saved} saved, {skipped} skipped (duplicates)")

if __name__ == "__main__":
    print("Fetching jobs from Adzuna...")
    jobs = fetch_jobs(query="software engineer", location="us", pages=5)
    print(f"Total fetched: {len(jobs)}")
    save_jobs(jobs)
