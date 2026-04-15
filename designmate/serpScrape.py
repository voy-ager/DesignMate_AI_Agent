# serpScraper.py
# Uses SerpAPI to find real Article.com product URLs per category.
# Saves results to product_urls.json which scraper.py reads from.
#
# Run this first, then run scraper.py:
#   python serpScraper.py
#   python scraper.py

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Categories and their search queries
# Add more categories or change queries as needed
CATEGORIES = {
    "sofa":          "site:article.com/product sofa",
    "rug":           "site:article.com/product rug",
    "floor_lamp":    "site:article.com/product floor lamp",
    "accent_chair":  "site:article.com/product chair",
    "bookshelf":     "site:article.com/product shelving bookshelf",
    "coffee_table":  "site:article.com/product coffee table",
    "throw_blanket": "site:article.com/product throw blanket",
    "dining_table":  "site:article.com/product dining table",
    "bed_frame":     "site:article.com/product bed frame",
    "side_table":    "site:article.com/product side table",
}

PRODUCTS_PER_CATEGORY = 10
OUTPUT_FILE           = "product_urls.json"


def find_product_urls(category: str, query: str, limit: int) -> list:
    """Search Google via SerpAPI for Article.com product URLs."""
    resp = requests.get("https://serpapi.com/search", params={
        "engine":  "google",
        "q":       query,
        "api_key": SERPAPI_KEY,
        "num":     limit,
    })

    if resp.status_code != 200:
        print(f"  SerpAPI error {resp.status_code}: {resp.text[:100]}")
        return []

    results = resp.json().get("organic_results", [])
    urls = []
    for r in results:
        link = r.get("link", "")
        if "article.com/product/" in link:
            clean = link.split("?")[0]  # strip tracking params
            urls.append(clean)

    return urls[:limit]


if __name__ == "__main__":
    if not SERPAPI_KEY:
        print("ERROR: SERPAPI_KEY not found in .env")
        exit(1)

    print("=" * 50)
    print("DesignMate -- SerpAPI Product URL Discovery")
    print("=" * 50)

    all_urls = {}
    total    = 0

    for category, query in CATEGORIES.items():
        print(f"\n[SerpAPI] Searching: {category}")
        urls = find_product_urls(category, query, PRODUCTS_PER_CATEGORY)
        all_urls[category] = urls
        total += len(urls)
        print(f"  Found {len(urls)} URLs")
        for u in urls:
            print(f"  {u}")

    # Save to file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_urls, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Done! Found {total} URLs across {len(all_urls)} categories")
    print(f"Saved to {OUTPUT_FILE}")
    print(f"\nNext step: run scraper.py to scrape and load into Pinecone")
    print(f"  python scraper.py")