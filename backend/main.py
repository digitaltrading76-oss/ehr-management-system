from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from typing import List
from assessment_engine import assess_documents
import csv, io

app = FastAPI(title="EHR Management System v2.0")
app.add_middleware(SessionMiddleware, secret_key="temporary-ehr-secret-change-before-production")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

USERS = {
 "administrator":{"password":"Conglomerate@2026","role":"administrator","name":"System Administrator","area":"Nationwide"},
 "hr001":{"password":"Hr@2026","role":"hr","name":"HR Officer 001","area":"Nationwide"},
 "hr002":{"password":"Hr@2026","role":"hr","name":"HR Officer 002","area":"Nationwide"},
 "coor001":{"password":"Coor@2026","role":"coordinator","name":"Coordinator 001","area":"Quezon City"},
 "coor002":{"password":"Coor@2026","role":"coordinator","name":"Coordinator 002","area":"Makati"},
 "coor003":{"password":"Coor@2026","role":"coordinator","name":"Coordinator 003","area":"Cebu"},
 "coor004":{"password":"Coor@2026","role":"coordinator","name":"Coordinator 004","area":"Davao"},
 "coor005":{"password":"Coor@2026","role":"coordinator","name":"Coordinator 005","area":"Batangas"},
 "coor006":{"password":"Coor@2026","role":"coordinator","name":"Coordinator 006","area":"Pampanga"}
}

def current_user(request):
    username = request.session.get("username")
    if not username or username not in USERS:
        return None
    return {"username": username, **USERS[username]}

def html(filename, request=None):
    page = (BASE_DIR / "static" / filename).read_text(encoding="utf-8")
    if request:
        user = current_user(request)
        if user:
            for k, v in user.items():
                page = page.replace("{{" + k.upper() + "}}", str(v))
    return page

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    user=current_user(request)
    if user:
        return RedirectResponse("/coordinator-dashboard" if user["role"]=="coordinator" else "/dashboard", 302)
    return html("login.html")

@app.post("/login")
def login(request: Request, username: str = Form(""), password: str = Form("")):
    user=USERS.get(username)
    if user and user["password"] == password:
        request.session["username"] = username
        return RedirectResponse("/coordinator-dashboard" if user["role"]=="coordinator" else "/dashboard", 302)
    page=html("login.html").replace("<!--ERROR-->", "<div class='error-box'>Invalid username or password.</div>")
    return HTMLResponse(page, status_code=401)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", 302)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user=current_user(request)
    if not user:
        return RedirectResponse("/", 302)
    if user["role"]=="coordinator":
        return RedirectResponse("/coordinator-dashboard", 302)
    return html("central_dashboard.html", request)

@app.get("/executive-report", response_class=HTMLResponse)
def executive_report(request: Request):
    user=current_user(request)
    if not user:
        return RedirectResponse("/", 302)
    if user["role"]=="coordinator":
        return RedirectResponse("/coordinator-dashboard", 302)
    return html("executive_report.html", request)

@app.get("/coordinator-dashboard", response_class=HTMLResponse)
def coordinator_dashboard(request: Request):
    user=current_user(request)
    if not user:
        return RedirectResponse("/", 302)
    if user["role"]!="coordinator":
        return RedirectResponse("/dashboard", 302)
    return html("coordinator_dashboard.html", request)

@app.get("/submit-incident", response_class=HTMLResponse)
def submit_incident(request: Request):
    if not current_user(request):
        return RedirectResponse("/", 302)
    return html("submit_incident.html", request)

@app.post("/assess-documents")
async def assess_upload(request: Request, worker_name: str = Form(""), worker_type: str = Form(""), incident_category: str = Form(""), incident_summary: str = Form(""), files: List[UploadFile] = File(default=[])):
    user=current_user(request)
    if not user:
        return JSONResponse({"error":"Not authenticated"}, status_code=401)
    uploaded=[{"filename":f.filename, "content_type":f.content_type} for f in files]
    return JSONResponse(assess_documents(user["username"], user["area"], worker_name, worker_type, incident_category, incident_summary, uploaded))

@app.get("/download-monthly-report")
def download_monthly_report(request: Request):
    if not current_user(request):
        return RedirectResponse("/", 302)

    rows=[
      ["Metric","Value","Notes"],
      ["Total Workers","1248","Riders, drivers, walkers, warehouse/backroom"],
      ["Active Coordinators","24","Nationwide"],
      ["Total Cases","414","June 2026"],
      ["Closed Cases","318","Closed this month"],
      ["Closure Rate","76.8%","Management KPI"],
      ["Average Resolution Time","2.8 days","Target below 3 days"],
      ["Overdue Cases","7","Requires escalation"],
      ["Parcel/Delivery Issues","101","Highest operational category"],
      ["Salary Complaints","78","Payroll verification required"],
      ["Accident Cases","56","Safety monitoring"],
      ["Attendance/AWOL Cases","46","Policy monitoring"],
      ["Theft/Fraud Cases","37","High-risk category"]
    ]
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=ehr_monthly_operations_report.csv"})

@app.get("/health")
def health():
    return {"status":"ok","version":"2.0"}
