from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from assessment_engine import assess_case

app = FastAPI(title="EHR Management System")
app.add_middleware(SessionMiddleware, secret_key="temporary-ehr-secret-change-before-production")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

ADMIN_USERNAME = "administrator"
ADMIN_PASSWORD = "Conglomerate@2026"

def logged(request: Request):
    return request.session.get("logged_in") is True

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    if logged(request):
        return RedirectResponse("/dashboard", status_code=302)
    return (BASE_DIR / "static" / "login.html").read_text(encoding="utf-8")

@app.post("/login")
def login(request: Request, username: str = Form(""), password: str = Form("")):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["logged_in"] = True
        request.session["username"] = ADMIN_USERNAME
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
    if not logged(request):
        return RedirectResponse("/", status_code=302)
    return (BASE_DIR / "static" / "dashboard.html").read_text(encoding="utf-8")

@app.get("/case-investigation", response_class=HTMLResponse)
def case_investigation(request: Request):
    if not logged(request):
        return RedirectResponse("/", status_code=302)
    return (BASE_DIR / "static" / "case_investigation.html").read_text(encoding="utf-8")

@app.post("/assess")
def assess(request: Request, employee_name: str = Form(""), position: str = Form(""), incident_date: str = Form(""), incident_text: str = Form(""), prior_offense_count: int = Form(0)):
    if not logged(request):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    return JSONResponse(assess_case(employee_name, position, incident_date, incident_text, prior_offense_count))

@app.get("/health")
def health():
    return {"status": "ok", "system": "EHR Management System"}
