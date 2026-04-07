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



## What it does
1. You upload a photo of an empty room and set a budget
2. The AI analyzes the room, generates 3 design concepts, sources real furniture products, and renders photorealistic images
3. You can refine designs conversationally — "make it more rustic" or "reduce the budget"
4. Every agent decision is visible in real-time via the Agent Thought Trace panel


## How to run

### Step 1 - Backend
```bash
cd designmate
py -3.13 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn api:app --reload --port 8000
```

Create a `.env` file inside `designmate/` with your API keys:
GROQ_API_KEY=gsk_...
HF_TOKEN=hf_...

> No keys? No problem. Leave `.env` empty and the system runs fully on free mock data.

### Step 2 - Frontend
```bash
cd designmate-ui
npm install
npm run dev
```

Open `http://localhost:3000`



## Tech stack

| Layer | Tool |
|---|---|
| Agent orchestration | LangGraph + FastAPI |
| Vision (room analysis) | Groq Llama 4 Scout 17B |
| Planning (design concepts) | Groq Llama 3.1 8B |
| Budget optimization | Google OR-Tools CP-SAT |
| Product search | Sentence Transformers + numpy |
| Image generation | HuggingFace FLUX.1-schnell |
| Frontend | Next.js + Tailwind + Shadcn/ui |
| 3D floor plan | React Three Fiber + Drei |
| State management | Zustand |
| Real-time logs | Server-Sent Events (SSE) |



## Key observations

- **Real vision intelligence** - Groq Llama 4 Scout correctly identifies room type, dimensions, floor material, lighting direction and wall color from a photo
- **Constraint-aware planning** - OR-Tools CP-SAT enforces hard budget limits per furniture category and logs spatial checks (e.g. "Sofa 96" on 15ft wall. Clearance: 84". PASSED")
- **Transparency layer** - every agent decision streams live to the UI via SSE. The Agent Thought Trace shows exactly why each product was selected or rejected
- **Mock-first architecture** — the entire pipeline runs locally for free without API keys. Real APIs activate with a single `.env` change, no code edits needed
- **Parallel rendering** — all 3 design concepts render concurrently via asyncio.gather, cutting render time by ~3x
- **TC4 limitation** — the $500 budget test case fails because the mock catalog lacks sub-$100 items across all categories. This is a known and expected limitation

## What is done vs remaining

### Done
- Multi-agent pipeline — Vision, Planning, Optimization, Retrieval, Rendering, Dialogue
- Real API integration — Groq vision + planning, HuggingFace FLUX rendering
- Budget optimization with OR-Tools and spatial validation
- Semantic product search with cosine similarity
- Conversational refinement with session memory
- Structured agent logging + SSE streaming to frontend
- Evaluation framework with 5 test cases
- Split-pane dashboard with Agent Thought Trace, 3D Blueprint, Product Manifest
- GitHub monorepo setup

### Remaining / future work
- Firecrawl + Pinecone — replace mock catalog with real scraped Amazon/IKEA products
- Weaviate Docker — replace numpy in-memory search with production vector database
- Session persistence — replace in-memory sessions with PostgreSQL/Supabase
- ImgBB — public image hosting so renders persist after server restart
- SAM compositing — place sourced product images directly into original room photo
- Critic Agent — LLM self-correction loop to improve style coherence scores
- Budget sensitivity graph — show coherence vs budget tradeoff as a sparkline
- Weighted Style DNA — allow blended styles like "70% Modern, 30% Industrial"