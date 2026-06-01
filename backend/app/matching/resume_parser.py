import os
import tempfile
import requests
import pdfplumber
from dotenv import load_dotenv

load_dotenv("backend/.env")

def extract_resume_text(pdf_path: str = None) -> str:
    resume_url = os.getenv("RESUME_URL")
    
    if resume_url:
        response = requests.get(resume_url)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        with pdfplumber.open(tmp_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        os.unlink(tmp_path)
        return text.strip()
    
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

if __name__ == "__main__":
    text = extract_resume_text("backend/resume.pdf")
    print(text)
