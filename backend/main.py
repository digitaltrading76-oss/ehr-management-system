from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from typing import List
from policy_engine import assess_case, extract_text_from_file
from bulk_engine import parse_bulk_file, build_bulk_assessment, make_csv_template
import json, os, uuid, datetime, csv, io

app=FastAPI(title="EHR v6 Hard Separated Routes")
app.add_middleware(SessionMiddleware, secret_key="temporary-ehr-secret-change-before-production")

BASE_DIR=Path(__file__).resolve().parent
DATA_DIR=BASE_DIR/"data"
UPLOAD_DIR=DATA_DIR/"uploads"
CASES_FILE=DATA_DIR/"cases.json"
BULK_FILE=DATA_DIR/"bulk_batches.json"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
if not CASES_FILE.exists(): CASES_FILE.write_text("[]",encoding="utf-8")
if not BULK_FILE.exists(): BULK_FILE.write_text("[]",encoding="utf-8")
app.mount("/static", StaticFiles(directory=BASE_DIR/"static"), name="static")

USERS={
 "administrator":{"password":"Conglomerate@2026","role":"administrator","name":"System Administrator","area":"Nationwide"},
 "hr001":{"password":"Hr@2026","role":"hr","name":"HR Officer 001","area":"Nationwide"},
 "coor001":{"password":"Coor@2026","role":"coordinator","name":"Coordinator 001","area":"Quezon City"},
 "coor002":{"password":"Coor@2026","role":"coordinator","name":"Coordinator 002","area":"Makati"}
}

def load_json(path):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return []
def save_json(path,data): path.write_text(json.dumps(data,indent=2),encoding="utf-8")
def load_cases(): return load_json(CASES_FILE)
def load_bulk(): return load_json(BULK_FILE)

def current_user(request):
    username=request.session.get("username")
    if not username or username not in USERS: return None
    return {"username":username, **USERS[username]}

def is_central(request):
    u=current_user(request)
    return bool(u and u["role"] in ["administrator","hr"])

def is_coordinator(request):
    u=current_user(request)
    return bool(u and u["role"]=="coordinator")

def render(filename, request=None, extra=None):
    html=(BASE_DIR/"static"/filename).read_text(encoding="utf-8")
    u=current_user(request) if request else None
    if u:
        for k,v in u.items(): html=html.replace("{{"+k.upper()+"}}",str(v))
    if extra:
        for k,v in extra.items(): html=html.replace("{{"+k+"}}",str(v))
    return html

@app.get("/", response_class=HTMLResponse)
def login_page(request:Request):
    u=current_user(request)
    if u:
        return RedirectResponse("/coordinator-dashboard" if u["role"]=="coordinator" else "/dashboard",302)
    return render("login.html")

@app.post("/login")
def login(request:Request, username:str=Form(""), password:str=Form("")):
    u=USERS.get(username)
    if u and u["password"]==password:
        request.session["username"]=username
        return RedirectResponse("/coordinator-dashboard" if u["role"]=="coordinator" else "/dashboard",302)
    return HTMLResponse(render("login.html").replace("<!--ERROR-->","<div class='error-box'>Invalid username or password.</div>"),401)

@app.get("/logout")
def logout(request:Request):
    request.session.clear()
    return RedirectResponse("/",302)

@app.get("/access-denied", response_class=HTMLResponse)
def access_denied(request:Request):
    return render("access_denied.html",request)

# ---------------- CENTRAL ONLY ----------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request:Request):
    if not is_central(request): return RedirectResponse("/access-denied",302)
    cases=load_cases()
    rows="".join([f"<tr><td><a href='/case/{c['case_id']}'>{c['case_id']}</a></td><td>{c['worker_name']}</td><td>{c['submitted_by']}</td><td>{c['area']}</td><td>{c['incident_category']}</td><td>{c['overall_readiness']}%</td><td><span class='pill review'>{c['status']}</span></td></tr>" for c in cases[-8:][::-1]]) or "<tr><td colspan='7'>No coordinator submissions yet.</td></tr>"
    return render("central_dashboard.html",request,{"CASE_ROWS":rows,"OPEN_CASES":len(cases)})

