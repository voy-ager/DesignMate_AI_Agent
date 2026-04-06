# mock_data.py

MOCK_ROOM_ANALYSIS = {
    "room_type": "living_room",
    "dimensions": {
        "width_ft": 12,
        "length_ft": 14,
        "area_sqft": 168,
        "ceiling_height_ft": 9
    },
    "windows": [
        {"wall": "west", "width_ft": 4, "height_ft": 5, "natural_light": "afternoon"}
    ],
    "doors": [
        {"wall": "north", "width_ft": 3}
    ],
    "lighting": {
        "natural_direction": "west",
        "quality": "warm_afternoon"
    },
    "floor_type": "hardwood",
    "wall_color": "#F5F0E8",
    "existing_features": [],
    "constraints": {
        "max_sofa_width_inches": 84,
        "walkway_clearance_inches": 36
    }
}

# REAL API SWITCH NOTE:
# When using real GPT-4 Vision, MOCK_ROOM_ANALYSIS is replaced by the
# parsed JSON response from the API. The schema must stay identical —
# same keys, same structure — so Planning agent works without any changes.

MOCK_DESIGN_CONCEPTS = [
    {
        "concept_name": "Zen Neutral",
        "style_tags": ["modern", "minimalist"],
        "color_palette": {
            "primary": "#E8E8E0",
            "secondary": "#C4B89A",
            "accent": "#8B7355"
        },
        "budget_total": 0,
        "budget_allocation": {
            "seating": 0.40,
            "tables": 0.25,
            "textiles": 0.20,
            "accessories": 0.15
        },
        "required_items": [
            {
                "category": "sofa",
                "max_width_inches": 84,
                "style_query": "modern gray minimalist sofa"
            },
            {
                "category": "coffee_table",
                "max_width_inches": 48,
                "style_query": "walnut rectangular coffee table minimalist"
            },
            {
                "category": "rug",
                "max_width_inches": 96,
                "style_query": "cream wool area rug minimalist"
            },
            {
                "category": "floor_lamp",
                "max_width_inches": None,
                "style_query": "modern arc floor lamp brass"
            }
        ]
    },
    {
        "concept_name": "Cozy Scandinavian",
        "style_tags": ["scandinavian", "warm", "hygge"],
        "color_palette": {
            "primary": "#F0EAD6",
            "secondary": "#D4C5A9",
            "accent": "#7B6B52"
        },
        "budget_total": 0,
        "budget_allocation": {
            "seating": 0.38,
            "tables": 0.22,
            "textiles": 0.28,
            "accessories": 0.12
        },
        "required_items": [
            {
                "category": "sofa",
                "max_width_inches": 80,
                "style_query": "scandinavian cream fabric sofa wooden legs"
            },
            {
                "category": "coffee_table",
                "max_width_inches": 44,
                "style_query": "light oak round coffee table scandinavian"
            },
            {
                "category": "rug",
                "max_width_inches": 96,
                "style_query": "warm beige textured area rug"
            },
            {
                "category": "throw_blanket",
                "max_width_inches": None,
                "style_query": "chunky knit throw blanket cream"
            }
        ]
    },
    {
        "concept_name": "Bold Contemporary",
        "style_tags": ["contemporary", "bold", "statement"],
        "color_palette": {
            "primary": "#2C2C2A",
            "secondary": "#4A4A45",
            "accent": "#C17F3B"
        },
        "budget_total": 0,
        "budget_allocation": {
            "seating": 0.45,
            "tables": 0.25,
            "textiles": 0.15,
            "accessories": 0.15
        },
        "required_items": [
            {
                "category": "sofa",
                "max_width_inches": 84,
                "style_query": "dark charcoal sectional sofa contemporary"
            },
            {
                "category": "coffee_table",
                "max_width_inches": 50,
                "style_query": "black metal glass coffee table modern"
            },
            {
                "category": "rug",
                "max_width_inches": 96,
                "style_query": "geometric pattern area rug dark tones"
            },
            {
                "category": "accent_chair",
                "max_width_inches": None,
                "style_query": "mustard yellow accent chair contemporary"
            }
        ]
    }
]