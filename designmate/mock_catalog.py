# mock_catalog.py
# 20+ realistic furniture products covering all categories used in design concepts.
# Each product has a style_descriptor field — this is what gets embedded into
# Weaviate as a vector. The Retrieval agent searches against this field.

# REAL API SWITCH NOTE:
# In production, this catalog gets replaced by live Amazon/IKEA API results.
# The schema must stay identical — same keys — so Retrieval agent works unchanged.

MOCK_CATALOG = [
    # ── SOFAS ─────────────────────────────────────────────────────────────────
    {
        "id": "sofa_001",
        "category": "sofa",
        "name": "Article Sven Charcoal Sofa",
        "price": 799.00,
        "dimensions": {"width": 82, "depth": 38, "height": 33},
        "style_descriptor": "low-profile charcoal fabric sofa solid wood legs modern minimalist",
        "purchase_url": "https://example.com/products/sofa_001",
        "in_stock": True
    },
    {
        "id": "sofa_002",
        "category": "sofa",
        "name": "IKEA KIVIK Grey Sofa",
        "price": 649.00,
        "dimensions": {"width": 83, "depth": 37, "height": 32},
        "style_descriptor": "gray fabric sofa deep seat casual modern scandinavian",
        "purchase_url": "https://example.com/products/sofa_002",
        "in_stock": True
    },
    {
        "id": "sofa_003",
        "category": "sofa",
        "name": "West Elm Cream Slope Sofa",
        "price": 1299.00,
        "dimensions": {"width": 79, "depth": 36, "height": 34},
        "style_descriptor": "cream fabric sofa wooden legs scandinavian hygge warm neutral",
        "purchase_url": "https://example.com/products/sofa_003",
        "in_stock": True
    },
    {
        "id": "sofa_004",
        "category": "sofa",
        "name": "CB2 Dark Charcoal Sectional",
        "price": 1899.00,
        "dimensions": {"width": 84, "depth": 40, "height": 32},
        "style_descriptor": "dark charcoal sectional sofa contemporary bold statement piece",
        "purchase_url": "https://example.com/products/sofa_004",
        "in_stock": True
    },
    {
        "id": "sofa_005",
        "category": "sofa",
        "name": "Burrow Nomad Olive Sofa",
        "price": 950.00,
        "dimensions": {"width": 80, "depth": 37, "height": 33},
        "style_descriptor": "olive green modular sofa mid-century modern fabric",
        "purchase_url": "https://example.com/products/sofa_005",
        "in_stock": False
    },

    # ── COFFEE TABLES ─────────────────────────────────────────────────────────
    {
        "id": "ct_001",
        "category": "coffee_table",
        "name": "Article Faun Walnut Coffee Table",
        "price": 349.00,
        "dimensions": {"width": 47, "depth": 24, "height": 16},
        "style_descriptor": "walnut rectangular coffee table minimalist solid wood modern",
        "purchase_url": "https://example.com/products/ct_001",
        "in_stock": True
    },
    {
        "id": "ct_002",
        "category": "coffee_table",
        "name": "IKEA LACK White Coffee Table",
        "price": 59.00,
        "dimensions": {"width": 46, "depth": 22, "height": 17},
        "style_descriptor": "white minimalist coffee table simple clean modern",
        "purchase_url": "https://example.com/products/ct_002",
        "in_stock": True
    },
    {
        "id": "ct_003",
        "category": "coffee_table",
        "name": "West Elm Oak Round Table",
        "price": 449.00,
        "dimensions": {"width": 42, "depth": 42, "height": 16},
        "style_descriptor": "light oak round coffee table scandinavian natural wood warm",
        "purchase_url": "https://example.com/products/ct_003",
        "in_stock": True
    },
    {
        "id": "ct_004",
        "category": "coffee_table",
        "name": "CB2 Blox Black Metal Table",
        "price": 599.00,
        "dimensions": {"width": 48, "depth": 24, "height": 16},
        "style_descriptor": "black metal glass coffee table modern contemporary bold",
        "purchase_url": "https://example.com/products/ct_004",
        "in_stock": True
    },

    # ── RUGS ──────────────────────────────────────────────────────────────────
    {
        "id": "rug_001",
        "category": "rug",
        "name": "Rugs USA Cream Wool Rug 8x10",
        "price": 289.00,
        "dimensions": {"width": 96, "depth": 120, "height": 0},
        "style_descriptor": "cream wool area rug minimalist neutral soft texture",
        "purchase_url": "https://example.com/products/rug_001",
        "in_stock": True
    },
    {
        "id": "rug_002",
        "category": "rug",
        "name": "Wayfair Beige Textured Rug 8x10",
        "price": 199.00,
        "dimensions": {"width": 96, "depth": 120, "height": 0},
        "style_descriptor": "warm beige textured area rug scandinavian hygge natural",
        "purchase_url": "https://example.com/products/rug_002",
        "in_stock": True
    },
    {
        "id": "rug_003",
        "category": "rug",
        "name": "Loloi Geometric Dark Rug 8x10",
        "price": 399.00,
        "dimensions": {"width": 96, "depth": 120, "height": 0},
        "style_descriptor": "geometric pattern area rug dark tones contemporary bold",
        "purchase_url": "https://example.com/products/rug_003",
        "in_stock": True
    },

    # ── FLOOR LAMPS ───────────────────────────────────────────────────────────
    {
        "id": "lamp_001",
        "category": "floor_lamp",
        "name": "CB2 Arched Brass Floor Lamp",
        "price": 249.00,
        "dimensions": {"width": 12, "depth": 12, "height": 72},
        "style_descriptor": "modern arc floor lamp brass minimalist elegant",
        "purchase_url": "https://example.com/products/lamp_001",
        "in_stock": True
    },
    {
        "id": "lamp_002",
        "category": "floor_lamp",
        "name": "IKEA HEKTAR Floor Lamp",
        "price": 69.00,
        "dimensions": {"width": 10, "depth": 10, "height": 68},
        "style_descriptor": "industrial floor lamp dark grey metal adjustable",
        "purchase_url": "https://example.com/products/lamp_002",
        "in_stock": True
    },

    # ── ACCENT CHAIRS ─────────────────────────────────────────────────────────
    {
        "id": "chair_001",
        "category": "accent_chair",
        "name": "Article Ceets Mustard Chair",
        "price": 449.00,
        "dimensions": {"width": 28, "depth": 30, "height": 32},
        "style_descriptor": "mustard yellow accent chair contemporary bold statement",
        "purchase_url": "https://example.com/products/chair_001",
        "in_stock": True
    },
    {
        "id": "chair_002",
        "category": "accent_chair",
        "name": "West Elm Slope Chair Cream",
        "price": 599.00,
        "dimensions": {"width": 27, "depth": 29, "height": 33},
        "style_descriptor": "cream fabric accent chair scandinavian wood legs warm",
        "purchase_url": "https://example.com/products/chair_002",
        "in_stock": True
    },

    # ── THROW BLANKETS ────────────────────────────────────────────────────────
    {
        "id": "blanket_001",
        "category": "throw_blanket",
        "name": "Chunky Knit Cream Throw",
        "price": 49.00,
        "dimensions": {"width": 50, "depth": 60, "height": 0},
        "style_descriptor": "chunky knit throw blanket cream cozy hygge scandinavian",
        "purchase_url": "https://example.com/products/blanket_001",
        "in_stock": True
    },
    {
        "id": "blanket_002",
        "category": "throw_blanket",
        "name": "Wool Herringbone Grey Throw",
        "price": 79.00,
        "dimensions": {"width": 50, "depth": 60, "height": 0},
        "style_descriptor": "wool herringbone throw blanket grey warm minimalist",
        "purchase_url": "https://example.com/products/blanket_002",
        "in_stock": True
    }
]