@app.get("/central-queue", response_class=HTMLResponse)
def central_queue(request:Request):
    if not is_central(request): return RedirectResponse("/access-denied",302)
    rows="".join([f"<tr><td><a href='/case/{c['case_id']}'>{c['case_id']}</a></td><td>{c['worker_name']}</td><td>{c['worker_type']}</td><td>{c['submitted_by']}</td><td>{c['area']}</td><td>{c['incident_category']}</td><td>{c['due_process_score']}%</td><td>{c['overall_readiness']}%</td><td><span class='pill review'>{c['status']}</span></td></tr>" for c in load_cases()[::-1]]) or "<tr><td colspan='9'>No submitted incidents yet.</td></tr>"
    return render("central_queue.html",request,{"CASE_ROWS":rows})

@app.get("/case/{case_id}", response_class=HTMLResponse)
def central_case_detail(case_id:str, request:Request):
    if not is_central(request): return RedirectResponse("/access-denied",302)
    notice_sent = request.query_params.get("notice_sent") == "1"
    sent_type = request.query_params.get("notice_type", "")
    case=next((c for c in load_cases() if c["case_id"]==case_id),None)
    if not case: return HTMLResponse("Case not found",404)
    a=case["assessment"]
    checklist="".join([f"<tr><td>{x['item']}</td><td><span class='status-ok'>✅ Complete</span></td></tr>" if x["status"] else f"<tr><td>{x['item']}</td><td><span class='status-missing'>❌ Missing / Pending</span></td></tr>" for x in a["due_process_checklist"]])
    policy_rows="".join([f"<tr><td>{x.get('policy_category','')}</td><td>{x.get('possible_violation','')}</td><td>{x.get('policy_basis','')}</td><td>{x.get('usual_next_step','')}</td></tr>" for x in a["policy_assessment"]])
    labor_rows="".join([f"<tr><td>{x.get('labor_category','')}</td><td>{x.get('legal_note','')}</td></tr>" for x in a["labor_standards_review"]])
    missing_rows="".join([f"<li>{m}</li>" for m in a.get("missing_requirements",[])]) or "<li>No missing requirement identified.</li>"
    files="".join([f"<li><a href='/case-file/{case_id}/{f}'>{f}</a></li>" for f in case.get("uploaded_files",[])]) or "<li>No uploaded file</li>"
    scores=a.get("scores",{})
    return render("case_detail.html",request,{
        "CASE_ID":case_id,
        "WORKER_NAME":case["worker_name"],
        "WORKER_TYPE":case["worker_type"],
        "AREA":case["area"],
        "INCIDENT_CATEGORY":case["incident_category"],
        "EXTRACTED_PREVIEW":a.get("extracted_content_preview",""),
        "DUE_PROCESS":case["due_process_score"],
        "READINESS":case["overall_readiness"],
        "STATUS":case["status"],
        "NEXT_MOVE":case["recommended_next_move"],
        "CHECKLIST":checklist,
        "POLICY_ROWS":policy_rows,
        "LABOR_ROWS":labor_rows,
        "MISSING_LIST":missing_rows,
        "FILE_LIST":files,
        "POLICY_SCORE":scores.get("company_policy_match",0),
        "LABOR_SCORE":scores.get("labor_standards_relevance",0),
        "EVIDENCE_SCORE":scores.get("evidence_sufficiency",0),
        "DUE_PROCESS_SCORE":scores.get("due_process_completion",0),
        "OVERALL_SCORE":scores.get("overall_readiness",0),
        "SAFEGUARD":a.get("safeguard","No final disciplinary action should be recommended until the worker has been properly notified and given an opportunity to respond."),
        "NOTICE_ACK":f"<div class='success-alert'>✅ {sent_type or 'Memo / notice'} has been sent successfully to the coordinator portal.</div>" if notice_sent else ""
    })

@app.get("/case-file/{case_id}/{filename}")
def central_case_file(case_id:str, filename:str, request:Request):
    if not is_central(request): return RedirectResponse("/access-denied",302)
    path=UPLOAD_DIR/case_id/os.path.basename(filename)
    if not path.exists(): return HTMLResponse("File not found",404)
    return FileResponse(path, filename=filename)

