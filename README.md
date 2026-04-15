# DesignMate AI
An autonomous multi-agent system for intelligent interior design with real-time product integration and budget optimization.

## Structure
- `designmate/` — FastAPI + LangGraph multi-agent pipeline (Python)
- `designmate-ui/` — Next.js + React Three Fiber dashboard (TypeScript)

## What it does
1. You upload a photo of a room and set a budget
2. The AI analyzes the room, fetches the real product catalog from Pinecone, and generates 3 design concepts using only real available products
3. Products are sourced directly by ID — no hallucinated items, every recommendation links to a real Article.com product page
4. Photorealistic room renders are generated for each concept via HuggingFace FLUX
5. You can refine designs conversationally — "make it more rustic" or "reduce the budget"
6. Every agent decision is visible in real-time via the Agent Thought Trace panel
7. A full metrics dashboard tracks reasoning quality, planning diversity, retrieval precision, tool call success, memory, actions and pipeline health

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
SERPAPI_KEY=...
```
No keys? No problem. Leave `.env` empty and the system runs fully on free mock data.

### Step 2 — Populate Product Catalog (optional but recommended)
```bash
cd designmate
venv\Scripts\activate

# Step 2a: Discover product URLs via SerpAPI
python serpScraper.py

# Step 2b: Scrape product pages and load into Pinecone
python scraper.py
```

This scrapes 10 products across 10 categories (100 total) from Article.com and loads them into Pinecone. The planning agent will then design concepts using only these real products.

### Step 3 — Frontend
```bash
cd designmate-ui
npm install
npm run dev
```
Open `http://localhost:3000`

---

## Setting Up Firecrawl + Pinecone + SerpAPI

