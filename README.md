# EHR Master v6 Embedded Human Resource

This version fully separates Coordinator and EHR Command Center routes.

## Critical Security Fix

Coordinator submit no longer redirects to EHR Command Center.

Coordinator routes:
- /coordinator-dashboard
- /submit-incident
- /coordinator-submitted/{case_id}
- /coordinator-file/{case_id}/{filename}

EHR Command Center routes:
- /dashboard
- /central-queue
- /case/{case_id}
- /case-file/{case_id}/{filename}
- /bulk-operations
- /executive-report

Coordinator accounts are blocked from every EHR Command Center route.

## Logins

EHR Command Center:
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
- Replaced with clean HR report sections, tables, color-coded scores, HR review checklist, policy assessment, labor standards review, missing requirements, uploaded files, and recommended next move.


## v6.2 Coordinator Status / Notice Workflow

Changed files:
- backend/main.py
- backend/static/case_detail.html
- backend/static/coordinator_status_detail.html
- backend/static/css/style.css

Fix:
- Coordinator dashboard status now shows: Waiting for EHR Command Center Notification.
- Clicking status opens a coordinator-only status detail page.
- EHR Command Center can upload memo/notice files to coordinator portal.
- Coordinator can download notice/memo files and serve/receive them with the worker.


## v6.3 Memo Sent Acknowledgement

Changed files:
- backend/main.py
- backend/static/case_detail.html
- backend/static/css/style.css

Fix:
- After EHR Command Center uploads/sends a memo, notice, or status file, the case detail page now shows a green success acknowledgement.
- A browser pop-up alert also confirms the memo/notice was sent successfully to the coordinator portal.


## v6.4 Clean Wording Update

Changed files:
- backend/main.py
- backend/static/*.html
- backend/static/css/style.css

Updates:
- Replaced repeated visible “due process” wording with cleaner HR terms such as Case Review, HR Review, Review Completion, and Labor Standards Check.
- Removed technical phrase “Hard Separated Routes” from the login and visible pages.
- Removed coordinator portal warning text saying coordinator cannot access EHR Command Center pages.
- Simplified branding to EHR / Embedded Human Resource.


## v7.0 Case Assessment Engine

Major added modules:
- backend/report_engine.py
- Editable DOCX case assessment report generator
- Central EHR case assessment report page upgraded into professional HR report format
- Evidence matrix
- Facts established from submitted documents
- Company Code of Conduct review first
- Philippine Labor Standards reference second
- Missing documents list
- Recommended next actions
- Downloadable editable Word report per case

Changed files:
- backend/main.py
- backend/report_engine.py
- backend/static/case_detail.html
- backend/static/css/style.css
- backend/requirements.txt
- backend/static/login.html

Important:
This version keeps the existing coordinator/Central EHR separation and only adds the assessment/report engine.


## v7.1 Fix

Fixed Central Case Detail route so all v7 report placeholders are populated correctly:
- Evidence matrix
- Facts list
- Recommended actions
- Labor law reference rows
- Evidence assessment level
- Downloadable Word report link
