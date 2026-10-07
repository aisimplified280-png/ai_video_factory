"""Asset Manager & Creator — pre-renders and caches reusable branding, subscribe cards, and graphic icons.

Assets are saved in `assets_library/` to preserve CPU/token resources and enable reuse across videos.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import platform

ROOT = Path(__file__).resolve().parent
LIBRARY_DIR = ROOT / "assets_library"
ICONS_DIR = LIBRARY_DIR / "icons"

LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
ICONS_DIR.mkdir(parents=True, exist_ok=True)


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    s = platform.system()
    paths = []
    if s == "Windows":
        b = "C:/Windows/Fonts/"
        paths = [b + "arialbd.ttf", b + "ARLRDBD.TTF"] if bold else [b + "arial.ttf", b + "ARIAL.TTF"]
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def extract_logo_with_transparency(logo_path: Path) -> Image.Image:
    """Load logo image, key out white background, crop to non-white content bounding box, and pad to square."""
    img = Image.open(logo_path).convert("RGBA")
    
    # Convert white/near-white pixels (R>230, G>230, B>230) to transparent (A=0)
    datas = img.getdata()
    newData = []
    for item in datas:
        if item[0] > 230 and item[1] > 230 and item[2] > 230:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)
    img.putdata(newData)
    
    # Find bounding box of visible graphic content
    bbox = img.getbbox()
    if bbox:
        margin = 15
        x0 = max(0, bbox[0] - margin)
        y0 = max(0, bbox[1] - margin)
        x1 = min(img.width, bbox[2] + margin)
        y1 = min(img.height, bbox[3] + margin)
        cropped = img.crop((x0, y0, x1, y1))
        
        # Fit into square canvas with transparent margin
        w, h = cropped.size
        max_dim = max(w, h)
        sq = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
        sq.paste(cropped, ((max_dim - w) // 2, (max_dim - h) // 2))
        return sq
    return img


def get_or_create_subscribe_card(force_recreate: bool = False) -> Path:
    """Generate or retrieve cached subscribe card overlay PNG with official LOGO avatar."""
    target = LIBRARY_DIR / "subscribe_card.png"
    if target.exists() and not force_recreate:
        return target

    w, h = 640, 240
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Translucent dark glass container
    d.rounded_rectangle((0, 0, w, h), radius=24, fill=(13, 31, 46, 235), outline=(26, 92, 255, 255), width=3)

    # Accent top highlight bar
    d.rounded_rectangle((40, 16, w - 40, 22), radius=3, fill=(238, 108, 77, 255))

    # Embed official channel LOGO if available with transparency
    from channel import LOGO
    has_logo = False
    if LOGO and LOGO.exists():
        try:
            logo_sq = extract_logo_with_transparency(LOGO)
            size = 84
            resized = logo_sq.resize((size, size), Image.LANCZOS)
            
            # Smooth circular background pill for logo avatar
            avatar_x, avatar_y = 36, 46
            d.ellipse((avatar_x - 4, avatar_y - 4, avatar_x + size + 4, avatar_y + size + 4), fill=(10, 26, 38, 255), outline=(26, 92, 255, 255), width=3)
            
            # Paste transparent logo cleanly over avatar pill
            img.paste(resized, (avatar_x, avatar_y), resized)
            has_logo = True
        except Exception as ex:
            print(f"Warning embedding logo avatar: {ex}")

    # Text positioning depending on whether avatar exists
    text_x = 144 if has_logo else w // 2
    anchor = "la" if has_logo else "mm"

    # Channel Title
    f_title = _get_font(32, bold=True)
    d.text((text_x, 50 if has_logo else 65), "AI SIMPLIFIED LAB", font=f_title, fill=(248, 247, 242, 255), anchor=anchor)

    # Tagline
    f_sub = _get_font(18, bold=False)
    d.text((text_x, 90 if has_logo else 105), "Simplifying Complex Tech", font=f_sub, fill=(156, 176, 189, 255), anchor=anchor)

    # Subscribe Button Pill
    btn_w, btn_h = 280, 52
    btn_x, btn_y = (w - btn_w) // 2, 156
    d.rounded_rectangle((btn_x, btn_y, btn_x + btn_w, btn_y + btn_h), radius=26, fill=(238, 108, 77, 255))

    f_btn = _get_font(22, bold=True)
    d.text((w // 2, btn_y + btn_h // 2), "SUBSCRIBE NOW", font=f_btn, fill=(255, 255, 255, 255), anchor="mm")

    img.save(target)
    return target



def get_or_create_brand_badge() -> Path:
    """Generate or retrieve cached channel watermark badge PNG."""
    target = LIBRARY_DIR / "brand_badge.png"
    if target.exists():
        return target

    w, h = 320, 60
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle((0, 0, w, h), radius=30, fill=(26, 92, 255, 220))
    fnt = _get_font(18, bold=True)
    d.text((w // 2, h // 2), "⚡ AI SIMPLIFIED LAB", font=fnt, fill=(255, 255, 255, 255), anchor="mm")

    img.save(target)
    return target


import io

def get_highres_emoji(emoji_str: str) -> Path | None:
    """Download and cache a high-res Noto Emoji PNG with Twemoji fallback."""
    if not emoji_str:
        return None

    emoji_str = emoji_str.strip()
    clean_hex = "_".join(f"{ord(c):x}" for c in emoji_str if ord(c) not in (0xFE0F, 0xFE0E))
    raw_hex = "_".join(f"{ord(c):x}" for c in emoji_str)

    target_clean = ICONS_DIR / f"emoji_u{clean_hex}.png"
    target_raw = ICONS_DIR / f"emoji_u{raw_hex}.png"

    if target_clean.exists():
        return target_clean
    if target_raw.exists():
        return target_raw

    urls = [
        f"https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/512/emoji_u{clean_hex}.png",
        f"https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/512/emoji_u{raw_hex}.png",
        f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{clean_hex}.png",
    ]

    import urllib.request
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = response.read()
                with open(target_clean, "wb") as f:
                    f.write(data)
            return target_clean
        except Exception:
            continue

    print(f"  -> Could not download emoji for '{emoji_str}' (hex: {clean_hex})")
    return None

def get_or_create_ai_icon(prompt: str, filename: str) -> Path | None:
    """Generate an AI icon using DALL-E 3, remove background, and cache it."""
    import os
    import json
    import urllib.request
    import io
    
    target = ICONS_DIR / f"{filename}.png"
    if target.exists():
        return target
    import urllib.parse
    print(f"  -> Icon Builder Agent: Generating '{filename}' via Pollinations...")
    try:
        encoded_prompt = urllib.parse.quote(f"A minimalist, clean, flat vector 3D icon of {prompt} on a pure solid white background. No text, high quality.")
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=45) as img_resp:
            img_data = img_resp.read()
            
        img = Image.open(io.BytesIO(img_data)).convert("RGBA")
        
        # Crop bottom 40px to remove Pollinations watermark if it exists
        w, h = img.size
        img = img.crop((0, 0, w, h - 40))
        
        # Make white background transparent using edge flood-fill to avoid jagged fringes
        from PIL import ImageDraw
        # Try flooding from corners. (thresh=20 handles near-white artifacts)
        # Using 255,255,255,0 (transparent)
        ImageDraw.floodfill(img, (0, 0), (255, 255, 255, 0), thresh=20)
        ImageDraw.floodfill(img, (w-1, 0), (255, 255, 255, 0), thresh=20)
        ImageDraw.floodfill(img, (0, h-41), (255, 255, 255, 0), thresh=20)
        ImageDraw.floodfill(img, (w-1, h-41), (255, 255, 255, 0), thresh=20)
        
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        img.thumbnail((300, 300), Image.LANCZOS)
        
        img.save(target)
        return target
    except urllib.error.HTTPError as e:
        print(f"  -> Error generating AI icon (HTTP {e.code}): {e.read().decode('utf-8', errors='ignore')}")
        from PIL import ImageDraw
    except Exception as e:
        print(f"  -> Error generating AI icon, using local fallback: {e}")
        from PIL import ImageDraw
        img = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        
        # Draw beautiful tech tile
        d.rounded_rectangle((10, 10, 290, 290), radius=60, fill=(30, 68, 96, 240), outline=(64, 224, 208, 255), width=8)
        
        # Add letter
        letter = prompt.strip()[0].upper() if prompt else "?"
        fnt = _get_font(160, bold=True)
        
        try:
            bbox = d.textbbox((0, 0), letter, font=fnt)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except Exception:
            tw, th = 80, 80
            
        d.text((150, 150 - th//4), letter, font=fnt, fill=(64, 224, 208, 255), anchor="mm")
        
        img.save(target)
        return target

def get_or_create_background(prompt: str, filename: str) -> Path | None:
    """Generate a high-quality vertical background visual using Pollinations and cache it."""
    import urllib.request
    import urllib.parse
    import io
    
    target = LIBRARY_DIR / f"{filename}.png"
    if target.exists():
        return target
        
    print(f"  -> Visual Intelligence: Generating background '{filename}' via Pollinations...")
    try:
        from production.phase9.visual_qa import sanitize_cinematic_prompt, validate_image_quality
        sanitized_prompt = sanitize_cinematic_prompt(prompt)
        # Request 1080x1920 (9:16) for shorts
        encoded_prompt = urllib.parse.quote(sanitized_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as img_resp:
            img_data = img_resp.read()
            
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        
        # Crop bottom 40px to remove Pollinations watermark if it exists
        w, h = img.size
        img = img.crop((0, 0, w, h - 40))
        img = img.resize((1080, 1920), Image.LANCZOS)
        
        # Visual QA Quality Gate
        valid, reason = validate_image_quality(img, prompt=prompt)
        if not valid:
            print(f"  -> Visual QA Rejected: {reason}")
            raise ValueError(reason)

        img.save(target)
        return target
    except urllib.error.HTTPError as e:
        print(f"  -> Error generating background (HTTP {e.code}): {e.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"  -> Error generating background: {e}")
        
    # Local fallback
    img = Image.new("RGB", (1080, 1920), (10, 14, 26))
    d = ImageDraw.Draw(img)
    fnt = _get_font(48, bold=True)
    d.text((540, 960), "VISUAL FALLBACK\n" + prompt[:50] + "...", font=fnt, fill=(100, 100, 100, 255), anchor="mm", align="center")
    img.save(target)
    return target


def ensure_all_cached_assets() -> dict[str, Path]:
    """Pre-warm asset library on startup."""
    return {
        "subscribe": get_or_create_subscribe_card(),
        "brand_badge": get_or_create_brand_badge(),
    }


if __name__ == "__main__":
    res = ensure_all_cached_assets()
    print(f"Cached asset library initialized at {LIBRARY_DIR}: {list(res.keys())}")