@app.get("/bulk-operations", response_class=HTMLResponse)
def bulk_operations(request:Request):
    if not is_central(request): return RedirectResponse("/access-denied",302)
    rows="".join([f"<tr><td><a href='/bulk-batch/{b['batch_id']}'>{b['batch_id']}</a></td><td>{b['total_records']}</td><td>{b['summary'].get('high_risk_cases',0)}</td><td>{b['summary'].get('nte_instructions',0)}</td><td>{b['summary'].get('ir_requests',0)}</td><td>{b['created_by']}</td></tr>" for b in load_bulk()[::-1]]) or "<tr><td colspan='6'>No bulk operations uploaded yet.</td></tr>"
    return render("bulk_operations.html",request,{"BULK_ROWS":rows})

@app.post("/bulk-operations")
async def bulk_operations_post(request:Request, bulk_file:UploadFile=File(...), batch_note:str=Form("")):
    u=current_user(request)
    if not is_central(request): return RedirectResponse("/access-denied",302)
    assessment=build_bulk_assessment(parse_bulk_file(bulk_file.filename, await bulk_file.read()))
    assessment.update({"source_filename":bulk_file.filename,"batch_note":batch_note,"created_by":u["username"],"created_at":datetime.datetime.now().isoformat(timespec="seconds")})
    batches=load_bulk(); batches.append(assessment); save_json(BULK_FILE,batches)
    return RedirectResponse(f"/bulk-batch/{assessment['batch_id']}",302)

@app.get("/bulk-batch/{batch_id}", response_class=HTMLResponse)
def view_bulk_batch(batch_id:str, request:Request):
    if not is_central(request): return RedirectResponse("/access-denied",302)
    batch=next((b for b in load_bulk() if b["batch_id"]==batch_id),None)
    if not batch: return HTMLResponse("Batch not found",404)
    rows="".join([f"<tr><td>{x['worker_id']}</td><td>{x['worker_name']}</td><td>{x['worker_type']}</td><td>{x['coordinator']}</td><td>{x['location']}</td><td>{x['issue']}</td><td>{x['recommended_action']}</td></tr>" for x in batch["items"]])
    return render("bulk_batch_detail.html",request,{"BATCH_ID":batch_id,"TOTAL":batch["total_records"],"HIGH_RISK":batch["summary"].get("high_risk_cases",0),"NTE":batch["summary"].get("nte_instructions",0),"IR":batch["summary"].get("ir_requests",0),"SOURCE":batch.get("source_filename",""),"BULK_ITEM_ROWS":rows})

@app.get("/bulk-batch/{batch_id}/download")
def download_bulk_template(batch_id:str, request:Request):
    if not is_central(request): return RedirectResponse("/access-denied",302)
    batch=next((b for b in load_bulk() if b["batch_id"]==batch_id),None)
    if not batch: return HTMLResponse("Batch not found",404)
    return StreamingResponse(iter([make_csv_template(batch["items"])]), media_type="text/csv", headers={"Content-Disposition":f"attachment; filename={batch_id}_coordinator_action_template.csv"})

@app.get("/executive-report", response_class=HTMLResponse)
def executive_report(request:Request):
    if not is_central(request): return RedirectResponse("/access-denied",302)
    return render("executive_report.html",request)

@app.get("/download-monthly-report")
def download_monthly_report(request:Request):
    if not is_central(request): return RedirectResponse("/access-denied",302)
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerow(["Metric","Value","Notes"])
    writer.writerows([["Open Cases",str(len(load_cases())),"Live submissions"],["HR Review Safeguard","Enabled","No final action without worker notice and opportunity to respond"],["Bulk Operations","Enabled","Excel/CSV intake"],["Executive Reporting","Enabled","BI dashboard"]])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=ehr_monthly_operations_report.csv"})

# ---------------- COORDINATOR ONLY ----------------
@app.get("/coordinator-dashboard", response_class=HTMLResponse)
def coordinator_dashboard(request:Request):
    u=current_user(request)
    if not u: return RedirectResponse("/",302)
    if u["role"]!="coordinator": return RedirectResponse("/dashboard",302)
    my=[c for c in load_cases() if c["submitted_by"]==u["username"]]
    rows="".join([f"<tr><td><a href='/coordinator-submitted/{c['case_id']}'>{c['case_id']}</a></td><td>{c['worker_name']}</td><td>{c['worker_type']}</td><td>{c['incident_category']}</td><td>{c['due_process_score']}%</td><td><a class='pill waiting' href='/coordinator-status/{c['case_id']}'>{c.get('coordinator_status','Waiting for Central Command Notification')}</a></td></tr>" for c in my[::-1]]) or "<tr><td colspan='6'>No submitted incident yet.</td></tr>"
    return render("coordinator_dashboard.html",request,{"MY_CASE_ROWS":rows,"MY_CASE_COUNT":len(my)})

