import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from supabase import create_client
from resume_parser import extract_resume_text

load_dotenv("backend/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> list:
    return model.encode(text).tolist()

def embed_all_jobs():
    print("Fetching jobs from Supabase...")
    jobs = supabase.table("jobs").select("id, description").eq("status", "active").execute().data
    print(f"Embedding {len(jobs)} jobs...")
    for i, job in enumerate(jobs):
        if not job.get("description"):
            continue
        embedding = embed_text(job["description"])
        supabase.table("jobs").update({"embedding": embedding}).eq("id", job["id"]).execute()
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(jobs)} done")
    print("All jobs embedded!")

if __name__ == "__main__":
    embed_all_jobs()
