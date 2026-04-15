# scraper.py
# Scrapes Article.com product pages using Firecrawl and loads into Pinecone.
# Product URLs sourced via SerpAPI Google search — verified working.
# Run once to populate the vector database:
#   python scraper.py

import os
import re
import json
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

load_dotenv()

PINECONE_API_KEY  = os.getenv("PINECONE_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
INDEX_NAME        = "designmate-products"

# Verified Article.com product URLs per category (sourced via SerpAPI)
PRODUCT_URLS = {
    "sofa": [
        "https://www.article.com/product/25356/ceni-83-sofa-quarry-gray",
        "https://www.article.com/product/22739/timber-90-leather-sofa-charme-tan",
        "https://www.article.com/product/27068/sven-88-tufted-sofa-fir-green",
    ],
    "rug": [
        "https://www.article.com/product/24491/arizona-8-x-10-rug",
        "https://www.article.com/product/23754/hira-8-x-10-rug-natural-ivory",
        "https://www.article.com/product/1834/texa-8-x-10-rug-vanilla-ivory",
    ],
    "floor_lamp": [
        "https://www.article.com/product/13996/moon-floor-lamp-gold",
        "https://www.article.com/product/12482/heron-floor-lamp-black",
        "https://www.article.com/product/17790/arvo-floor-lamp-white",
    ],
    "accent_chair": [
        "https://www.article.com/product/25557/mod-35-lounge-chair-blue-berry",
        "https://www.article.com/product/26648/riley-42-grand-swivel-chair-napa-charcoal",
        "https://www.article.com/product/27028/everse-33-5-velvet-lounge-chair-melange-espresso",
    ],
    "bookshelf": [
        "https://www.article.com/product/25676/fantol-51-5-shelving-unit-wide-natural-oak",
        "https://www.article.com/product/21758/caliper-47-shelving-unit-white-walnut",
        "https://www.article.com/product/29692/krossa-32-5-shelving-unit-tall-walnut",
    ],
}


def _extract_product_data(markdown: str, url: str, category: str) -> dict:
    """Extracts structured product data from an Article.com product page."""

    # Name from h1
    name = ""
    h1 = re.search(r'^#\s+(.+)$', markdown, re.MULTILINE)
    if h1:
        name = h1.group(1).strip()
    name = re.sub(r'\s*-\s*Article.*$', '', name).strip()
    if not name:
        slug = url.rstrip("/").split("/")[-1]
        name = slug.replace("-", " ").title()

    # Price
    price = 0.0
    price_match = re.search(r'\$\s*([\d,]+(?:\.\d{2})?)', markdown)
    if price_match:
        price = float(price_match.group(1).replace(",", ""))
    if price == 0.0:
        price = _default_price(category)

    # Product ID from URL
    product_id = url.rstrip("/").split("/")[-2]

    # Style descriptor
    desc_parts = [name.lower(), category.replace("_", " ")]

    colors = re.findall(
        r'\b(white|black|gray|grey|beige|brown|oak|walnut|blue|green|'
        r'yellow|red|cream|natural|dark|light|metal|fabric|velvet|'
        r'linen|cotton|wool|leather|wood|brass|chrome|gold|silver|'
        r'charcoal|ivory|sand|navy|teal|olive|blush|cognac|tan|ivory)\b',
        markdown.lower()
    )
    if colors:
        desc_parts.extend(list(dict.fromkeys(colors))[:4])

    styles = re.findall(
        r'\b(modern|minimalist|scandinavian|industrial|rustic|contemporary|'
        r'classic|traditional|bohemian|mid-century|farmhouse|coastal|'
        r'transitional|elegant|hygge|cozy|sleek|clean)\b',
        markdown.lower()
    )
    if styles:
        desc_parts.extend(list(dict.fromkeys(styles))[:3])

    return {
        "id":               f"{category}_{product_id}",
        "category":         category,
        "name":             name,
        "price":            price,
        "dimensions":       _default_dimensions(category),
        "style_descriptor": " ".join(desc_parts),
        "purchase_url":     url,
        "in_stock":         True
    }


def _default_price(category: str) -> float:
    defaults = {
        "sofa": 899.0, "rug": 299.0, "floor_lamp": 199.0,
        "accent_chair": 499.0, "bookshelf": 349.0
    }
    return defaults.get(category, 199.0)


def _default_dimensions(category: str) -> dict:
    defaults = {
        "sofa":         {"width": 82, "depth": 37, "height": 33},
        "rug":          {"width": 96, "depth": 120, "height": 0},
        "floor_lamp":   {"width": 11, "depth": 11, "height": 70},
        "accent_chair": {"width": 28, "depth": 30, "height": 32},
        "bookshelf":    {"width": 31, "depth": 15, "height": 79},
    }
    return defaults.get(category, {"width": 30, "depth": 30, "height": 30})


def scrape_products() -> list:
    """Scrapes each Article.com product page for real data."""
    app      = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    products = []

    for category, urls in PRODUCT_URLS.items():
        print(f"\n[Firecrawl] Category: {category}")
        for url in urls:
            try:
                print(f"  -> {url[:80]}...")
                result   = app.scrape_url(url)
                markdown = result.get("markdown", "")
                product  = _extract_product_data(markdown, url, category)
                products.append(product)
                print(f"  OK {product['name']} -- ${product['price']}")
            except Exception as e:
                print(f"  FAIL: {e}")

    print(f"\n[Firecrawl] Scraped {len(products)} products total")
    return products


def load_into_pinecone(products: list):
    """Embeds products and upserts into Pinecone index."""
    pc       = Pinecone(api_key=PINECONE_API_KEY)
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    existing = [i.name for i in pc.list_indexes()]
    if INDEX_NAME not in existing:
        print(f"\n[Pinecone] Creating index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        print(f"[Pinecone] Index created.")
    else:
        print(f"\n[Pinecone] Index '{INDEX_NAME}' already exists.")

    index = pc.Index(INDEX_NAME)

    print(f"[Pinecone] Embedding and upserting {len(products)} products...")
    vectors = []
    for product in products:
        embedding = embedder.encode(
            product["style_descriptor"],
            normalize_embeddings=True
        ).tolist()
        vectors.append({
            "id":     product["id"],
            "values": embedding,
            "metadata": {
                "category":         product["category"],
                "name":             product["name"],
                "price":            product["price"],
                "dimensions":       json.dumps(product["dimensions"]),
                "style_descriptor": product["style_descriptor"],
                "purchase_url":     product["purchase_url"],
                "in_stock":         product["in_stock"],
            }
        })

    batch_size = 50
    for i in range(0, len(vectors), batch_size):
        index.upsert(vectors=vectors[i:i + batch_size])
        print(f"[Pinecone] Upserted batch {i//batch_size + 1}")

    print(f"[Pinecone] Done! {len(vectors)} products indexed.")


if __name__ == "__main__":
    print("=" * 50)
    print("DesignMate -- Article.com Scraper + Pinecone")
    print("=" * 50)

    print("\nStep 1: Scraping Article.com products...")
    products = scrape_products()

    with open("scraped_products.json", "w") as f:
        json.dump(products, f, indent=2)
    print(f"\n[Backup] Saved {len(products)} products to scraped_products.json")

    print("\nStep 2: Loading into Pinecone...")
    load_into_pinecone(products)

    print("\nSetup complete! Pinecone is ready.")