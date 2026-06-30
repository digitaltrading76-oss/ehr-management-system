# EHR Master v6 Hard Separated Routes

This version fully separates Coordinator and Central Command routes.

## Critical Security Fix

Coordinator submit no longer redirects to Central Command.

Coordinator routes:
- /coordinator-dashboard
- /submit-incident
- /coordinator-submitted/{case_id}
- /coordinator-file/{case_id}/{filename}

Central Command routes:
- /dashboard
- /central-queue
- /case/{case_id}
- /case-file/{case_id}/{filename}
- /bulk-operations
- /executive-report

Coordinator accounts are blocked from every Central Command route.

## Logins

Central Command:
administrator / Conglomerate@2026
hr001 / Hr@2026

Coordinator:
coor001 / Coor@2026
coor002 / Coor@2026

## Render

Root Directory:
backend

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT

## Important GitHub instruction

Delete the old backend folder first, then upload this backend folder. Do not only add files on top of the old version.


## v6.1 Clean Assessment Report

Changed files:
- backend/main.py
- backend/static/case_detail.html
- backend/static/css/style.css

Fix:
- Removed messy raw JSON from Full Structured Assessment.
- Replaced with clean HR report sections, tables, color-coded scores, due process checklist, policy assessment, labor standards review, missing requirements, uploaded files, and recommended next move.


## v6.2 Coordinator Status / Notice Workflow

Changed files:
- backend/main.py
- backend/static/case_detail.html
- backend/static/coordinator_status_detail.html
- backend/static/css/style.css

Fix:
- Coordinator dashboard status now shows: Waiting for Central Command Notification.
- Clicking status opens a coordinator-only status detail page.
- Central Command can upload memo/notice files to coordinator portal.
- Coordinator can download notice/memo files and serve/receive them with the worker.
