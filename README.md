# Sales Campaign CRM — Fullstack (React + FastAPI + MailHog + Ollama)

## Run (Windows PowerShell)
```powershell
cd sales-crm-fullstack
copy .env.example .env
docker compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- MailHog: http://localhost:8025

### Dev (optional)
- React only: `cd frontend && npm i && npm run dev` (proxy -> backend:8000)

## Acceptance Criteria (✅)
- One command: `docker compose up`
- ≥20 leads: `data/leads.csv` included
- Emails visible: open MailHog UI
- CSV updated: `data/leads_enriched.csv`
- Report: `reports/campaign_summary.md`

## Notes
- Switch to HuggingFace or Groq by setting env in `.env` (see `.env.example`).
- All outbound mail goes to MailHog (safe for demos).
- Replace `data/leads.csv` with your own; keep headers.