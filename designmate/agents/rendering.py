# agents/rendering.py
import os
import asyncio
import base64
import io
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from state import AppState
from logger import log_event, log_stage_start, log_stage_end

PLACEHOLDER_IMAGE = "https://placehold.co/1024x1024/E8E8E0/8B7355?text=DesignMate+Mock+Render"

def _use_real_api() -> bool:
    return bool(os.getenv("HF_TOKEN", "").strip())


def _build_prompt(concept: dict, room_analysis: dict):
    style_tags  = ", ".join(concept.get("style_tags", ["modern"]))
    palette     = concept.get("color_palette", {})
    primary     = palette.get("primary", "#FFFFFF")
    accent      = palette.get("accent", "#000000")
    room_type   = room_analysis.get("room_type", "living room").replace("_", " ")
    floor_type  = room_analysis.get("floor_type", "hardwood")
    lighting    = room_analysis.get("lighting", {}).get("quality", "natural light")
    wall_color  = room_analysis.get("wall_color", "#FFFFFF")
    width_ft    = room_analysis.get("dimensions", {}).get("width_ft", 12)
    length_ft   = room_analysis.get("dimensions", {}).get("length_ft", 14)

    furniture_parts = []
    for item in concept.get("items", []):
        descriptor = item.get("style_descriptor", "")
        name       = item.get("name", "")
        if descriptor:
            furniture_parts.append(descriptor)
        elif name:
            furniture_parts.append(name)

    furniture_desc = ", ".join(furniture_parts) if furniture_parts else f"{style_tags} furniture"

    prompt = (
        f"Interior design photograph, professional architectural photography, "
        f"same room structure with identical walls windows and doors, "
        f"furnished with: {furniture_desc}, "
        f"room dimensions approximately {width_ft} by {length_ft} feet, "
        f"wall color {wall_color}, {floor_type} floors, "
        f"color scheme: primary {primary} with {accent} accents, "
        f"lighting: {lighting}, "
        f"wide angle shot showing full room layout, "
        f"4K resolution, Architectural Digest style, "
        f"photorealistic, high detail, soft natural shadows, "
        f"keep all windows doors and architectural features in exact same position"
    )

    negative_prompt = (
        "cluttered, distorted furniture, unrealistic lighting, "
        "cartoon, illustration, painting, blurry, people, humans, "
        "text, watermark, oversaturated, dark, empty room, "
        "wrong furniture style, mismatched items, "
        "move windows, move doors, change walls, different room structure"
    )
    return prompt, negative_prompt


def _upload_image_to_imgbb(image_bytes: bytes) -> str:
    import urllib.request
    import urllib.parse

    imgbb_key = os.getenv("IMGBB_API_KEY", "")
    if not imgbb_key:
        import uuid
        os.makedirs("uploads/renders", exist_ok=True)
        filename = f"uploads/renders/{uuid.uuid4()}.png"
        with open(filename, "wb") as f:
            f.write(image_bytes)
        return f"http://localhost:8000/renders/{filename}"

    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data = urllib.parse.urlencode({
        "key": imgbb_key,
        "image": b64_image
    }).encode()

    req = urllib.request.Request(
        "https://api.imgbb.com/1/upload",
        data=data,
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = __import__('json').loads(resp.read())
        return result["data"]["url"]


async def _render_concept_async(
    concept: dict,
    room_analysis: dict,
    state_ref: list,
    image_path: str
) -> dict:
    concept_name  = concept.get("concept_name", "Design")
    concept_index = concept.get("concept_index", 0)
    prompt, negative_prompt = _build_prompt(concept, room_analysis)

    if not _use_real_api():
        colors = ["E8E8E0/8B7355", "F0EAD6/7B6B52", "2C2C2A/C17F3B"]
        color  = colors[concept_index % len(colors)]
        label  = concept_name.replace(" ", "+")
        url    = f"https://placehold.co/1024x1024/{color}?text={label}"
        return {
            "concept_name":  concept_name,
            "concept_index": concept_index,
            "image_url":     url,
            "prompt_used":   prompt,
            "mode":          "mock"
        }

    try:
        from huggingface_hub import InferenceClient

        hf_token = os.getenv("HF_TOKEN", "")
        client   = InferenceClient(api_key=hf_token)

        def run_flux():
            try:
                return client.text_to_image(
                    prompt,
                    model="black-forest-labs/FLUX.1-schnell",
                    negative_prompt=negative_prompt,
                )
            except StopIteration as e:
                raise RuntimeError(f"HF client error: {e}") from e

        loop = asyncio.get_event_loop()
        img = await loop.run_in_executor(None, run_flux)

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes = img_bytes.getvalue()

        image_url = _upload_image_to_imgbb(img_bytes)

        return {
            "concept_name":  concept_name,
            "concept_index": concept_index,
            "image_url":     image_url,
            "prompt_used":   prompt,
            "mode":          "real"
        }

    except Exception as e:
        return {
            "concept_name":  concept_name,
            "concept_index": concept_index,
            "image_url":     PLACEHOLDER_IMAGE,
            "prompt_used":   prompt,
            "mode":          "mock_fallback",
            "error":         str(e)
        }


def rendering_agent(state: AppState) -> AppState:
    sourced_products = state.get("sourced_products", [])
    room_analysis    = state.get("room_analysis", {})
    image_path       = state.get("image_path", "")

    state = log_stage_start(state, "rendering")
    state = log_event(state, "rendering", "render_start",
        f"Starting parallel rendering for {len(sourced_products)} concepts",
        data={"num_concepts": len(sourced_products),
              "mode": "real" if _use_real_api() else "mock"})

    if not sourced_products:
        sourced_products = [
            {"concept_name": "Design 1", "concept_index": 0, "items": []},
            {"concept_name": "Design 2", "concept_index": 1, "items": []},
            {"concept_name": "Design 3", "concept_index": 2, "items": []}
        ]

    for concept in sourced_products:
        state = log_event(state, "rendering", "building_prompt",
            f"Building prompt for '{concept.get('concept_name')}'",
            data={"concept": concept.get("concept_name")})

    state_ref = [state]

    async def render_all():
        tasks = [
            _render_concept_async(concept, room_analysis, state_ref, image_path)
            for concept in sourced_products
        ]
        return await asyncio.gather(*tasks)

    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, render_all())
                    render_results = future.result()
            else:
                render_results = loop.run_until_complete(render_all())
        except RuntimeError:
            render_results = asyncio.run(render_all())

        render_results = sorted(render_results, key=lambda x: x["concept_index"])

        for r in render_results:
            level = "success" if r.get("mode") != "mock_fallback" else "warning"
            state = log_event(state, "rendering", "render_complete",
                f"Render complete for '{r['concept_name']}' — mode: {r.get('mode')}",
                level=level,
                data={"concept":   r["concept_name"],
                      "mode":      r.get("mode"),
                      "image_url": r["image_url"]})

        state = log_stage_end(state, "rendering")
        return {**state, "render_urls": render_results, "error": None}

    except Exception as e:
        state = log_event(state, "rendering", "render_failed",
            f"Rendering fatal error: {str(e)}",
            level="error", data={"error": str(e)})
        state = log_stage_end(state, "rendering")
        return {
            **state,
            "render_urls": [],
            "error": f"rendering_failed: {str(e)}"
        }