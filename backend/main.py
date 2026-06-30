from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from analyzer import analyze_case

app = FastAPI(title="EHR Management System")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
def login():
    return (BASE_DIR / "static" / "login.html").read_text(encoding="utf-8")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return (BASE_DIR / "static" / "dashboard.html").read_text(encoding="utf-8")

@app.get("/case-investigation", response_class=HTMLResponse)
def case_investigation():
    return (BASE_DIR / "static" / "case_investigation.html").read_text(encoding="utf-8")

@app.post("/analyze")
def analyze(
    employee_name: str = Form(""),
    position: str = Form(""),
    incident_date: str = Form(""),
    incident_text: str = Form(""),
    prior_offense_count: int = Form(0),
):
    result = analyze_case(
        employee_name=employee_name,
        position=position,
        incident_date=incident_date,
        incident_text=incident_text,
        prior_offense_count=prior_offense_count,
    )
    return JSONResponse(result)

@app.get("/health")
def health():
    return {"status": "ok", "system": "EHR Management System"}
