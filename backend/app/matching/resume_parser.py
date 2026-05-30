import os
import pdfplumber
from dotenv import load_dotenv

load_dotenv("backend/.env")

def extract_resume_text(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

if __name__ == "__main__":
    path = "backend/resume.pdf"
    text = extract_resume_text(path)
    print(text)
