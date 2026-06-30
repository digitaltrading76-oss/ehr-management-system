# EHR Due Process Workflow

Embedded Human Resource Central Command System  
Powered by Conglomerate Corp

## Purpose

This version makes Philippine labor due process the core workflow.

Coordinator submits incident → system checks:
- Company policy match
- Labor standards category
- Evidence completeness
- Due process completion
- Recommended next move

Central Command reviews the case before any NTE, decision, suspension, or dismissal.

## Sample Login

Coordinator:
coor001 / Coor@2026

Central Command:
administrator / Conglomerate@2026

## Render Settings

Root Directory:
backend

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT


## Bulk Operations Intake

Central Command can upload operations lists in Excel/CSV/TXT format and generate:
- Bulk coordinator action list
- IR request instructions
- NTE instruction flags
- Payroll verification flags
- High-risk fraud/theft escalation flags
- Downloadable CSV template for coordinator action
