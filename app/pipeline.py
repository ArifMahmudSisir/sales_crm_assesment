import os, smtplib, pandas as pd
from typing import Dict, Tuple
from email.mime.text import MIMEText
from jinja2 import Template
import llm_client

LEADS_PATH = os.getenv("LEADS_PATH", "data/leads.csv")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "data/leads_enriched.csv")
REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
MAILHOG_HOST = os.getenv("SMTP_HOST", "mailhog")
MAILHOG_PORT = int(os.getenv("SMTP_PORT", "1025"))
FROM_EMAIL = os.getenv("FROM_EMAIL", "sales@example.com")

EMAIL_TMPL = Template("""
Hi {{ first_name }}{% if company %} at {{ company }}{% endif %},

{{ intro_line }}

Based on what {{ company or 'you' }} seem to focus on, I think {{ offer_line }}.

If you're open to it, I can share a 5-minute walkthrough tailored for {{ company or first_name }}.

Best,
{{ sender_name }}
""")

def simple_score(lead: Dict[str, str]) -> int:
    score = 50
    title = (lead.get("title","") or "").lower()
    company = (lead.get("company","") or "").lower()
    domain = (lead.get("email","").split("@")[-1] if lead.get("email") else "").lower()
    if any(k in title for k in ["head","vp","director","chief","owner","founder"]): score += 25
    if any(k in title for k in ["intern","assistant","trainee"]): score -= 15
    if company and len(company)>8: score += 5
    if domain.endswith((".edu",".gov",".org")): score -= 10
    return max(1, min(score, 100))

def llm_enrich(lead: Dict[str, str]) -> Tuple[int, str, str]:
    prompt = f"""
You are a B2B SDR assistant. Given this lead:
Name: {lead.get('name','')}
Title: {lead.get('title','')}
Company: {lead.get('company','')}
Email: {lead.get('email','')}
Notes: {lead.get('notes','')}

1) Give a lead score from 1-100.
2) Suggest a short buyer persona (3-6 words).
3) Write ONE warm intro sentence (<= 30 words) customized to the lead.
Return JSON with keys: score, persona, intro.
"""
    resp = llm_client.generate(prompt)
    score = None; persona=None; intro=None
    if resp and resp.strip().startswith("{") and "}" in resp:
        import json
        try:
            data = json.loads(resp.strip().splitlines()[0])
            score = int(data.get("score", 0))
            persona = (data.get("persona") or "").strip()
            intro = (data.get("intro") or "").strip()
        except Exception:
            pass
    if score is None: score = simple_score(lead)
    if not persona: persona = "Pragmatic decision-maker"
    if not intro: intro = f"I thought I'd share something concise that could help {lead.get('company','you')} move faster this quarter."
    return score, persona, intro

def draft_email(lead: Dict[str, str], intro_line: str) -> str:
    first_name = (lead.get("name","").split()[0] if lead.get("name") else "there")
    offer_line = "we could cut your outreach time by ~40% using our lightweight AI-assisted CRM"
    return EMAIL_TMPL.render(first_name=first_name, company=lead.get("company",""),
                             intro_line=intro_line, offer_line=offer_line,
                             sender_name=os.getenv("SENDER_NAME","Ariana from Aster")).strip()

def classify_response(text: str) -> str:
    t = text.lower()
    if "not interested" in t or "unsubscribe" in t: return "Uninterested"
    if "call" in t or "meeting" in t: return "Positive"
    if "later" in t or "next quarter" in t: return "Nurture"
    return "No Reply Yet"

def send_email(to_email: str, subject: str, body: str):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject; msg["From"] = FROM_EMAIL; msg["To"] = to_email
    with smtplib.SMTP(MAILHOG_HOST, MAILHOG_PORT) as smtp:
        smtp.send_message(msg)

def process_leads():
    df = pd.read_csv(LEADS_PATH)
    for col in ["status","score","persona","priority","email_draft","response_class"]:
        if col not in df.columns: df[col] = "" if col!="score" else 0

    for idx, row in df.iterrows():
        lead = row.to_dict()
        score, persona, intro = llm_enrich(lead)
        body = draft_email(lead, intro)
        priority = "High" if score>=75 else ("Medium" if score>=50 else "Low")
        subject = f"{lead.get('company','')} x Quick idea for Q{os.getenv('CURRENT_QUARTER','3')}"
        status = "SKIPPED: Missing email"
        if lead.get("email"):
            try: send_email(lead["email"], subject, body); status="SENT"
            except Exception as e: status=f"ERROR: {e}"
        df.at[idx,"score"]=score; df.at[idx,"persona"]=persona; df.at[idx,"priority"]=priority
        df.at[idx,"email_draft"]=body; df.at[idx,"status"]=status
        df.at[idx,"response_class"]=classify_response(body)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    total=len(df); high=(df["priority"]=="High").sum(); med=(df["priority"]=="Medium").sum(); low=(df["priority"]=="Low").sum()
    sent=(df["status"]=="SENT").sum()
    report=f"# Campaign Summary\n\n- Total leads processed: {total}\n- Emails sent (MailHog): {sent}\n- Priority split: High {high}, Medium {med}, Low {low}\n\n## Notes\n- Personalized via LLM (+ fallback).\n- SMTP to MailHog.\n- See `data/leads_enriched.csv`.\n"
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(os.path.join(REPORTS_DIR,"campaign_summary.md"),"w",encoding="utf-8") as f: f.write(report)
    return {"total": total, "sent": sent, "high": high, "medium": med, "low": low}