@app.get("/submit-incident", response_class=HTMLResponse)
def submit_incident(request:Request):
    if not is_coordinator(request): return RedirectResponse("/access-denied",302)
    return render("submit_incident.html",request)

@app.post("/submit-incident")
async def submit_incident_post(request:Request, worker_name:str=Form(""), worker_type:str=Form(""), incident_category:str=Form(""), upload_mode:str=Form("individual"), files:List[UploadFile]=File(default=[])):
    u=current_user(request)
    if not u: return RedirectResponse("/",302)
    if u["role"]!="coordinator": return RedirectResponse("/access-denied",302)
    valid=[f for f in files if f.filename]
    if not valid:
        return HTMLResponse(render("submit_incident.html",request).replace("<!--ERROR-->","<div class='error-box'>Please upload at least one incident report or supporting document before submitting.</div>"),400)

    case_id="CASE-"+datetime.datetime.now().strftime("%Y%m%d")+"-"+uuid.uuid4().hex[:5].upper()
    case_dir=UPLOAD_DIR/case_id
    case_dir.mkdir(exist_ok=True)

    uploaded=[]
    extracted=[]
    for f in valid:
        safe=os.path.basename(f.filename)
        content=await f.read()
        (case_dir/safe).write_bytes(content)
        uploaded.append(safe)
        extracted.append(f"--- {safe} ---\\n"+extract_text_from_file(safe, content))
    extracted_text="\\n\\n".join(extracted)

    assessment=assess_case(worker_name,worker_type,incident_category,extracted_text,uploaded,u["username"],u["area"])
    scores=assessment["scores"]
    status="Review Incomplete" if scores["due_process_completion"]<45 else "Ready for Central Review" if scores["overall_readiness"]>=70 else "Needs Follow-up"
    case={"case_id":case_id,"submitted_at":datetime.datetime.now().isoformat(timespec="seconds"),"submitted_by":u["username"],"area":u["area"],"worker_name":worker_name,"worker_type":worker_type,"incident_category":incident_category,"upload_mode":upload_mode,"extracted_text":extracted_text,"uploaded_files":uploaded,"assessment":assessment,"due_process_score":scores["due_process_completion"],"overall_readiness":scores["overall_readiness"],"recommended_next_move":assessment["recommended_next_move"],"status":status,"coordinator_status":"Waiting for Central Command Notification","central_notices":[]}
    cases=load_cases(); cases.append(case); save_json(CASES_FILE,cases)

    # HARD RULE: coordinator goes only to coordinator route, never /case
    return RedirectResponse(f"/coordinator-submitted/{case_id}",302)

@app.get("/coordinator-submitted/{case_id}", response_class=HTMLResponse)
def coordinator_submitted(case_id:str, request:Request):
    u=current_user(request)
    if not u: return RedirectResponse("/",302)
    if u["role"]!="coordinator": return RedirectResponse("/dashboard",302)
    case=next((c for c in load_cases() if c["case_id"]==case_id and c["submitted_by"]==u["username"]),None)
    if not case: return RedirectResponse("/access-denied",302)
    files="".join([f"<li><a href='/coordinator-file/{case_id}/{f}'>{f}</a></li>" for f in case.get("uploaded_files",[])]) or "<li>No uploaded file</li>"
    return render("coordinator_submitted.html",request,{"CASE_ID":case_id,"WORKER_NAME":case["worker_name"],"WORKER_TYPE":case["worker_type"],"INCIDENT_CATEGORY":case["incident_category"],"STATUS":case["status"],"DUE_PROCESS":case["due_process_score"],"FILE_LIST":files})

