# Job Hunter AI — Project Scope

> An AI-powered job hunting agent that finds, researches, tailors, and applies to jobs on your behalf — with human approval at every critical step.

---

## Project goals

- Build a fully functional AI agent pipeline that automates the most tedious parts of job hunting
- Create a portfolio piece that demonstrates AI/ML engineering skills across the full stack
- Design it as a real product with monetization potential ($20–30/month SaaS)
- Keep infrastructure costs under $60/month until revenue covers them

---

## Tech stack

| Layer | Technology | Cost |
|---|---|---|
| Frontend | Next.js + Tailwind CSS | Free |
| Backend | Python + FastAPI | Free |
| Database | Supabase (Postgres + pgvector) | Free tier |
| LLM | Claude API / GPT-4o | Pay per use (~$0.01–0.05/task) |
| Embeddings | OpenAI `text-embedding-3-small` | Pay per use (~$0.0001/job) |
| Browser automation | Playwright | Free |
| Background jobs | Redis + Celery | Free (self-hosted) |
| Frontend hosting | Vercel | Free tier |
| Backend hosting | Render or Railway | $5–7/month |
| Job data | Greenhouse API, Adzuna API, RSS feeds | Free |
| Scraping service (optional, later) | Apify or Bright Data | $20–50/month |

---

## Phase 1 — Data ingestion (weeks 1–2)

### Goal
Get real job postings flowing into a structured database.

### Tasks
- [ ] Set up Supabase project with Postgres + pgvector enabled
- [ ] Register for Adzuna API (free, ~1M listings)
- [ ] Build Greenhouse job board fetcher (public API, no auth required)
- [ ] Parse RSS feeds from RemoteOK, We Work Remotely
- [ ] Normalize all sources into a shared `jobs` schema
- [ ] Generate embeddings for each job posting using OpenAI
- [ ] Store embeddings in pgvector for semantic search
- [ ] Deduplicate postings (same role at same company from different sources)
- [ ] Build a basic scheduler to refresh data daily (Celery + Redis)

### Jobs table schema
```sql
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT,
  company TEXT,
  location TEXT,
  url TEXT UNIQUE,
  description TEXT,
  source TEXT,
  salary_min INT,
  salary_max INT,
  embedding VECTOR(1536),
  fetched_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT DEFAULT 'new'
);
```

### Possible complications
- **Adzuna rate limits**: free tier is 100 requests/day — enough for development, may need paid plan at scale
- **Greenhouse pagination**: each company has its own subdomain (`boards.greenhouse.io/{company}`) — requires a seed list of companies to monitor
- **Embedding costs**: 10,000 job postings × ~500 tokens = ~$0.25 one-time, then pennies per day for new postings
- **Redis setup**: requires a running Redis instance locally or a free cloud instance (Upstash has a free tier)

---

## Phase 2 — Resume matching engine (weeks 2–3)

### Goal
Compare your resume against job postings and surface the best matches with explanations.

### Tasks
- [ ] Build resume parser — upload PDF, extract structured data
- [ ] Generate resume embedding
- [ ] Implement cosine similarity search against jobs table
- [ ] Build fit scorer — LLM explains why each job is a good/bad match
- [ ] Score output: match percentage + 3-sentence explanation
- [ ] Filter by role, location, salary, remote preference
- [ ] Build basic UI to browse ranked results

### Fit score output format
```json
{
  "match_score": 87,
  "match_reasons": [
    "Strong Python and ML experience aligns with core requirements",
    "Previous work with LLMs directly relevant to role",
    "Missing: Kubernetes experience listed as preferred"
  ],
  "recommendation": "strong_match"
}
```

### Possible complications
- **Resume parsing accuracy**: PDF parsing is messy — use `pdfplumber` or `pymupdf`, expect to handle edge cases
- **Embedding model drift**: if you switch embedding models later, all stored embeddings become incompatible and need regeneration
- **LLM costs for scoring**: scoring 100 jobs × ~$0.02 = ~$2 per full scan — fine for personal use, needs caching for multi-user

---

## Phase 3 — Agent layer (weeks 3–5)

### 3a — Research agent

#### Goal
For top-matched jobs, automatically generate a company intelligence briefing.

#### Tasks
- [ ] Web search for recent company news (use Bing Search API or Serper — ~$5/month)
- [ ] Scrape company LinkedIn page overview (or use a data provider)
- [ ] Pull Glassdoor rating if available
- [ ] Identify tech stack from job description and company website
- [ ] LLM synthesizes everything into a 1-page briefing
- [ ] Store briefing in `company_research` table, refresh weekly

#### Briefing output covers
- What the company does (2 sentences)
- Recent news (funding, product launches, layoffs)
- Tech stack in use
- Culture signals from Glassdoor
- Why this role exists (inferred from JD)
- Suggested talking points for application

#### Possible complications
- **Glassdoor blocks scrapers aggressively** — use a scraping proxy or skip it initially
- **Search API costs**: Serper is $50/2,500 queries — budget ~$5–10/month
- **Stale research**: companies change fast — implement a `researched_at` timestamp and refresh threshold

---

### 3b — Tailoring agent

#### Goal
Generate a customized resume and cover letter for each approved job.

#### Tasks
- [ ] Build prompt template that takes: base resume + job description + company research → tailored resume bullets
- [ ] Generate cover letter tuned to role, company tone, and your experience
- [ ] Version control all generated documents (store each version with job ID)
- [ ] Allow manual editing before approval
- [ ] Output: PDF-ready resume + cover letter text

