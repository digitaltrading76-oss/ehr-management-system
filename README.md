# EHR Live Workflow Demo

This version allows you to test the real workflow:

1. Login as coordinator:
   coor001 / Coor@2026

2. Submit incident report and upload files.

3. Logout.

4. Login as Central Command:
   administrator / Conglomerate@2026

5. Open Central Case Queue.

6. Review the uploaded coordinator case and see recommendation.

## Render Settings

Root Directory:
backend

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT
