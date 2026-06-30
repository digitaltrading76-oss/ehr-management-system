from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from typing import List
from policy_engine import assess_case
from bulk_engine import parse_bulk_file, build_bulk_assessment, make_csv_template
import json, os, uuid, datetime

app = FastAPI(title="EHR Due Process Workflow")
app.add_middleware(SessionMiddleware, secret_key="temporary-ehr-secret-change-before-production")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CASES_FILE = DATA_DIR / "cases.json"
BULK_FILE = DATA_DIR / "bulk_batches.json"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
if not CASES_FILE.exists():
    CASES_FILE.write_text("[]", encoding="utf-8")
if not BULK_FILE.exists():
    BULK_FILE.write_text("[]", encoding="utf-8")

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

def load_bulk_batches():
    try:
        return json.loads(BULK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_bulk_batches(batches):
    BULK_FILE.write_text(json.dumps(batches, indent=2), encoding="utf-8")

def require_central(request):
    u=current_user(request)
    return u and u.get('role') in ['administrator','hr']

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

@app.get("/access-denied", response_class=HTMLResponse)
def access_denied(request:Request):
    return render("access_denied.html", request)

@app.get("/logout")
def logout(request:Request):
    request.session.clear()
    return RedirectResponse("/",302)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request:Request):
    user=current_user(request)
    if not require_central(request): return RedirectResponse("/access-denied",302)
    cases=load_cases()
    rows="".join([
        f"<tr><td><a href='/case/{c['case_id']}'>{c['case_id']}</a></td><td>{c['worker_name']}</td><td>{c['submitted_by']}</td><td>{c['area']}</td><td>{c['incident_category']}</td><td>{c['overall_readiness']}%</td><td><span class='pill review'>{c['status']}</span></td></tr>"
        for c in cases[-8:][::-1]
    ]) or "<tr><td colspan='7'>No coordinator submissions yet.</td></tr>"
    return render("central_dashboard.html", request, {"CASE_ROWS":rows, "OPEN_CASES":len(cases)})

@app.get("/central-queue", response_class=HTMLResponse)
def central_queue(request:Request):
    user=current_user(request)
    if not require_central(request): return RedirectResponse("/access-denied",302)
    cases=load_cases()
    rows="".join([
        f"<tr><td><a href='/case/{c['case_id']}'>{c['case_id']}</a></td><td>{c['worker_name']}</td><td>{c['worker_type']}</td><td>{c['submitted_by']}</td><td>{c['area']}</td><td>{c['incident_category']}</td><td>{c['due_process_score']}%</td><td>{c['overall_readiness']}%</td><td><span class='pill review'>{c['status']}</span></td></tr>"
        for c in cases[::-1]
    ]) or "<tr><td colspan='9'>No submitted incidents yet. Login as coor001 and submit a case.</td></tr>"
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

    a=case["assessment"]
    checklist="".join([f"<tr><td>{x['item']}</td><td>{'✅ Complete' if x['status'] else '❌ Missing / Pending'}</td></tr>" for x in a["due_process_checklist"]])
    policy="".join([f"<li><strong>{x.get('possible_violation','')}</strong><br>{x.get('policy_basis','')}<br><em>{x.get('usual_next_step','')}</em></li>" for x in a["policy_assessment"]])
    labor="".join([f"<li><strong>{x.get('labor_category','')}</strong><br>{x.get('legal_note','')}</li>" for x in a["labor_standards_review"]])
    files="".join([f"<li><a href='/case/{case_id}/file/{f}'>{f}</a></li>" for f in case.get("uploaded_files",[])]) or "<li>No uploaded file</li>"
    assessment=json.dumps(a, indent=2)

    return render("case_detail.html", request, {
        "CASE_ID":case["case_id"],
        "WORKER_NAME":case["worker_name"],
        "WORKER_TYPE":case["worker_type"],
        "SUBMITTED_BY":case["submitted_by"],
        "AREA":case["area"],
        "INCIDENT_CATEGORY":case["incident_category"],
        "INCIDENT_SUMMARY":case["incident_summary"],
        "DUE_PROCESS":case["due_process_score"],
        "READINESS":case["overall_readiness"],
        "STATUS":case["status"],
        "NEXT_MOVE":case["recommended_next_move"],
        "CHECKLIST":checklist,
        "POLICY_LIST":policy,
        "LABOR_LIST":labor,
        "FILE_LIST":files,
        "ASSESSMENT":assessment
    })

@app.get("/case/{case_id}/file/{filename}")
def download_case_file(case_id:str, filename:str, request:Request):
    user=current_user(request)
    if not user: return RedirectResponse("/",302)
    cases=load_cases()
    case=next((c for c in cases if c["case_id"]==case_id), None)
    if not case: return HTMLResponse("Case not found",404)
    if user["role"]=="coordinator" and case["submitted_by"] != user["username"]:
        return RedirectResponse("/access-denied",302)
    path=UPLOAD_DIR/case_id/os.path.basename(filename)
    if not path.exists(): return HTMLResponse("File not found",404)
    return FileResponse(path, filename=filename)