#### Possible complications
- **LLM hallucination**: model may invent experience you don't have — always review output before sending
- **Resume formatting**: generating a visually formatted PDF resume is harder than it sounds — use a fixed template (LaTeX or HTML-to-PDF via `weasyprint`) and only swap the content
- **Cover letter tone**: needs to sound like you — add a "writing style" section to your profile that the LLM uses as a style guide
- **Cost**: ~$0.05–0.10 per tailored application — negligible

---

### 3c — Application agent

#### Goal
Automatically fill out and submit job applications — with your explicit approval before anything is sent.

#### Tasks
- [ ] Use Playwright to navigate to application URL
- [ ] Detect form fields using accessibility tree (not CSS selectors — too brittle)
- [ ] Map fields to your profile data: name, email, LinkedIn, GitHub, resume upload, cover letter
- [ ] Handle common ATS platforms: Greenhouse, Lever, Workday, Ashby
- [ ] Pause before submission and show you exactly what will be sent — **human approval required**
- [ ] Log every application: URL, date, fields submitted, documents sent
- [ ] Handle file uploads (resume PDF)

#### Human approval step (critical)
Before submitting any application, the system must:
1. Show a preview of every field that will be filled
2. Show the tailored resume and cover letter
3. Require explicit "Approve & Submit" click from you
4. Never auto-submit without confirmation

#### Possible complications
- **CAPTCHA**: many ATS platforms use CAPTCHA — cannot be bypassed programmatically, requires manual intervention. Flag these for manual completion.
- **Workday is notoriously complex**: their forms are JS-heavy and change frequently — expect significant engineering time for Workday support
- **Multi-page forms**: some applications span 5–10 pages — agent needs to track state across pages
- **File upload handling**: Playwright can upload files but the input element must be visible — may need to trigger click events
- **Form field detection accuracy**: custom dropdown components and rich text editors don't behave like standard HTML inputs — handle edge cases carefully
- **Session expiry**: long forms may time out — implement keepalive pings
- **IP flagging**: submitting many applications from the same IP may trigger fraud detection — consider residential proxies for scale (adds cost)

---

## Phase 4 — Dashboard UI (weeks 5–7)

### Goal
A clean, professional interface that makes the whole system usable and demonstrable.

### Tasks
- [ ] Pipeline kanban view: Discovered → Matched → Approved → Applied → Responded
- [ ] Job detail view: posting + match score + company briefing + generated documents
- [ ] Application history with status tracking
- [ ] Resume and profile management
- [ ] Settings: job preferences, salary range, remote/hybrid/onsite filter, locations
- [ ] Notification when new strong matches are found
- [ ] Analytics: applications sent, response rate, match score distribution

### Possible complications
- **Real-time updates**: use Supabase realtime subscriptions to push new matches to the UI without polling
- **Mobile responsiveness**: Tailwind makes this manageable but budget extra time

---

## Phase 5 — Productization (ongoing)

### If you want to monetize this

- [ ] Add Stripe for subscriptions ($20–30/month tier)
- [ ] Multi-user auth (Supabase Auth — free)
- [ ] Per-user job preferences and resume storage
- [ ] Usage limits per tier (e.g. 50 applications/month on free, unlimited on paid)
- [ ] Landing page explaining the product
- [ ] Waitlist before public launch

### Cost at scale (100 paying users)

| Item | Monthly cost |
|---|---|
| Vercel Pro (if needed) | $20 |
| Supabase Pro | $25 |
| Render/Railway backend | $7–20 |
| LLM API calls (100 users × ~$5) | $500 |
| Scraping service | $50 |
| Search API | $10 |
| **Total** | **~$612/month** |
| **Revenue (100 × $20)** | **$2,000/month** |
| **Profit** | **~$1,388/month** |

---

## Real money summary

| Item | When | Estimated cost |
|---|---|---|
| LLM API calls | From day 1 (testing) | ~$5–15/month |
| Backend hosting | When you deploy publicly | $5–7/month |
| Search API (Serper/Bing) | Phase 3a | ~$5–10/month |
| Scraping service | Only if you need LinkedIn | $20–50/month |
| Supabase Pro | Only if you exceed free tier | $25/month |
| **Total while building** | | **~$5–15/month** |
| **Total when live** | | **~$35–85/month** |

---

## What this project demonstrates (for job applications)

| Skill | Where it shows up |
|---|---|
| LLM orchestration + agents | Research agent, tailoring agent, apply agent |
| Vector embeddings + semantic search | Matching engine |
| Data pipelines | Ingestion layer, scheduler |
| Browser automation | Application agent (Playwright) |
| Full-stack development | Next.js frontend + FastAPI backend |
| System design | Multi-service architecture with queue |
| Product thinking | Human-in-the-loop design, monetization model |
| API integration | Adzuna, Greenhouse, Serper, Stripe |

---

## Build order (recommended)

```
Week 1–2:   Phase 1 — get job data flowing into Supabase
Week 2–3:   Phase 2 — resume matching, basic UI to browse results
Week 3–4:   Phase 3a — research agent
Week 4–5:   Phase 3b — tailoring agent
Week 5–6:   Phase 3c — application agent (Greenhouse + Lever first, Workday later)
Week 6–7:   Phase 4 — polish the dashboard
Week 7+:    Phase 5 — productize if desired
```

---

## Immediate next steps

1. Create a GitHub repo: `job-hunter-ai`
2. Set up a Supabase project and enable pgvector
3. Register for Adzuna API (free at developer.adzuna.com)
4. Build the first ingestion script — get 100 real jobs into your database
5. Come back here and we'll move to Phase 2

---

*Built with Claude — architecture designed May 2026*
