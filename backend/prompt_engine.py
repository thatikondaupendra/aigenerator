from __future__ import annotations


NEGATIVE_PROMPT = (
    "low quality, blurry, watermark, text, logo, deformed anatomy, extra fingers, "
    "duplicate limbs, bad hands, distorted face, plastic skin, overexposed"
)

PROMPT_TEMPLATES: dict[str, str] = {
    "cinematic_male": (
        "ultra realistic handsome Indian male, cinematic lighting, sharp jawline, "
        "realistic skin texture, volumetric light, luxury interior, shallow depth of field, 8k"
    ),
    "kitchen_scene": (
        "ultra realistic Indian man cooking in a modern kitchen, natural body hair, "
        "warm cinematic lighting, highly detailed skin, photorealistic"
    ),
    "luxury_scene": (
        "luxury penthouse apartment, city skyline, golden hour sunlight, cinematic photography"
    ),
}


def build_prompt(user_prompt: str, template: str | None = None) -> str:
    base = PROMPT_TEMPLATES.get(template or "", "")
    if not base:
        return user_prompt.strip()
    return f"{user_prompt.strip()}, {base}"


def build_negative_prompt(negative_prompt: str | None = None) -> str:
    if not negative_prompt:
        return NEGATIVE_PROMPT
    return f"{negative_prompt.strip()}, {NEGATIVE_PROMPT}"
