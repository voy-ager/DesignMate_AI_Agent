# vector_store.py
# Production vector search using Pinecone.
# Replaces numpy in-memory search with Pinecone serverless index.
# Interface is identical — search_products() signature unchanged —
# so retrieval.py, optimization.py, graph.py, api.py need no changes.
#
# FALLBACK: if PINECONE_API_KEY is not set, falls back to numpy mock catalog.

import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME       = "designmate-products"

print("[VectorStore] Loading sentence transformer model...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("[VectorStore] Model loaded.")

# Pinecone index (lazy initialized)
_pinecone_index = None
_use_pinecone   = bool(PINECONE_API_KEY)


def _get_pinecone_index():
    global _pinecone_index
    if _pinecone_index is None:
        from pinecone import Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        _pinecone_index = pc.Index(INDEX_NAME)
        print(f"[VectorStore] Connected to Pinecone index '{INDEX_NAME}'")
    return _pinecone_index


# ── Fallback: numpy in-memory (mock catalog) ─────────────────────────────────
_product_store: list = []
_seeded: bool = False


def _seed_mock_catalog():
    global _product_store, _seeded
    if _seeded:
        return
    from mock_catalog import MOCK_CATALOG
    print("[VectorStore] Seeding mock catalog into memory...")
    _product_store = []
    for product in MOCK_CATALOG:
        embedding = embedder.encode(
            product["style_descriptor"],
            normalize_embeddings=True
        )
        _product_store.append({**product, "embedding": embedding})
    _seeded = True
    print(f"[VectorStore] Seeded {len(_product_store)} products.")


def _search_numpy(query: str, category: str, limit: int) -> list:
    _seed_mock_catalog()
    candidates = [p for p in _product_store if p["category"] == category]
    if not candidates:
        return []
    query_vector = embedder.encode(query, normalize_embeddings=True)
    candidate_embeddings = np.stack([c["embedding"] for c in candidates])
    similarities = candidate_embeddings @ query_vector
    top_indices  = np.argsort(similarities)[::-1][:limit]
    results = []
    for idx in top_indices:
        p = candidates[idx]
        results.append({
            "product_id":       p["id"],
            "category":         p["category"],
            "name":             p["name"],
            "price":            p["price"],
            "dimensions":       p["dimensions"],
            "style_descriptor": p["style_descriptor"],
            "purchase_url":     p["purchase_url"],
            "in_stock":         p["in_stock"],
            "similarity_score": round(float(similarities[idx]), 4)
        })
    return results


# ── Pinecone search ───────────────────────────────────────────────────────────
def _search_pinecone(query: str, category: str, limit: int) -> list:
    index        = _get_pinecone_index()
    query_vector = embedder.encode(query, normalize_embeddings=True).tolist()

    response = index.query(
        vector=query_vector,
        top_k=limit * 3,   # fetch more to filter by category
        include_metadata=True,
        filter={"category": {"$eq": category}}
    )

    results = []
    for match in response.matches[:limit]:
        meta = match.metadata
        # dimensions stored as JSON string in Pinecone metadata
        dims = meta.get("dimensions", "{}")
        if isinstance(dims, str):
            try:
                dims = json.loads(dims)
            except Exception:
                dims = {"width": 30, "depth": 30, "height": 30}

        results.append({
            "product_id":       match.id,
            "category":         meta.get("category", category),
            "name":             meta.get("name", "Unknown Product"),
            "price":            float(meta.get("price", 0)),
            "dimensions":       dims,
            "style_descriptor": meta.get("style_descriptor", ""),
            "purchase_url":     meta.get("purchase_url", ""),
            "in_stock":         bool(meta.get("in_stock", True)),
            "similarity_score": round(float(match.score), 4)
        })
    return results


# ── Direct product lookup by ID ───────────────────────────────────────────────
def get_product_by_id(product_id: str) -> dict | None:
    """
    Fetches a single product by its Pinecone vector ID.
    Used by retrieval agent in catalog-grounded mode.
    """
    if _use_pinecone:
        try:
            index  = _get_pinecone_index()
            result = index.fetch(ids=[product_id])
            vectors = result.vectors
            if not vectors or product_id not in vectors:
                return None
            meta = vectors[product_id].metadata
            dims = meta.get("dimensions", "{}")
            if isinstance(dims, str):
                try:
                    dims = json.loads(dims)
                except Exception:
                    dims = {}
            return {
                "product_id":       product_id,
                "category":         meta.get("category", ""),
                "name":             meta.get("name", ""),
                "price":            float(meta.get("price", 0)),
                "dimensions":       dims,
                "style_descriptor": meta.get("style_descriptor", ""),
                "description":      meta.get("description", ""),
                "purchase_url":     meta.get("purchase_url", ""),
                "in_stock":         bool(meta.get("in_stock", True)),
                "similarity_score": 1.0,
            }
        except Exception as e:
            print(f"[VectorStore] get_product_by_id error: {e}")
            return None

    # Fallback: search mock catalog by id
    _seed_mock_catalog()
    for p in _product_store:
        if p.get("id") == product_id:
            return {
                "product_id":       p["id"],
                "category":         p["category"],
                "name":             p["name"],
                "price":            p["price"],
                "dimensions":       p["dimensions"],
                "style_descriptor": p["style_descriptor"],
                "purchase_url":     p["purchase_url"],
                "in_stock":         p["in_stock"],
                "similarity_score": 1.0,
            }
    return None


# ── Public interface ───────────────────────────────────────────────────────────
def search_products(query: str, category: str, limit: int = 3) -> list:
    """
    Search for products matching query within a category.
    Uses Pinecone if PINECONE_API_KEY is set, otherwise numpy mock catalog.
    Returns top-N results sorted by similarity score descending.
    """
    if _use_pinecone:
        try:
            results = _search_pinecone(query, category, limit)
            if results:
                return results
            print(f"[VectorStore] Pinecone returned no results for '{category}', falling back to mock")
        except Exception as e:
            print(f"[VectorStore] Pinecone error: {e}, falling back to mock")

    return _search_numpy(query, category, limit)