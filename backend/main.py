from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from typing import List
from assessment_engine import assess_documents
import json, os, uuid, datetime

app = FastAPI(title="EHR Live Workflow Demo")
app.add_middleware(SessionMiddleware, secret_key="temporary-ehr-secret-change-before-production")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CASES_FILE = DATA_DIR / "cases.json"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
if not CASES_FILE.exists():
    CASES_FILE.write_text("[]", encoding="utf-8")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

USERS = {
 "administrator":{"password":"Conglomerate@2026","role":"administrator","name":"System Administrator","area":"Nationwide"},
 "hr001":{"password":"Hr@2026","role":"hr","name":"HR Officer 001","area":"Nationwide"},
 "coor001":{"password":"Coor@2026","role":"coordinator","name":"Coordinator 001","area":"Quezon City"},
 "coor002":{"password":"Coor@2026","role":"coordinator","name":"Coordinator 002","area":"Makati"},
 "coor003":{"password":"Coor@2026","role":"coordinator","name":"Coordinator 003","area":"Cebu"}
}

def load_cases():
    try:
        return json.loads(CASES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_cases(cases):
    CASES_FILE.write_text(json.dumps(cases, indent=2), encoding="utf-8")

def current_user(request):
    username=request.session.get("username")
    if not username or username not in USERS:
        return None
    return {"username":username, **USERS[username]}

def render(filename, request=None, extra=None):
    html=(BASE_DIR/"static"/filename).read_text(encoding="utf-8")
    user=current_user(request) if request else None
    if user:
        for k,v in user.items():
            html=html.replace("{{"+k.upper()+"}}", str(v))
    if extra:
        for k,v in extra.items():
            html=html.replace("{{"+k+"}}", str(v))
    return html

@app.get("/", response_class=HTMLResponse)
def login_page(request:Request):
    user=current_user(request)
    if user:
        return RedirectResponse("/coordinator-dashboard" if user["role"]=="coordinator" else "/dashboard", 302)
    return render("login.html")

@app.post("/login")
def login(request:Request, username:str=Form(""), password:str=Form("")):
    user=USERS.get(username)
    if user and user["password"] == password:
        request.session["username"] = username
        return RedirectResponse("/coordinator-dashboard" if user["role"]=="coordinator" else "/dashboard", 302)
    html=render("login.html").replace("<!--ERROR-->", "<div class='error-box'>Invalid username or password.</div>")
    return HTMLResponse(html, status_code=401)

@app.get("/logout")
def logout(request:Request):
    request.session.clear()
    return RedirectResponse("/",302)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request:Request):
    user=current_user(request)
    if not user: return RedirectResponse("/",302)
    if user["role"]=="coordinator": return RedirectResponse("/coordinator-dashboard",302)
    cases=load_cases()
    rows="".join([
        f"<tr><td><a href='/case/{c['case_id']}'>{c['case_id']}</a></td><td>{c['worker_name']}</td><td>{c['submitted_by']}</td><td>{c['area']}</td><td>{c['incident_category']}</td><td><span class='pill review'>{c['status']}</span></td></tr>"
        for c in cases[-8:][::-1]
    ]) or "<tr><td colspan='6'>No coordinator submissions yet.</td></tr>"
    return render("central_dashboard.html", request, {"CASE_ROWS":rows, "OPEN_CASES":len(cases)})

@app.get("/central-queue", response_class=HTMLResponse)
def central_queue(request:Request):
    user=current_user(request)
    if not user: return RedirectResponse("/",302)
    if user["role"]=="coordinator": return RedirectResponse("/coordinator-dashboard",302)
    cases=load_cases()
    rows="".join([
        f"<tr><td><a href='/case/{c['case_id']}'>{c['case_id']}</a></td><td>{c['worker_name']}</td><td>{c['worker_type']}</td><td>{c['submitted_by']}</td><td>{c['area']}</td><td>{c['incident_category']}</td><td>{c['readiness_score']}%</td><td><span class='pill review'>{c['status']}</span></td></tr>"
        for c in cases[::-1]
    ]) or "<tr><td colspan='8'>No submitted incidents yet. Login as coor001 and submit a case.</td></tr>"
    return render("central_queue.html", request, {"CASE_ROWS":rows})

