from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from typing import List
from assessment_engine import assess_documents

app = FastAPI(title="EHR Central Command System")
app.add_middleware(SessionMiddleware, secret_key="temporary-ehr-secret-change-before-production")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

USERS = {
    "administrator": {"password": "Conglomerate@2026", "role": "administrator", "name": "System Administrator", "area": "Nationwide"},
    "hr001": {"password": "Hr@2026", "role": "hr", "name": "HR Officer 001", "area": "Nationwide"},
    "hr002": {"password": "Hr@2026", "role": "hr", "name": "HR Officer 002", "area": "Nationwide"},
    "coor001": {"password": "Coor@2026", "role": "coordinator", "name": "Coordinator 001", "area": "Quezon City"},
    "coor002": {"password": "Coor@2026", "role": "coordinator", "name": "Coordinator 002", "area": "Makati"},
    "coor003": {"password": "Coor@2026", "role": "coordinator", "name": "Coordinator 003", "area": "Cebu"},
    "coor004": {"password": "Coor@2026", "role": "coordinator", "name": "Coordinator 004", "area": "Davao"},
    "coor005": {"password": "Coor@2026", "role": "coordinator", "name": "Coordinator 005", "area": "Batangas"},
    "coor006": {"password": "Coor@2026", "role": "coordinator", "name": "Coordinator 006", "area": "Pampanga"},
}

def current_user(request: Request):
    username = request.session.get("username")
    if not username:
        return None
    user = USERS.get(username)
    if not user:
        return None
    return {"username": username, **user}

def require_login(request: Request):
    return current_user(request) is not None

def render_html(filename: str, request: Request):
    html = (BASE_DIR / "static" / filename).read_text(encoding="utf-8")
    user = current_user(request)
    if user:
        html = html.replace("{{USERNAME}}", user["username"])
        html = html.replace("{{NAME}}", user["name"])
        html = html.replace("{{ROLE}}", user["role"].title())
        html = html.replace("{{AREA}}", user["area"])
    return html

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    user = current_user(request)
    if user:
        if user["role"] == "coordinator":
            return RedirectResponse("/coordinator-dashboard", status_code=302)
        return RedirectResponse("/dashboard", status_code=302)
    return (BASE_DIR / "static" / "login.html").read_text(encoding="utf-8")

@app.post("/login")
def login(request: Request, username: str = Form(""), password: str = Form("")):
    user = USERS.get(username)
    if user and user["password"] == password:
        request.session["username"] = username
        if user["role"] == "coordinator":
            return RedirectResponse("/coordinator-dashboard", status_code=302)
        return RedirectResponse("/dashboard", status_code=302)
    html = (BASE_DIR / "static" / "login.html").read_text(encoding="utf-8")
    html = html.replace("<!--ERROR-->", "<div class='error-box'>Invalid username or password.</div>")
    return HTMLResponse(html, status_code=401)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)
    if user["role"] == "coordinator":
        return RedirectResponse("/coordinator-dashboard", status_code=302)
    return render_html("central_dashboard.html", request)

@app.get("/coordinator-dashboard", response_class=HTMLResponse)
def coordinator_dashboard(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)
    if user["role"] != "coordinator":
        return RedirectResponse("/dashboard", status_code=302)
    return render_html("coordinator_dashboard.html", request)

@app.get("/submit-incident", response_class=HTMLResponse)
def submit_incident(request: Request):
    if not require_login(request):
        return RedirectResponse("/", status_code=302)
    return render_html("submit_incident.html", request)

@app.post("/assess-documents")
async def assess_upload(
    request: Request,
    worker_name: str = Form(""),
    worker_type: str = Form(""),
    incident_category: str = Form(""),
    incident_summary: str = Form(""),
    files: List[UploadFile] = File(default=[])
):
    user = current_user(request)
    if not user:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    uploaded = []
    for f in files:
        uploaded.append({
            "filename": f.filename,
            "content_type": f.content_type,
            "size_note": "Accepted for assessment simulation"
        })

    result = assess_documents(
        submitted_by=user["username"],
        area=user["area"],
        worker_name=worker_name,
        worker_type=worker_type,
        incident_category=incident_category,
        incident_summary=incident_summary,
        files=uploaded
    )
    return JSONResponse(result)

@app.get("/health")
def health():
    return {"status": "ok", "system": "EHR Central Command System"}
