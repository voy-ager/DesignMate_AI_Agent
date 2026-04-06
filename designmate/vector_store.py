# vector_store.py
# Pure Python in-memory vector search using numpy cosine similarity.
# Replaces Weaviate embedded mode which does not support Windows.
# Interface is identical — search_products() signature unchanged —
# so retrieval.py, optimization.py, graph.py, api.py need no changes.

# REAL API SWITCH NOTE (Weaviate Docker):
# When ready to switch to Docker-based Weaviate:
# 1. Install Docker Desktop from docker.com
# 2. Run: docker run -p 8080:8080 semitechnologies/weaviate:latest
# 3. Replace this entire file with the Weaviate client version
#    (only change: connect_to_local() instead of connect_to_embedded())
# 4. No other files need changes — same search_products() interface.

import numpy as np
from sentence_transformers import SentenceTransformer
from mock_catalog import MOCK_CATALOG

print("[VectorStore] Loading sentence transformer model...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("[VectorStore] Model loaded.")

# In-memory store: list of dicts with product metadata + embedding vector
_product_store: list = []
_seeded: bool = False


def _seed_catalog():
    global _product_store, _seeded
    if _seeded:
        return

    print("[VectorStore] Seeding mock catalog into memory...")
    _product_store = []

    for product in MOCK_CATALOG:
        embedding = embedder.encode(
            product["style_descriptor"],
            normalize_embeddings=True   # unit vectors — cosine sim = dot product
        )
        _product_store.append({
            "product_id":       product["id"],
            "category":         product["category"],
            "name":             product["name"],
            "price":            product["price"],
            "dimensions":       product["dimensions"],
            "style_descriptor": product["style_descriptor"],
            "purchase_url":     product["purchase_url"],
            "in_stock":         product["in_stock"],
            "embedding":        embedding   # numpy array, stays here, never in AppState
        })

    _seeded = True
    print(f"[VectorStore] Seeded {len(_product_store)} products.")


def search_products(query: str, category: str, limit: int = 3) -> list:
    """
    Search in-memory catalog for products matching query within a category.
    Uses cosine similarity between query embedding and product embeddings.
    Returns top-N results sorted by similarity score descending.
    Pitfall 2: embedding vectors are stripped before returning — only
               metadata goes back to the caller and into AppState.
    """
    _seed_catalog()

    # Filter by category first
    candidates = [p for p in _product_store if p["category"] == category]

    if not candidates:
        return []

    # Encode query with same normalization — cosine sim = dot product
    query_vector = embedder.encode(query, normalize_embeddings=True)

    # Compute cosine similarity for all candidates in one matrix op
    candidate_embeddings = np.stack([c["embedding"] for c in candidates])
    similarities = candidate_embeddings @ query_vector   # dot product = cosine sim

    # Sort by similarity descending and take top N
    top_indices = np.argsort(similarities)[::-1][:limit]

    results = []
    for idx in top_indices:
        product = candidates[idx]
        score = float(similarities[idx])
        results.append({
            "product_id":       product["product_id"],
            "category":         product["category"],
            "name":             product["name"],
            "price":            product["price"],
            "dimensions":       product["dimensions"],
            "style_descriptor": product["style_descriptor"],
            "purchase_url":     product["purchase_url"],
            "in_stock":         product["in_stock"],
            "similarity_score": round(score, 4)
            # embedding intentionally excluded — pitfall 2
        })

    return results