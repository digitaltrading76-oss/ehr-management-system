# EHR Central Command Role Portal

Embedded Human Resource Central Command System  
Powered by Conglomerate Services

## Sample Login Accounts

Administrator:
- username: administrator
- password: Conglomerate@2026

HR Officers:
- username: hr001
- password: Hr@2026
- username: hr002
- password: Hr@2026

Coordinators:
- username: coor001
- password: Coor@2026
- area: Quezon City

- username: coor002
- password: Coor@2026
- area: Makati

- username: coor003
- password: Coor@2026
- area: Cebu

- username: coor004
- password: Coor@2026
- area: Davao

- username: coor005
- password: Coor@2026
- area: Batangas

- username: coor006
- password: Coor@2026
- area: Pampanga

## Render Settings

Root Directory:
backend

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT
