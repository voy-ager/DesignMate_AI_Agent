# DesignMate AI
An autonomous multi-agent system for intelligent interior design with real-time product integration and budget optimization.

## Structure
- `designmate/` — FastAPI + LangGraph multi-agent pipeline (Python)
- `designmate-ui/` — Next.js + React Three Fiber dashboard (TypeScript)

## What it does
1. You upload a photo of a room and set a budget
2. The AI analyzes the room, generates 3 design concepts, sources real furniture products, and renders photorealistic images
3. You can refine designs conversationally — "make it more rustic" or "reduce the budget"
4. Every agent decision is visible in real-time via the Agent Thought Trace panel

## How to run

### Step 1 — Backend
```bash
cd designmate
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install sse-starlette ortools sentence-transformers python-multipart pinecone firecrawl-py==1.0.0
python -m uvicorn api:app --port 8000
```

Create a `.env` file inside `designmate/` with your API keys:
```
GROQ_API_KEY=gsk_...
HF_TOKEN=hf_...
PINECONE_API_KEY=pcsk_...
FIRECRAWL_API_KEY=fc-...
```
No keys? No problem. Leave `.env` empty and the system runs fully on free mock data.

### Step 2 — Populate Product Catalog (optional)
```bash
cd designmate
python scraper.py
```
Scrapes Article.com for real furniture products and loads them into Pinecone. Requires `PINECONE_API_KEY` and `FIRECRAWL_API_KEY` in `.env`.

### Step 3 — Frontend
```bash
cd designmate-ui
npm install
npm run dev
```
Open `http://localhost:3000`

## Setting Up Firecrawl + Pinecone

### 1. Create accounts
- **Firecrawl** — sign up at [firecrawl.dev](https://firecrawl.dev) (free tier: 500 credits)
- **Pinecone** — sign up at [pinecone.io](https://pinecone.io) (free tier: 1 serverless index)

### 2. Add API keys to `.env`
```
PINECONE_API_KEY=pcsk_...
FIRECRAWL_API_KEY=fc-...
```

### 3. Run the scraper
```bash
cd designmate
venv\Scripts\activate
python scraper.py
```

This will:
1. Scrape Article.com category pages automatically (no manual URLs needed)
2. Extract product URLs from each category page
3. Scrape each product page for name, price, and style details
4. Embed products using Sentence Transformers
5. Load all vectors into your Pinecone index

**Credit usage:** ~20 Firecrawl credits per run (5 category pages + 15 product pages)

### 4. Verify in Pinecone dashboard
Go to [app.pinecone.io](https://app.pinecone.io) → your index → **Browse** to confirm products are loaded.

### How it works
```
Article.com category page (e.g. /category/sofas)
        ↓  Firecrawl scrapes page
Extract product URLs automatically via regex
        ↓
Scrape each product page (name, price, colors, style)
        ↓
Embed style descriptor with Sentence Transformers
        ↓
Upsert vectors into Pinecone index
        ↓
vector_store.py uses Pinecone for semantic search
(falls back to numpy mock catalog if no API key)
```

### Adding more products
To scrape more retailers, add their category page URLs to `CATEGORY_PAGES` in `scraper.py`. World Market is also supported — other major retailers (IKEA, Amazon) block automated scraping.

## Tech Stack
| Layer | Tool |
|---|---|
| Agent orchestration | LangGraph + FastAPI |
| Vision (room analysis) | Groq Llama 4 Scout 17B |
| Planning (design concepts) | Groq Llama 3.1 8B |
| Budget optimization | Google OR-Tools CP-SAT |
| Product search | Pinecone + Sentence Transformers |
| Product scraping | Firecrawl (Article.com) |
| Image generation | HuggingFace FLUX.1-schnell |
| Frontend | Next.js + Tailwind + Shadcn/ui |
| 3D floor plan | React Three Fiber + Drei |
| State management | Zustand |
| Real-time logs | Server-Sent Events (SSE) |

## Key Observations
- **Real vision intelligence** — Groq Llama 4 Scout correctly identifies room type, dimensions, floor material, lighting direction and wall color from a photo
- **Constraint-aware planning** — OR-Tools CP-SAT enforces hard budget limits per furniture category and logs spatial checks (e.g. "Sofa 96" on 15ft wall. Clearance: 84". PASSED")
- **Transparency layer** — every agent decision streams live to the UI via SSE. The Agent Thought Trace shows exactly why each product was selected or rejected
- **Mock-first architecture** — the entire pipeline runs locally for free without API keys. Real APIs activate with a single `.env` change, no code edits needed
- **Parallel rendering** — all 3 design concepts render concurrently via asyncio.gather, cutting render time by ~3x
- **Real product catalog** — Firecrawl scrapes Article.com automatically, extracts product URLs from category pages, and loads enriched data into Pinecone for semantic search
- **TC4 limitation** — the $500 budget test case fails because the mock catalog lacks sub-$100 items across all categories. This is a known and expected limitation

## What is Done vs Remaining

### Done
- Multi-agent pipeline — Vision, Planning, Optimization, Retrieval, Rendering, Dialogue
- Real API integration — Groq vision + planning, HuggingFace FLUX rendering
- Budget optimization with OR-Tools and spatial validation
- Pinecone vector database for production semantic product search
- Firecrawl scraper — automatically scrapes Article.com category pages and loads into Pinecone
- Conversational refinement with session memory
- Structured agent logging + SSE streaming to frontend
- Evaluation framework with 5 test cases
- Split-pane dashboard with Agent Thought Trace, 3D Blueprint, Product Manifest
- GitHub monorepo setup

### Remaining / Future Work
- **Multi-retailer scraping** — extend Firecrawl scraper to World Market, Wayfair and other scrapable retailers (IKEA and Amazon block bots)
- **Weaviate Docker** — replace Pinecone with self-hosted Weaviate for fully local production vector database
- **Session persistence** — replace in-memory sessions with PostgreSQL/Supabase
- **ImgBB** — public image hosting so renders persist after server restart
- **SAM compositing** — place sourced product images directly into original room photo using Segment Anything Model
- **Critic Agent** — LLM self-correction loop to improve style coherence scores
- **Budget sensitivity graph** — show coherence vs budget tradeoff as a sparkline
- **Weighted Style DNA** — allow blended styles like "70% Modern, 30% Industrial"
- **ControlNet rendering** — use depth maps from original photo to preserve room structure (walls, windows, doors) in generated images