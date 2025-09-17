import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import pandas as pd
import pipeline

load_dotenv()

app = FastAPI(title="Sales Campaign CRM MVP")

# Expose data/reports for download
app.mount("/files", StaticFiles(directory="."), name="files")

@app.get("/")
def root():
    return HTMLResponse("<h1>Sales Campaign CRM API</h1><p>Open the React app at <a href='http://localhost:3000'>http://localhost:3000</a></p>")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/leads")
def api_leads():
    leads_path = os.getenv("OUTPUT_PATH", "data/leads_enriched.csv")
    if not os.path.exists(leads_path):
        leads_path = os.getenv("LEADS_PATH", "data/leads.csv")
    if not os.path.exists(leads_path):
        return JSONResponse({"leads": []})
    df = pd.read_csv(leads_path)
    return JSONResponse({"leads": df.fillna("").to_dict(orient="records")})

@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    os.makedirs("data", exist_ok=True)
    target = "data/leads.csv"
    content = await file.read()
    with open(target, "wb") as f:
        f.write(content)
    return JSONResponse({"message": "Leads CSV uploaded. Click Run Campaign."})

@app.post("/run")
def run_pipeline():
    stats = pipeline.process_leads()
    return JSONResponse(stats)

@app.get("/reports/summary")
def read_summary():
    path = os.getenv("REPORTS_DIR", "reports")
    file = os.path.join(path, "campaign_summary.md")
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return PlainTextResponse(f.read())
    return JSONResponse({"error": "report not found"}, status_code=404)

if os.getenv("RUN_ON_START","1") == "1":
    try:
        pipeline.process_leads()
    except Exception as e:
        print("Startup run error:", e)