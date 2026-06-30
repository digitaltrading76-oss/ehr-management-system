# EHR Executive BI Dashboard Update

Includes:
- Enterprise-style Central Command dashboard
- Executive BI report center
- Color-coded KPI cards
- Case trend graph
- Case distribution visual chart
- Resolution performance bars
- Coordinator leaderboard
- Risk indicators
- Downloadable monthly CSV report
- Print / Save as PDF report page
- Coordinator portal
- Bulk incident document pre-review

## Render Settings

Root Directory:
backend

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT

## Logins

administrator / Conglomerate@2026  
hr001 / Hr@2026  
coor001 / Coor@2026  
coor002 / Coor@2026


## Logo Update

Conglomerate Corp logo has been inserted into:
- Login page
- Central Command dashboard sidebar
- Executive Report sidebar and print report
- Coordinator portal sidebar
- Submit Incident page sidebar

Logo path:
backend/static/assets/conglomerate_logo.png