@app.get("/case/{case_id}", response_class=HTMLResponse)
def view_case(case_id:str, request:Request):
    user=current_user(request)
    if not user: return RedirectResponse("/",302)
    cases=load_cases()
    case=next((c for c in cases if c["case_id"]==case_id), None)
    if not case:
        return HTMLResponse("Case not found", status_code=404)
    if user["role"]=="coordinator" and case["submitted_by"] != user["username"]:
        return HTMLResponse("Unauthorized", status_code=403)
    assessment=json.dumps(case["assessment"], indent=2)
    file_list="".join([f"<li>{f}</li>" for f in case.get("uploaded_files",[])]) or "<li>No uploaded file</li>"
    return render("case_detail.html", request, {
        "CASE_ID":case["case_id"],
        "WORKER_NAME":case["worker_name"],
        "WORKER_TYPE":case["worker_type"],
        "SUBMITTED_BY":case["submitted_by"],
        "AREA":case["area"],
        "INCIDENT_CATEGORY":case["incident_category"],
        "INCIDENT_SUMMARY":case["incident_summary"],
        "READINESS":case["readiness_score"],
        "STATUS":case["status"],
        "NEXT_MOVE":case["recommended_next_move"],
        "ASSESSMENT":assessment,
        "FILE_LIST":file_list
    })

@app.get("/coordinator-dashboard", response_class=HTMLResponse)
def coordinator_dashboard(request:Request):
    user=current_user(request)
    if not user: return RedirectResponse("/",302)
    if user["role"]!="coordinator": return RedirectResponse("/dashboard",302)
    cases=[c for c in load_cases() if c["submitted_by"]==user["username"]]
    rows="".join([
        f"<tr><td><a href='/case/{c['case_id']}'>{c['case_id']}</a></td><td>{c['worker_name']}</td><td>{c['worker_type']}</td><td>{c['incident_category']}</td><td><span class='pill review'>{c['status']}</span></td></tr>"
        for c in cases[::-1]
    ]) or "<tr><td colspan='5'>No submitted incident yet.</td></tr>"
    return render("coordinator_dashboard.html", request, {"MY_CASE_ROWS":rows, "MY_CASE_COUNT":len(cases)})

@app.get("/submit-incident", response_class=HTMLResponse)
def submit_incident(request:Request):
    if not current_user(request): return RedirectResponse("/",302)
    return render("submit_incident.html", request)

@app.post("/submit-incident")
async def submit_incident_post(request:Request, worker_name:str=Form(""), worker_type:str=Form(""), incident_category:str=Form(""), incident_summary:str=Form(""), files:List[UploadFile]=File(default=[])):
    user=current_user(request)
    if not user: return RedirectResponse("/",302)

    case_id="CASE-" + datetime.datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:5].upper()
    case_dir=UPLOAD_DIR/case_id
    case_dir.mkdir(exist_ok=True)

    uploaded=[]
    for f in files:
        if not f.filename: 
            continue
        safe=os.path.basename(f.filename)
        dest=case_dir/safe
        content=await f.read()
        dest.write_bytes(content)
        uploaded.append({"filename":safe,"content_type":f.content_type})

    assessment=assess_documents(user["username"], user["area"], worker_name, worker_type, incident_category, incident_summary, uploaded)

    case={
        "case_id":case_id,
        "submitted_at":datetime.datetime.now().isoformat(timespec="seconds"),
        "submitted_by":user["username"],
        "area":user["area"],
        "worker_name":worker_name,
        "worker_type":worker_type,
        "incident_category":incident_category,
        "incident_summary":incident_summary,
        "uploaded_files":[x["filename"] for x in uploaded],
        "assessment":assessment,
        "readiness_score":assessment["readiness_score"],
        "recommended_next_move":assessment["recommended_next_move"],
        "status":assessment["submission_status"]
    }
    cases=load_cases()
    cases.append(case)
    save_cases(cases)
    return RedirectResponse(f"/case/{case_id}", 302)

@app.get("/health")
def health():
    return {"status":"ok","version":"live-workflow-demo"}
