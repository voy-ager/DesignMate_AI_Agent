# scraper.py
# Scrapes Article.com product pages using Firecrawl and loads into Pinecone.
# URLs sourced automatically via SerpAPI (serpScraper.py -> product_urls.json).
# Run once to populate the vector database:
#   python serpScraper.py   ← generates product_urls.json
#   python scraper.py       ← scrapes pages and loads into Pinecone

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
URLS_FILE         = "product_urls.json"


def _load_urls() -> dict:
    if not os.path.exists(URLS_FILE):
        raise FileNotFoundError(f"{URLS_FILE} not found. Run serpScraper.py first.")
    with open(URLS_FILE) as f:
        data = json.load(f)
    # Deduplicate URLs per category
    return {cat: list(dict.fromkeys(urls)) for cat, urls in data.items()}


def _extract_product_data(markdown: str, url: str, category: str) -> dict:
    # Name always from URL slug — avoids picking up marketing copy from h1
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

    # Description
    paragraphs  = re.findall(r'(?<!\#)\n([A-Z][^#\n]{30,300})', markdown)
    description = " ".join(paragraphs[:2]).strip() if paragraphs else ""

    # Dimensions
    dim_match = re.search(
        r'(\d+(?:\.\d+)?)\s*["\']?\s*[Ww].*?(\d+(?:\.\d+)?)\s*["\']?\s*[Dd].*?(\d+(?:\.\d+)?)\s*["\']?\s*[Hh]',
        markdown
    )
    dimensions = _default_dimensions(category)
    if dim_match:
        try:
            dimensions = {
                "width":  float(dim_match.group(1)),
                "depth":  float(dim_match.group(2)),
                "height": float(dim_match.group(3))
            }
        except Exception:
            pass

    # Materials
    materials = list(dict.fromkeys(re.findall(
        r'\b(leather|fabric|velvet|linen|cotton|wool|wood|oak|walnut|'
        r'marble|metal|brass|chrome|gold|silver|rattan|wicker|'
        r'polyester|acrylic|sheepskin|gauze|knit|boucle|eucalyptus)\b',
        markdown.lower()
    )))[:5]

    # Colors
    colors = list(dict.fromkeys(re.findall(
        r'\b(white|black|gray|grey|beige|brown|tan|blue|green|yellow|'
        r'red|cream|natural|dark|light|charcoal|ivory|sand|navy|teal|'
        r'olive|blush|cognac|taupe|peacock|walnut|oak|espresso|rust|'
        r'copper|multi|warm|cool)\b',
        markdown.lower()
    )))[:5]

    # Style keywords
    styles = list(dict.fromkeys(re.findall(
        r'\b(modern|minimalist|scandinavian|industrial|rustic|contemporary|'
        r'classic|traditional|bohemian|mid-century|farmhouse|coastal|'
        r'transitional|elegant|hygge|cozy|sleek|clean|luxurious|modular)\b',
        markdown.lower()
    )))[:5]

    # Rich style descriptor
    desc_parts = [name.lower(), category.replace("_", " ")]
    desc_parts.extend(materials[:3])
    desc_parts.extend(colors[:4])
    desc_parts.extend(styles[:3])
    if description:
        desc_parts.append(description[:100].lower())

    return {
        "id":               f"{category}_{product_id}",
        "category":         category,
        "name":             name,
        "price":            price,
        "dimensions":       dimensions,
        "style_descriptor": " ".join(desc_parts),
        "description":      description,
        "materials":        materials,
        "colors":           colors,
        "style_tags":       styles,
        "purchase_url":     url,
        "in_stock":         True
    }


def _default_price(category: str) -> float:
    defaults = {
        "sofa": 899.0, "rug": 299.0, "floor_lamp": 199.0,
        "accent_chair": 499.0, "bookshelf": 349.0,
        "coffee_table": 449.0, "throw_blanket": 79.0,
        "dining_table": 799.0, "bed_frame": 699.0,
        "side_table": 199.0,
    }
    return defaults.get(category, 199.0)


def _default_dimensions(category: str) -> dict:
    defaults = {
        "sofa":          {"width": 82,  "depth": 37,  "height": 33},
        "rug":           {"width": 96,  "depth": 120, "height": 0},
        "floor_lamp":    {"width": 11,  "depth": 11,  "height": 70},
        "accent_chair":  {"width": 28,  "depth": 30,  "height": 32},
        "bookshelf":     {"width": 31,  "depth": 15,  "height": 79},
        "coffee_table":  {"width": 43,  "depth": 22,  "height": 17},
        "throw_blanket": {"width": 50,  "depth": 60,  "height": 0},
        "dining_table":  {"width": 86,  "depth": 36,  "height": 30},
        "bed_frame":     {"width": 80,  "depth": 85,  "height": 40},
        "side_table":    {"width": 18,  "depth": 18,  "height": 24},
    }
    return defaults.get(category, {"width": 30, "depth": 30, "height": 30})


def scrape_products() -> list:
    app      = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    products = []
    url_map  = _load_urls()

    total = sum(len(v) for v in url_map.values())
    print(f"Scraping {total} products across {len(url_map)} categories...")

    for category, urls in url_map.items():
        print(f"\n[Firecrawl] Category: {category} ({len(urls)} products)")
        for url in urls:
            try:
                print(f"  -> {url.split('/')[-1][:60]}...")
                result   = app.scrape_url(url)
                markdown = result.get("markdown", "")
                if not markdown or len(markdown) < 100:
                    print(f"  SKIP: empty or too short response")
                    continue
                product  = _extract_product_data(markdown, url, category)
                products.append(product)
                print(f"  OK {product['name']} -- ${product['price']}")
            except Exception as e:
                print(f"  FAIL: {e}")

    print(f"\n[Firecrawl] Scraped {len(products)} products total")
    return products


def load_into_pinecone(products: list):
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
                "description":      product.get("description", ""),
                "materials":        json.dumps(product.get("materials", [])),
                "colors":           json.dumps(product.get("colors", [])),
                "style_tags":       json.dumps(product.get("style_tags", [])),
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