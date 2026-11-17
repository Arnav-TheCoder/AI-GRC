# AI GRC MVP

Starter application for an AI model governance, risk and compliance assessment.

## Stack
- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- Database: SQLite + SQLAlchemy
- Upload handling: ZIP inspection without executing uploaded code

## Requirements
- Python 3.10+
- Node.js 20+

## 1. Start the backend (Windows PowerShell)

```powershell
cd Backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

If Python 3.13 is not installed, use `python` instead of `py -3.13`.

Backend: http://127.0.0.1:8000  
API docs: http://127.0.0.1:8000/docs

## 2. Start the frontend (new terminal)

```powershell
cd Frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Frontend: http://localhost:5173

## Current functionality
- Create and persist assessments
- Upload a model ZIP
- Safely inspect archive paths, file names, sizes and common model/config files
- Upload optional training, validation and test CSV files
- Persist upload metadata in SQLite
- View assessment details and upload status

## Important security notes
- Uploaded ZIP contents are never extracted or executed.
- The backend rejects path traversal entries, encrypted entries, oversized archives,
  excessive file counts and suspicious compression ratios.
- This is a prototype intake/inspection layer, not a malware scanner or model safety certification.
- Do not upload real personal, confidential or production data to an unsecured demo deployment.
