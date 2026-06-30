# EHR Management System

Embedded Human Resource Management System  
Powered by Conglomerate Services

## Phase 1 Features

- Professional login page
- Dashboard
- Case Investigation page
- Company Policy placeholder
- Client Companies placeholder
- Case assessment engine
- Labor standards fallback
- JSON case report download

## Run Locally

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Notes

This is a decision-support system. Final HR action must be reviewed by authorized personnel after due process.