### 1. Create accounts
- **SerpAPI** — sign up at [serpapi.com](https://serpapi.com) (free tier: 100 searches/month)
- **Firecrawl** — sign up at [firecrawl.dev](https://firecrawl.dev) (free tier: 500 credits)
- **Pinecone** — sign up at [pinecone.io](https://pinecone.io) (free tier: 1 serverless index)

### 2. Add API keys to `.env`
```
SERPAPI_KEY=...
PINECONE_API_KEY=pcsk_...
FIRECRAWL_API_KEY=fc-...
```

### 3. Discover product URLs
```bash
python serpScraper.py
```
Uses SerpAPI to search Google for real Article.com product URLs across all 10 categories. Saves results to `product_urls.json`.

### 4. Scrape and load into Pinecone
```bash
python scraper.py
```
Firecrawl scrapes each product page for name, price, materials, colors, style tags and description. Embeds with Sentence Transformers and upserts into Pinecone.

**Credit usage:** ~100 Firecrawl credits per full run (1 per product page)

### 5. Verify in Pinecone dashboard
Go to [app.pinecone.io](https://app.pinecone.io) → your index → **Browse** to confirm products are loaded.

### How the catalog pipeline works
```
serpScraper.py searches Google for Article.com product URLs
        ↓
Saves 10 URLs × 10 categories to product_urls.json
        ↓
scraper.py reads product_urls.json
        ↓
Firecrawl scrapes each product page
        ↓
Extracts: name, price, materials, colors, style tags, description
        ↓
Embeds style_descriptor with Sentence Transformers (all-MiniLM-L6-v2)
        ↓
Upserts 100 product vectors into Pinecone index
        ↓
planning_agent fetches full catalog from Pinecone at runtime
        ↓
Groq LLM selects specific products by ID for each design concept
        ↓
retrieval_agent does direct product lookup (no semantic guessing)
```

### Adding more products
To expand the catalog, edit `CATEGORIES` in `serpScraper.py` and re-run both scripts. Article.com works reliably — other major retailers (IKEA, Amazon) block automated scraping.

---

## Tech Stack
| Layer | Tool |
|---|---|
| Agent orchestration | LangGraph + FastAPI |
| Vision (room analysis) | Groq Llama 4 Scout 17B |
| Planning (design concepts) | Groq Llama 3.1 8B + Pinecone catalog |
| Budget optimization | Google OR-Tools CP-SAT |
| Product URL discovery | SerpAPI (Google Search) |
| Product scraping | Firecrawl (Article.com) |
| Vector database | Pinecone serverless |
| Semantic embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Image generation | HuggingFace FLUX.1-schnell |
| Frontend | Next.js + Tailwind + Shadcn/ui |
| 3D floor plan | React Three Fiber + Drei |
| State management | Zustand |
| Real-time logs | Server-Sent Events (SSE) |
| Metrics dashboard | Custom 11-section agentic metrics panel |

---

## Key Observations
- **Catalog-grounded design** — the planning agent fetches the full Pinecone product catalog and passes it to Groq as context. The LLM selects specific products by ID — no hallucinated items, every recommendation is a real purchasable product
- **Real vision intelligence** — Groq Llama 4 Scout correctly identifies room type, dimensions, floor material, lighting direction and wall color from a photo
- **Constraint-aware planning** — OR-Tools CP-SAT enforces hard budget limits per furniture category and logs spatial checks (e.g. "Sofa 96" on 15ft wall. Clearance: 84". PASSED")
- **Transparency layer** — every agent decision streams live to the UI via SSE. The Agent Thought Trace shows exactly why each product was selected or rejected
- **Comprehensive metrics** — 11-section agentic metrics dashboard covering reasoning, planning, budget, style coherence, retrieval precision, tool calls, memory, actions, concept diversity, constraint satisfaction and pipeline health
- **Mock-first architecture** — the entire pipeline runs locally for free without API keys. Real APIs activate with a single `.env` change, no code edits needed
- **Parallel rendering** — all 3 design concepts render concurrently via asyncio.gather, cutting render time by ~3x
- **SerpAPI + Firecrawl pipeline** — SerpAPI discovers real product URLs via Google search, Firecrawl scrapes rich product data, Pinecone stores and serves vectors at query time
- **TC4 limitation** — the $500 budget test case may fail because the catalog lacks sufficient sub-$100 items. This is a known limitation

---

## What is Done vs Remaining

### Done
- Multi-agent pipeline — Vision, Planning, Optimization, Retrieval, Rendering, Dialogue
- Real API integration — Groq vision + planning, HuggingFace FLUX rendering
- **Catalog-grounded planning** — LLM designs using only real Pinecone products selected by ID
- Budget optimization with OR-Tools and spatial validation
- Pinecone vector database for production product storage and search
- SerpAPI + Firecrawl automated product discovery and scraping pipeline
- 100 real Article.com products across 10 categories
- Conversational refinement with session memory
- Structured agent logging + SSE streaming to frontend
- **11-section agentic metrics dashboard** — reasoning, planning, budget, coherence, retrieval precision, tool calls, memory, actions, diversity, constraints, pipeline health
- Evaluation framework with 5 test cases
- Split-pane dashboard with Agent Thought Trace, Metrics Dashboard, 3D Blueprint, Product Manifest
- GitHub monorepo setup

### Remaining / Future Work
- **Multi-retailer scraping** — extend to World Market, Wayfair and other scrapable retailers
- **Weaviate Docker** — replace Pinecone with self-hosted Weaviate for fully local vector database
- **Session persistence** — replace in-memory sessions with PostgreSQL/Supabase
- **ImgBB** — public image hosting so renders persist after server restart
- **SAM compositing** — place sourced product images directly into original room photo
- **Critic Agent** — LLM self-correction loop to improve style coherence scores
- **Budget sensitivity graph** — show coherence vs budget tradeoff as a sparkline
- **Weighted Style DNA** — allow blended styles like "70% Modern, 30% Industrial"
- **ControlNet rendering** — use depth maps from original photo to preserve room structure in generated images
- **Larger catalog** — expand beyond 100 products for more diverse design concepts++