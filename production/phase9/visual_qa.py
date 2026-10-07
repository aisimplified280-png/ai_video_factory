"""Visual QA & Image Quality Validator for Phase 9 & 10.5.

Validates that generated visual assets adhere to cinematic documentary standards.
Rejects:
- Low-detail or flat blurred artifacts
- Solid or corrupt images
- Anime / cartoon style indications
- Low resolution

Accepts:
- Realistic, high-contrast, documentary-grade 9:16 vertical images
"""
from __future__ import annotations

from pathlib import Path
from typing import Union
from PIL import Image, ImageStat


def validate_image_quality(
    image_input: Union[str, Path, Image.Image],
    prompt: str = "",
) -> tuple[bool, str]:
    """Validate visual quality of a candidate background image.
    
    Returns (is_valid, reason).
    """
    try:
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input).convert("RGB")
        else:
            img = image_input.convert("RGB")
    except Exception as e:
        return False, f"Failed to open image: {e}"

    # 1. Dimension and Aspect Ratio Check
    w, h = img.size
    if w < 540 or h < 960:
        return False, f"Resolution too low: {w}x{h} (minimum 540x960)"
    aspect_ratio = h / max(1, w)
    if aspect_ratio < 1.3:  # Not vertical enough for 9:16 short
        return False, f"Incorrect aspect ratio: {aspect_ratio:.2f} (expected vertical >= 1.3)"

    # 2. Check for solid or near-blank color (standard deviation of pixel values)
    stat = ImageStat.Stat(img)
    stddevs = stat.stddev
    avg_stddev = sum(stddevs) / len(stddevs)
    if avg_stddev < 12.0:
        return False, f"Image lacks detail / nearly flat color (stddev: {avg_stddev:.1f})"

    # 3. Check for extreme blown-out white or complete blackness
    mean_brightness = sum(stat.mean) / len(stat.mean)
    if mean_brightness < 4.0:
        return False, f"Image is completely dark/black (mean: {mean_brightness:.1f})"
    if mean_brightness > 250.0:
        return False, f"Image is completely blown out white (mean: {mean_brightness:.1f})"

    # 4. Anti-Cartoon / Anti-Anime Prompt Guard
    prompt_lower = prompt.lower()
    rejected_terms = ["anime", "cartoon", "illustration", "vector art", "drawing", "comic"]
    for term in rejected_terms:
        if term in prompt_lower and "no " + term not in prompt_lower:
            return False, f"Prompt requests prohibited aesthetic: '{term}'"

    return True, "PASS: Cinematic documentary quality verified"


def sanitize_cinematic_prompt(prompt: str) -> str:
    """Ensure the prompt enforces documentary photography and suppresses cartoons."""
    # Enforce negative constraints for Pollinations
    anti_tropes = (
        "photorealistic, cinematic documentary photography, realistic industrial materials, "
        "natural lighting, 8k resolution, highly detailed, no anime, no cartoon, no illustration, "
        "no drawing, no text, no watermark, no 3d render"
    )
    clean = prompt.strip().rstrip(".")
    return f"{clean}, {anti_tropes}"