@app.get("/coordinator-dashboard", response_class=HTMLResponse)
def coordinator_dashboard(request:Request):
    user=current_user(request)
    if not user: return RedirectResponse("/",302)
    if user["role"]!="coordinator": return RedirectResponse("/dashboard",302)
    cases=[c for c in load_cases() if c["submitted_by"]==user["username"]]
    rows="".join([
        f"<tr><td><a href='/case/{c['case_id']}'>{c['case_id']}</a></td><td>{c['worker_name']}</td><td>{c['worker_type']}</td><td>{c['incident_category']}</td><td>{c['due_process_score']}%</td><td><span class='pill review'>{c['status']}</span></td></tr>"
        for c in cases[::-1]
    ]) or "<tr><td colspan='6'>No submitted incident yet.</td></tr>"
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

    uploaded_names=[x["filename"] for x in uploaded]
    assessment=assess_case(worker_name, worker_type, incident_category, incident_summary, uploaded_names, user["username"], user["area"])

    scores=assessment["scores"]
    if scores["due_process_completion"] < 45:
        status="Due Process Incomplete"
    elif scores["overall_readiness"] >= 70:
        status="Ready for Central Review"
    else:
        status="Needs Follow-up"

    case={
        "case_id":case_id,
        "submitted_at":datetime.datetime.now().isoformat(timespec="seconds"),
        "submitted_by":user["username"],
        "area":user["area"],
        "worker_name":worker_name,
        "worker_type":worker_type,
        "incident_category":incident_category,
        "incident_summary":incident_summary,
        "uploaded_files":uploaded_names,
        "assessment":assessment,
        "due_process_score":scores["due_process_completion"],
        "overall_readiness":scores["overall_readiness"],
        "recommended_next_move":assessment["recommended_next_move"],
        "status":status
    }
    cases=load_cases()
    cases.append(case)
    save_cases(cases)
    return RedirectResponse(f"/case/{case_id}", 302)


@app.get("/bulk-operations", response_class=HTMLResponse)
def bulk_operations(request:Request):
    user=current_user(request)
    if not require_central(request): return RedirectResponse("/access-denied",302)
    batches=load_bulk_batches()
    rows="".join([
        f"<tr><td><a href='/bulk-batch/{b['batch_id']}'>{b['batch_id']}</a></td><td>{b['total_records']}</td><td>{b['summary'].get('high_risk_cases',0)}</td><td>{b['summary'].get('nte_instructions',0)}</td><td>{b['summary'].get('ir_requests',0)}</td><td>{b['created_by']}</td></tr>"
        for b in batches[::-1]
    ]) or "<tr><td colspan='6'>No bulk operations uploaded yet.</td></tr>"
    return render("bulk_operations.html", request, {"BULK_ROWS":rows})

@app.post("/bulk-operations")
async def bulk_operations_post(request:Request, bulk_file:UploadFile=File(...), batch_note:str=Form("")):
    user=current_user(request)
    if not require_central(request): return RedirectResponse("/access-denied",302)
    content=await bulk_file.read()
    parsed=parse_bulk_file(bulk_file.filename, content)
    assessment=build_bulk_assessment(parsed)
    assessment["source_filename"]=bulk_file.filename
    assessment["batch_note"]=batch_note
    assessment["created_by"]=user["username"]
    assessment["created_at"]=datetime.datetime.now().isoformat(timespec="seconds")
    batches=load_bulk_batches()
    batches.append(assessment)
    save_bulk_batches(batches)
    return RedirectResponse(f"/bulk-batch/{assessment['batch_id']}",302)

@app.get("/bulk-batch/{batch_id}", response_class=HTMLResponse)
def view_bulk_batch(batch_id:str, request:Request):
    user=current_user(request)
    if not require_central(request): return RedirectResponse("/access-denied",302)
    batch=next((b for b in load_bulk_batches() if b["batch_id"]==batch_id), None)
    if not batch: return HTMLResponse("Batch not found",404)
    rows="".join([
        f"<tr><td>{x['worker_id']}</td><td>{x['worker_name']}</td><td>{x['worker_type']}</td><td>{x['coordinator']}</td><td>{x['location']}</td><td>{x['issue']}</td><td>{x['recommended_action']}</td></tr>"
        for x in batch["items"]
    ])
    return render("bulk_batch_detail.html", request, {
        "BATCH_ID":batch["batch_id"],
        "TOTAL":batch["total_records"],
        "HIGH_RISK":batch["summary"].get("high_risk_cases",0),
        "NTE":batch["summary"].get("nte_instructions",0),
        "IR":batch["summary"].get("ir_requests",0),
        "PAYROLL":batch["summary"].get("payroll_verification",0),
        "SOURCE":batch.get("source_filename",""),
        "BULK_ITEM_ROWS":rows
    })

@app.get("/bulk-batch/{batch_id}/download")
def download_bulk_template(batch_id:str, request:Request):
    user=current_user(request)
    if not user: return RedirectResponse("/",302)
    batch=next((b for b in load_bulk_batches() if b["batch_id"]==batch_id), None)
    if not batch: return HTMLResponse("Batch not found",404)
    csv_text=make_csv_template(batch["items"])
    return StreamingResponse(iter([csv_text]), media_type="text/csv", headers={"Content-Disposition":f"attachment; filename={batch_id}_coordinator_action_template.csv"})

@app.get("/executive-report", response_class=HTMLResponse)
def executive_report(request:Request):
    if not require_central(request): return RedirectResponse("/access-denied",302)
    return render("executive_report.html", request)

@app.get("/download-monthly-report")
def download_monthly_report(request:Request):
    if not require_central(request): return RedirectResponse("/access-denied",302)
    rows=[["Metric","Value","Notes"],["Open Cases",str(len(load_cases())),"Live submissions"],["Due Process","Enabled","No final action without worker due process"],["Bulk Operations","Enabled","Excel/CSV intake"],["Executive Reporting","Enabled","BI dashboard"]]
    import csv, io
    output=io.StringIO(); writer=csv.writer(output); writer.writerows(rows)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=ehr_monthly_operations_report.csv"})

@app.get("/health")
def health():
    return {"status":"ok","version":"due-process-workflow"}
