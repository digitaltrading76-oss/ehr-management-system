# EHR Central Command Master Merged v3

This is the consolidated package. It retains all approved updates:
- Central Command dashboard
- Coordinator portal
- Strict role-based access control
- Uploaded supporting file access in case detail
- Due process workflow
- Company policy and Philippine labor standards review
- Central Case Queue
- Bulk Operations Intake for Excel/CSV/TXT
- Downloadable bulk action CSV
- Executive BI reporting dashboard
- Monthly CSV report download
- Proper Conglomerate Corp logo sizing

## Logins
administrator / Conglomerate@2026
hr001 / Hr@2026
coor001 / Coor@2026

## Render
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT


## Security Fix

- Coordinator submission now redirects only to `/coordinator-case/{case_id}`.
- Coordinators cannot open `/dashboard`, `/central-queue`, `/bulk-operations`, `/executive-report`, or `/case/{case_id}`.
- Central Command case detail and file access are HR/Admin-only.
- Coordinator can only view their own submitted case copy and their own uploaded files.
