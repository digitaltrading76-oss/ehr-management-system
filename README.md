# HR Case AI Web App MVP

This is a starter web app for AI-assisted HR incident assessment.

## Features
- Upload/paste company policy text
- Submit employee incident/explanation text
- AI-style rule matching against company policy rules
- Labor Code fallback when no company policy match is found
- Missing evidence checklist
- Follow-up questions
- Preliminary HR recommendation
- Downloadable case output as JSON

## Important
This app is for HR decision support only. It should not automatically discipline, suspend, or dismiss employees. HR/legal counsel must make the final decision after due process.

## Quick Start

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Optional AI Upgrade
You may connect OpenAI later by adding API logic inside `analyzer.py`.
