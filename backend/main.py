from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from typing import List
from assessment_engine import assess_documents
import csv, io

app = FastAPI(title="EHR Central Command System")
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
    u=request.session.get("username")
    if not u or u not in USERS: return None
    return {"username":u, **USERS[u]}

def render(filename, request):
    html=(BASE_DIR/"static"/filename).read_text(encoding="utf-8")
    u=current_user(request)
    if u:
        for k,v in u.items(): html=html.replace("{{"+k.upper()+"}}", str(v))
    return html

@app.get("/", response_class=HTMLResponse)
def login_page(request:Request):
    u=current_user(request)
    if u: return RedirectResponse("/coordinator-dashboard" if u["role"]=="coordinator" else "/dashboard", 302)
    return (BASE_DIR/"static"/"login.html").read_text(encoding="utf-8")

@app.post("/login")
def login(request:Request, username:str=Form(""), password:str=Form("")):
    u=USERS.get(username)
    if u and u["password"]==password:
        request.session["username"]=username
        return RedirectResponse("/coordinator-dashboard" if u["role"]=="coordinator" else "/dashboard", 302)
    html=(BASE_DIR/"static"/"login.html").read_text(encoding="utf-8").replace("<!--ERROR-->","<div class='error-box'>Invalid username or password.</div>")
    return HTMLResponse(html,401)

@app.get("/logout")
def logout(request:Request):
    request.session.clear()
    return RedirectResponse("/",302)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request:Request):
    u=current_user(request)
    if not u: return RedirectResponse("/",302)
    if u["role"]=="coordinator": return RedirectResponse("/coordinator-dashboard",302)
    return render("central_dashboard.html", request)

@app.get("/executive-report", response_class=HTMLResponse)
def executive_report(request:Request):
    u=current_user(request)
    if not u: return RedirectResponse("/",302)
    if u["role"]=="coordinator": return RedirectResponse("/coordinator-dashboard",302)
    return render("executive_report.html", request)

@app.get("/coordinator-dashboard", response_class=HTMLResponse)
def coordinator_dashboard(request:Request):
    u=current_user(request)
    if not u: return RedirectResponse("/",302)
    if u["role"]!="coordinator": return RedirectResponse("/dashboard",302)
    return render("coordinator_dashboard.html", request)

@app.get("/submit-incident", response_class=HTMLResponse)
def submit_incident(request:Request):
    if not current_user(request): return RedirectResponse("/",302)
    return render("submit_incident.html", request)

@app.post("/assess-documents")
async def assess_upload(request:Request, worker_name:str=Form(""), worker_type:str=Form(""), incident_category:str=Form(""), incident_summary:str=Form(""), files:List[UploadFile]=File(default=[])):
    u=current_user(request)
    if not u: return JSONResponse({"error":"Not authenticated"},401)
    uploaded=[{"filename":f.filename,"content_type":f.content_type} for f in files]
    return JSONResponse(assess_documents(u["username"],u["area"],worker_name,worker_type,incident_category,incident_summary,uploaded))

@app.get("/download-monthly-report")
def download_monthly_report(request:Request):
    u=current_user(request)
    if not u: return RedirectResponse("/",302)
    rows=[
      ["Metric","Value","Notes"],
      ["Total Workers","1248","Riders, drivers, walkers, backroom"],
      ["Active Coordinators","24","Nationwide"],
      ["Open Cases","96","Pending as of month end"],
      ["Closed Cases","318","Closed this month"],
      ["Average Resolution Time","2.8 days","Target below 3 days"],
      ["Overdue Cases","7","Requires escalation"],
      ["Salary Complaints","78","Top category"],
      ["Accident Cases","56","Safety monitoring"],
      ["Theft/Fraud Cases","37","High risk"],
      ["Attendance/AWOL Cases","46","Policy monitoring"]
    ]
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=ehr_monthly_operations_report.csv"})

@app.get("/health")
def health():
    return {"status":"ok"}