@app.get("/coordinator-file/{case_id}/{filename}")
def coordinator_file(case_id:str, filename:str, request:Request):
    u=current_user(request)
    if not u: return RedirectResponse("/",302)
    if u["role"]!="coordinator": return RedirectResponse("/dashboard",302)
    case=next((c for c in load_cases() if c["case_id"]==case_id and c["submitted_by"]==u["username"]),None)
    if not case: return RedirectResponse("/access-denied",302)
    path=UPLOAD_DIR/case_id/os.path.basename(filename)
    if not path.exists(): return HTMLResponse("File not found",404)
    return FileResponse(path, filename=filename)


@app.get("/coordinator-status/{case_id}", response_class=HTMLResponse)
def coordinator_status_detail(case_id:str, request:Request):
    u=current_user(request)
    if not u: return RedirectResponse("/",302)
    if u["role"]!="coordinator": return RedirectResponse("/access-denied",302)

    case=next((c for c in load_cases() if c["case_id"]==case_id and c["submitted_by"]==u["username"]), None)
    if not case: return RedirectResponse("/access-denied",302)

    notices=case.get("central_notices",[])
    if notices:
        notice_rows="".join([
            f"<tr><td>{n.get('notice_type','Notice')}</td><td>{n.get('remarks','')}</td><td>{n.get('uploaded_at','')}</td><td><a class='btn' href='/coordinator-notice-file/{case_id}/{n.get('filename','')}'>Download</a></td></tr>"
            for n in notices
        ])
    else:
        notice_rows="<tr><td colspan='4'>No memo, notice, or document uploaded yet by Central Command.</td></tr>"

    return render("coordinator_status_detail.html", request, {
        "CASE_ID":case_id,
        "WORKER_NAME":case.get("worker_name",""),
        "WORKER_TYPE":case.get("worker_type",""),
        "INCIDENT_CATEGORY":case.get("incident_category",""),
        "COORDINATOR_STATUS":case.get("coordinator_status","Waiting for Central Command Notification"),
        "NOTICE_ROWS":notice_rows
    })

@app.get("/coordinator-notice-file/{case_id}/{filename}")
def coordinator_notice_file(case_id:str, filename:str, request:Request):
    u=current_user(request)
    if not u: return RedirectResponse("/",302)
    if u["role"]!="coordinator": return RedirectResponse("/access-denied",302)

    case=next((c for c in load_cases() if c["case_id"]==case_id and c["submitted_by"]==u["username"]), None)
    if not case: return RedirectResponse("/access-denied",302)

    allowed=[n.get("filename") for n in case.get("central_notices",[])]
    if filename not in allowed:
        return RedirectResponse("/access-denied",302)

    path=UPLOAD_DIR/case_id/"central_notices"/os.path.basename(filename)
    if not path.exists(): return HTMLResponse("File not found",404)
    return FileResponse(path, filename=filename)

@app.post("/case/{case_id}/central-notice")
async def upload_central_notice(case_id:str, request:Request, notice_type:str=Form("Additional Documents Required"), remarks:str=Form(""), notice_file:UploadFile=File(...)):
    u=current_user(request)
    if not is_central(request): return RedirectResponse("/access-denied",302)

    cases=load_cases()
    case=next((c for c in cases if c["case_id"]==case_id), None)
    if not case: return HTMLResponse("Case not found",404)

    if not notice_file.filename:
        return RedirectResponse(f"/case/{case_id}?notice_sent=1&notice_type={notice_type}",302)

    notice_dir=UPLOAD_DIR/case_id/"central_notices"
    notice_dir.mkdir(exist_ok=True)

    safe=os.path.basename(notice_file.filename)
    content=await notice_file.read()
    (notice_dir/safe).write_bytes(content)

    if "central_notices" not in case:
        case["central_notices"]=[]

    case["central_notices"].append({
        "filename":safe,
        "notice_type":notice_type,
        "remarks":remarks,
        "uploaded_by":u["username"],
        "uploaded_at":datetime.datetime.now().isoformat(timespec="seconds")
    })

    case["coordinator_status"]=notice_type
    save_json(CASES_FILE,cases)

    return RedirectResponse(f"/case/{case_id}?notice_sent=1&notice_type={notice_type}",302)

@app.get("/health")
def health():
    return {"status":"ok","version":"v6-hard-separated-routes"}
