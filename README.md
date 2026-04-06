# DesignMate AI

An autonomous multi-agent system for intelligent interior design with real-time product integration and budget optimization.

## Structure
- `designmate/` — FastAPI + LangGraph multi-agent pipeline (Python)
- `designmate-ui/` — Next.js + React Three Fiber dashboard (TypeScript)

## Backend setup
cd designmate
pip install -r requirements.txt
python -m uvicorn api:app --reload --port 8000

## Frontend setup
cd designmate-ui
npm install
npm run dev