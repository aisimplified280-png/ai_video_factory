"""Animation engine v2 — precise per-element motion control.

Every element has:
  - (x, y): final resting position
  - from_x, from_y: where it enters FROM (off-screen)
  - enter_start, enter_end: timing as fraction of scene intro
  - easing: motion curve
  - draw_fn: how to render at (x, y) with progress 0→1

Motion types map to specific from→to trajectories:
  slide_up    → enters from (x, y+80)  moving up
  slide_down  → enters from (x, y-80)  moving down
  slide_left  → enters from (x-100, y) moving right
  slide_right → enters from (x+100, y) moving left
  scale       → starts at 0% size, scales to 100%
  pop         → starts at 0% size with bounce overshoot
  fade        → starts transparent, fades in
  draw_line   → line extends from start point to end point
  typewriter  → text appears character by character
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Defensive PIL Safety Patches ─────────────────────────────────────────
# Prevents any mathematical overshoots, negative easings, or AI custom code
# from ever raising "x1 must be greater than or equal to x0"
_orig_rounded_rect = ImageDraw.ImageDraw.rounded_rectangle
def _safe_draw_rounded_rect(self, xy, radius=0, *args, **kwargs):
    try:
        x0, y0, x1, y1 = xy
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        if x1 <= x0 or y1 <= y0: return
        r = max(0, min(radius, int(abs(x1 - x0) // 2), int(abs(y1 - y0) // 2)))
        return _orig_rounded_rect(self, (x0, y0, x1, y1), r, *args, **kwargs)
    except Exception:
        pass
ImageDraw.ImageDraw.rounded_rectangle = _safe_draw_rounded_rect

_orig_rect = ImageDraw.ImageDraw.rectangle
def _safe_draw_rect(self, xy, *args, **kwargs):
    try:
        x0, y0, x1, y1 = xy
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        if x1 <= x0 or y1 <= y0: return
        return _orig_rect(self, (x0, y0, x1, y1), *args, **kwargs)
    except Exception:
        pass
ImageDraw.ImageDraw.rectangle = _safe_draw_rect

_orig_ellipse = ImageDraw.ImageDraw.ellipse
def _safe_draw_ellipse(self, xy, *args, **kwargs):
    try:
        x0, y0, x1, y1 = xy
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        if x1 <= x0 or y1 <= y0: return
        return _orig_ellipse(self, (x0, y0, x1, y1), *args, **kwargs)
    except Exception:
        pass
ImageDraw.ImageDraw.ellipse = _safe_draw_ellipse

W, H = 1080, 1920
FPS = 24

# ── Colours ──────────────────────────────────────────────────────────────
WHITE = "#FFFFFF"
INK = "#111111"
MUTED = "#65707C"
ACCENT = "#E03188"
ORANGE = "#F59E0B"
RED = "#DC2626"
GREEN = "#16A34A"
DARK = "#1E1E1E"
DARK2 = "#111111"
PAPER_BG = "#F8F8F6"
LIGHT_BLUE = "#E03188"
SOFT_TEAL = "#16A34A"
BRAND_BLUE = "#1E1E1E"
EDITORIAL_LIGHT = "#F6F8FC"
EDITORIAL_BLUE = "#1E5EFF"
EDITORIAL_DEEP = "#0E1B3A"
EDITORIAL_MUTED = "#697C96"
EDITORIAL_SOFT = "#EAF2FF"


# ── Fonts ────────────────────────────────────────────────────────────────
def _fc(bold, mono=False):
    import platform
    s = platform.system()
    if s == "Windows":
        b = "C:/Windows/Fonts/"
        if mono:
            return [b+"consola.ttf", b+"lucon.ttf"]
        return ([b+"segoeuib.ttf", b+"arialbd.ttf"] if bold else [b+"segoeui.ttf", b+"arial.ttf"])
    if s == "Darwin":
        if mono:
            return ["/System/Library/Fonts/SFNSMono.ttf", "/System/Library/Fonts/Menlo.ttc"]
        return ["/System/Library/Fonts/Helvetica.ttc"]
    if mono:
        return ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
    return (["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])

def _f(size, bold=False, mono=False):
    for p in _fc(bold, mono):
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

def _draw_hand_pointer(d, cx, cy, scale=1.0):
    """Draw a crisp vector hand pointer / index cursor."""
    s = max(0.2, scale)
    pts = [
        (cx, cy),
        (cx + int(4 * s), cy + int(14 * s)),
        (cx + int(10 * s), cy + int(12 * s)),
        (cx + int(14 * s), cy + int(18 * s)),
        (cx + int(18 * s), cy + int(16 * s)),
        (cx + int(22 * s), cy + int(22 * s)),
        (cx + int(26 * s), cy + int(20 * s)),
        (cx + int(28 * s), cy + int(28 * s)),
        (cx + int(20 * s), cy + int(40 * s)),
        (cx + int(5 * s), cy + int(45 * s)),
        (cx - int(10 * s), cy + int(25 * s)),
        (cx - int(12 * s), cy + int(15 * s)),
        (cx - int(4 * s), cy + int(12 * s)),
        (cx - int(2 * s), cy + int(16 * s)),
    ]
    # Draw dark shadow
    d.polygon([(x + 2, y + 2) for (x, y) in pts], fill=(10, 10, 10, 180))
    # Draw white filled pointer with crisp outline
    d.polygon(pts, fill=(255, 255, 255, 255), outline=(20, 20, 20, 255))


def _draw_checkmark(d, cx, cy, size=14, color=WHITE):
    sz = int(size)
    d.line([(cx - sz, cy), (cx - sz // 3, cy + int(sz * 0.7)), (cx + sz, cy - int(sz * 0.8))], fill=color, width=max(2, sz // 4))


FT = _f(87, True)   # title
FH1 = _f(63, True)  # heading 1
FH2 = _f(54, True)  # heading 2
FB = _f(42)          # body
FS = _f(30)          # small
FL = _f(27, True)    # label
FBIG = _f(120, True)  # big icon
FMASS = _f(180, True)# massive
FMONO_S = _f(24, False, True)
FMONO = _f(30, False, True)
FMONO_L = _f(42, False, True)


# ── Easing ───────────────────────────────────────────────────────────────
def ease_out_cubic(t): return 1 - (1 - t) ** 3
def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def ease_out_elastic(t):
    if t in (0, 1): return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1
def ease_in_out_quad(t): return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2
def ease_out_bounce(t):
    n1, d1 = 7.5625, 2.75
    if t < 1/d1:
        return n1 * t * t
    elif t < 2/d1:
        t2 = t - 1.5/d1
        return n1 * t2 * t2 + 0.75
    elif t < 2.5/d1:
        t2 = t - 2.25/d1
        return n1 * t2 * t2 + 0.9375
    else:
        t2 = t - 2.625/d1
        return n1 * t2 * t2 + 0.984375
def linear(t): return t

EASINGS = {
    "ease_out_cubic": ease_out_cubic,
    "ease_out_back": ease_out_back,
    "ease_out_elastic": ease_out_elastic,
    "ease_out_bounce": ease_out_bounce,
    "ease_in_out_quad": ease_in_out_quad,
    "linear": linear,
}


# ── Element ──────────────────────────────────────────────────────────────
@dataclass
class El:
    """One animatable element with full motion control."""
    # Final resting position
    x: float = W / 2
    y: float = H / 2
    # Entry position (where it comes FROM)
    from_x: float | None = None  # None = no horizontal motion
    from_y: float | None = None  # None = no vertical motion
    # Timing (fraction of intro duration)
    enter_start: float = 0.0
    enter_end: float = 0.25
    # Easing
    easing: str = "ease_out_cubic"
    # Motion type (determines from_x/from_y if not set)
    motion: str = "fade"  # slide_up|slide_down|slide_left|slide_right|scale|pop|fade|draw_line|typewriter
    # Draw function: (draw, current_x, current_y, progress, data) -> None
    draw_fn: Callable | None = None
    data: dict = field(default_factory=dict)
    # Hold visible after enter
    hold: bool = True
    persist: bool = False
    # Exit animation timing
    exit_start: float | None = None
    exit_motion: str | None = None
    
    # Compositor attributes
    depth: float = 1.0
    id: str = ""


def _apply_motion(el: El):
    """Set from_x/from_y based on motion type if not already set."""
    if el.from_x is not None or el.from_y is not None:
        return  # Already set explicitly
    m = el.motion
    if m == "slide_up":
        el.from_x, el.from_y = el.x, el.y + 80
    elif m == "slide_down":
        el.from_x, el.from_y = el.x, el.y - 80
    elif m == "slide_left":
        el.from_x, el.from_y = el.x - 120, el.y
    elif m == "slide_right":
        el.from_x, el.from_y = el.x + 120, el.y
    elif m in ("scale", "pop", "fade", "draw_line", "typewriter"):
        el.from_x, el.from_y = el.x, el.y
    else:
        el.from_x, el.from_y = el.x, el.y


# ── Drawing helpers ──────────────────────────────────────────────────────
def _lerp(a, b, t): return a + (b - a) * t

def _hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _lerp_color(c1, c2, t):
    r1,g1,b1 = _hex_rgb(c1); r2,g2,b2 = _hex_rgb(c2)
    return "#{:02x}{:02x}{:02x}".format(int(_lerp(r1,r2,t)), int(_lerp(g1,g2,t)), int(_lerp(b1,b2,t)))

def _txt(d, cx, cy, text, fnt, fill, anchor="mm"):
    d.text((int(cx), int(cy)), text, font=fnt, fill=fill, anchor=anchor)

def _txt_width(d, text, fnt):
    bb = d.textbbox((0,0), text, font=fnt)
    return bb[2] - bb[0]

def _measure_text_bounds(d, text, fnt, max_width=500):
    max_w = min(max_width, W - 60)
    words = str(text).split()
    if not words: return (0, 0)
    lines = []
    curr = []
    for w in words:
        test_line = " ".join(curr + [w]) if curr else w
        bb = d.textbbox((0,0), test_line, font=fnt, anchor="mm")
        tw = bb[2] - bb[0]
        if tw <= max_w:
            curr.append(w)
        else:
            if curr: lines.append(" ".join(curr))
            curr = [w]
    if curr: lines.append(" ".join(curr))
    
    line_heights = []
    max_line_width = 0
    for line in lines:
        bb = d.textbbox((0,0), line, font=fnt, anchor="mm")
        line_heights.append(bb[3] - bb[1])
        tw = bb[2] - bb[0]
        if tw > max_line_width:
            max_line_width = tw
            
    line_spacing = max(8, int(fnt.size * 0.3)) if hasattr(fnt, "size") else 14
    total_h = sum(line_heights) + (len(lines) - 1) * line_spacing
    return (max_line_width, total_h)

def _center(d, cx, cy, text, fnt, fill, max_width=500, align="center"):
    max_w = min(max_width, W - 60)
    words = str(text).split()
    if not words: return
    lines = []
    curr = []
    for w in words:
        test_line = " ".join(curr + [w]) if curr else w
        bb = d.textbbox((0,0), test_line, font=fnt, anchor="mm")
        tw = bb[2] - bb[0]
        if tw <= max_w:
            curr.append(w)
        else:
            if curr: lines.append(" ".join(curr))
            curr = [w]
    if curr: lines.append(" ".join(curr))
    
    line_heights = []
    for line in lines:
        bb = d.textbbox((0,0), line, font=fnt, anchor="mm")
        line_heights.append(bb[3] - bb[1])
        
    line_spacing = max(8, int(fnt.size * 0.3)) if hasattr(fnt, "size") else 14
    total_h = sum(line_heights) + (len(lines) - 1) * line_spacing
    
    cy_current = cy - total_h / 2
    
    for i, line in enumerate(lines):
        tw = d.textbbox((0,0), line, font=fnt, anchor="mm")[2] - d.textbbox((0,0), line, font=fnt, anchor="mm")[0]
        th = line_heights[i]
        line_cy = cy_current + th / 2
        
        if align == "left":
            draw_x = cx + tw/2
        elif align == "right":
            draw_x = cx - tw/2
        else:
            draw_x = cx
            
        if draw_x - tw/2 < 28: draw_x = 28 + tw/2
        if draw_x + tw/2 > W - 28: draw_x = W - 28 - tw/2
        
        d.text((int(draw_x), int(line_cy)), line, font=fnt, fill=fill, anchor="mm")
        cy_current += th + line_spacing

def _pop(d, cx, cy, text, fnt, fill, progress):
    s = ease_out_back(progress)
    if s < 0.01: return
    _center(d, cx, cy, text, fnt, fill)

def _box(d, cx, cy, w, h, fill, radius=20, outline=None, stroke=2):
    x1, y1 = int(cx-w//2), int(cy-h//2)
    d.rounded_rectangle((x1, y1, x1+w, y1+h), radius=radius, fill=fill, outline=outline, width=stroke)

def _rect(d, x1, y1, x2, y2, fill, radius=20, outline=None, stroke=2):
    """Corner-coordinate rect. Use when you already have top-left and bottom-right coords."""
    d.rounded_rectangle((int(x1), int(y1), int(x2), int(y2)), radius=radius, fill=fill, outline=outline, width=stroke)

def _scale_box(d, cx, cy, w, h, fill, radius, progress):
    s = ease_out_back(progress)
    sw, sh = int(w*s), int(h*s)
    if sw < 2: return
    x1, y1 = int(cx-sw//2), int(cy-sh//2)
    d.rounded_rectangle((x1, y1, x1+sw, y1+sh), radius=min(radius, sw//4, sh//4), fill=fill)

def _circle(d, cx, cy, r, fill=None, outline=None, width=3, stroke=None, **kwargs):
    w = stroke if stroke is not None else width
    if fill:
        d.ellipse((int(cx-r), int(cy-r), int(cx+r), int(cy+r)), fill=fill)
    if outline:
        d.ellipse((int(cx-r), int(cy-r), int(cx+r), int(cy+r)), outline=outline, width=w)

def _scale_circle(d, cx, cy, r, outline, width, progress):
    s = ease_out_back(progress)
    cr = int(r * s)
    if cr < 2: return
    d.ellipse((int(cx-cr), int(cy-cr), int(cx+cr), int(cy+cr)), outline=outline, width=width)

def _grow_circle(d, cx, cy, r, fill, progress):
    cr = int(r * ease_out_cubic(progress))
    if cr < 1: return
    d.ellipse((int(cx-cr), int(cy-cr), int(cx+cr), int(cy+cr)), fill=fill)

def _accent_bar(d, y, width=140, color=ACCENT):
    x = (W - int(width)) // 2
    d.rounded_rectangle((x, int(y), x+int(width), int(y+5)), radius=2, fill=color)

def _arrow(d, x1, y1, x2, y2, fill=ACCENT, width=5, progress=1.0):
    s = ease_out_cubic(progress)
    ex = int(_lerp(x1, x2, s))
    ey = int(_lerp(y1, y2, s))
    d.line([(x1, y1), (ex, ey)], fill=fill, width=width)
    if progress > 0.3:
        sz = 14
        angle = math.atan2(y2 - y1, x2 - x1)
        a1 = angle + math.pi * 5 / 6
        a2 = angle - math.pi * 5 / 6
        px1 = ex + sz * math.cos(a1)
        py1 = ey + sz * math.sin(a1)
        px2 = ex + sz * math.cos(a2)
        py2 = ey + sz * math.sin(a2)
        d.polygon([(ex, ey), (px1, py1), (px2, py2)], fill=fill)

def _dashed(d, x1, y1, x2, y2, fill=INK, width=2, dash=10, gap=6):
    length = math.hypot(x2-x1, y2-y1)
    if length == 0: return
    dx, dy = (x2-x1)/length, (y2-y1)/length
    pos = 0
    while pos < length:
        se = min(pos+dash, length)
        d.line([(x1+dx*pos, y1+dy*pos), (x1+dx*se, y1+dy*se)], fill=fill, width=width)
        pos += dash + gap

def _grid(d, x1, y1, x2, y2, fill, progress):
    vx = int(x1 + (x2-x1) * min(progress*1.5, 1))
    vy = int(y1 + (y2-y1) * min(progress*1.5, 1))
    for y in range(y1, vy, 50): d.line((x1, y, x2, y), fill=fill, width=1)
    for x in range(x1, vx, 50): d.line((x, y1, x, y2), fill=fill, width=1)

def _progress_dots(d, current, total, y=1240):
    r, gap = 5, 20
    tw = total * r * 2 + (total-1) * gap
    sx = (W - tw) // 2
    for i in range(total):
        cx = sx + i * (r*2+gap) + r
        d.ellipse((cx-r, int(y)-r, cx+r, int(y)+r), fill=ACCENT if i == current else "#C8D6DC")

def _db_icon(d, cx, cy, w=80, h=100, fill=INK, progress=1.0):
    s = ease_out_cubic(progress)
    w, h = int(w*s), int(h*s)
    if w < 2: return
    ew, eh = w//2, int(w*0.2)
    # Body
    d.rectangle((cx-ew, cy-h//2, cx+ew, cy+h//2), fill=fill)
    # Disks
    d.ellipse((cx-ew, cy-h//2-eh, cx+ew, cy-h//2+eh), fill="#FFFFFF", width=3)
    d.ellipse((cx-ew, cy-eh, cx+ew, cy+eh), outline="#FFFFFF", width=3)
    d.ellipse((cx-ew, cy+h//2-eh, cx+ew, cy+h//2+eh), fill=fill, outline="#FFFFFF", width=3)

def _server_icon(d, cx, cy, w=100, h=120, fill=INK, progress=1.0):
    s = ease_out_cubic(progress)
    w, h = int(w*s), int(h*s)
    if w < 2: return
    _box(d, cx, cy, w, h, fill, 10)
    d.rectangle((cx-w//2+10, cy-h//2+15, cx+w//2-10, cy-h//2+30), fill="#FFFFFF")
    d.rectangle((cx-w//2+10, cy-10, cx+w//2-10, cy+5), fill="#FFFFFF")
    d.rectangle((cx-w//2+10, cy+h//2-30, cx+w//2-10, cy+h//2-15), fill="#FFFFFF")

def _cloud_icon(d, cx, cy, w=120, fill=INK, progress=1.0):
    s = ease_out_cubic(progress)
    r = int((w/4)*s)
    if r < 2: return
    d.ellipse((cx-r*2, cy-r, cx, cy+r), fill=fill)
    d.ellipse((cx-r, cy-r*2, cx+r, cy+r), fill=fill)
    d.ellipse((cx, cy-r, cx+r*2, cy+r), fill=fill)

def _smartphone_icon(d, cx, cy, w=70, h=140, fill=INK, progress=1.0):
    s = ease_out_cubic(progress)
    w, h = int(w*s), int(h*s)
    if w < 2: return
    _box(d, cx, cy, w, h, fill, 15)
    _box(d, cx, cy-10, int(w*0.8), int(h*0.75), "#FFFFFF", 5)
    d.ellipse((cx-4, cy+h//2-15, cx+4, cy+h//2-7), fill="#FFFFFF")

def _terminal_window(d, cx, cy, w=480, h=240, title="bash", lines=None, progress=1.0):
    s = ease_out_back(progress)
    if s < 0.01: return
    sw, sh = int(w * s), int(h * s)
    if sw < 10 or sh < 10: return
    x1, y1 = int(cx - sw // 2), int(cy - sh // 2)
    # Window body
    d.rounded_rectangle((x1, y1, x1 + sw, y1 + sh), radius=16, fill="#121820", outline="#2A3848", width=2)
    # Header bar
    header_h = min(36, max(12, sh // 5))
    d.rounded_rectangle((x1, y1, x1 + sw, y1 + header_h), radius=16, fill="#1B2430")
    d.rectangle((x1, y1 + header_h - 8, x1 + sw, y1 + header_h), fill="#1B2430")
    # 3 Mac dots
    if sw > 80:
        dot_y = y1 + header_h // 2
        d.ellipse((x1 + 14, dot_y - 4, x1 + 22, dot_y + 4), fill="#FF5F56")
        d.ellipse((x1 + 28, dot_y - 4, x1 + 36, dot_y + 4), fill="#FFBD2E")
        d.ellipse((x1 + 42, dot_y - 4, x1 + 50, dot_y + 4), fill="#27C93F")
    if title and sw > 160:
        d.text((cx, y1 + header_h // 2), str(title), font=FL, fill="#8898AA", anchor="mm")
    # Code content
    if lines and progress > 0.3:
        if isinstance(lines, str):
            lines = [l.strip() for l in lines.split("\n") if l.strip()]
        line_y = y1 + header_h + 18
        t_sec = getattr(d, "t_seconds", 0.0)
        show_cursor = int(t_sec * 2.5) % 2 == 0
        for idx_l, line in enumerate(lines[:5]):
            if line_y + 20 > y1 + sh: break
            col = "#00F0FF" if line.startswith("$") or line.startswith(">") else "#F8F7F2"
            display_line = line
            if idx_l == len(lines[:5]) - 1 and show_cursor:
                display_line += " ▌"
            d.text((x1 + 20, line_y), display_line, font=FS, fill=col)
            line_y += 28

def _metric_card(d, cx, cy, w=340, h=180, value="99.9%", label="SUCCESS RATE", subtext="", color=ACCENT, progress=1.0):
    s = ease_out_back(progress)
    t_sec = getattr(d, "t_seconds", 0.0)
    if progress >= 1.0: s *= (1.0 + 0.018 * math.sin(t_sec * math.pi * 1.5 + cx))
    if s < 0.01: return
    sw, sh = int(w * s), int(h * s)
    if sw < 10: return
    x1, y1 = int(cx - sw // 2), int(cy - sh // 2)
    # Card background
    d.rounded_rectangle((x1, y1, x1 + sw, y1 + sh), radius=20, fill="#FFFFFF", outline="#DCE4EC", width=2)
    # Accent top pill
    d.rounded_rectangle((x1 + 20, y1 + 16, x1 + sw - 20, y1 + 22), radius=3, fill=color)
    # Big Stat Value
    if progress > 0.2:
        _center(d, cx, cy - 12, str(value), FH1, color, max_width=sw - 40)
    # Label
    if label and progress > 0.4:
        _center(d, cx, cy + 34, str(label).upper(), FL, MUTED, max_width=sw - 40)
    if subtext and progress > 0.5:
        _center(d, cx, cy + 62, str(subtext), FS, "#8898AA", max_width=sw - 40)

def _badge(d, cx, cy, text="⚡ FEATURE", color=ACCENT, progress=1.0):
    s = ease_out_back(progress)
    t_sec = getattr(d, "t_seconds", 0.0)
    if progress >= 1.0: s *= (1.0 + 0.02 * math.sin(t_sec * math.pi * 1.5 + cx))
    if s < 0.01: return
    fnt = FH2
    bb = d.textbbox((0,0), text, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    bw, bh = int((tw + 60) * s), int((th + 30) * s)
    if bw < 5: return
    x1, y1 = int(cx - bw // 2), int(cy - bh // 2)
    d.rounded_rectangle((x1, y1, x1 + bw, y1 + bh), radius=max(8, bh // 2), fill=color)
    if progress > 0.3:
        d.text((cx, cy - 2), text, font=fnt, fill=WHITE, anchor="mm")

def _alert_card(d, cx, cy, w=480, h=140, title="IMPORTANT", message="", is_success=False, progress=1.0):
    s = ease_out_back(progress)
    if s < 0.01: return
    sw, sh = int(w * s), int(h * s)
    if sw < 10: return
    x1, y1 = int(cx - sw // 2), int(cy - sh // 2)
    accent_col = GREEN if is_success else ACCENT
    bg_col = "#F0FAF0" if is_success else "#FFF5F2"
    d.rounded_rectangle((x1, y1, x1 + sw, y1 + sh), radius=16, fill=bg_col, outline=accent_col, width=2)
    # Title & message
    if progress > 0.2:
        d.text((x1 + 30, y1 + 24), ("✔ " if is_success else "⚠ ") + title.upper(), font=FH2, fill=accent_col)
    if message and progress > 0.4:
        _center(d, cx + 10, y1 + 75, message, FB, INK, max_width=sw - 60)


def _vs_card(d, cx, cy, w=800, h=260, left_text="Docker", right_text="VMs", progress=1.0):
    s = ease_out_back(progress)
    if s < 0.01: return
    sw, sh = int(w * s), int(h * s)
    if sw < 20: return
    card_w = (sw - 40) // 2
    x1, y1 = int(cx - sw // 2), int(cy - sh // 2)
    
    # Left Card (Option A - Blue/Dark)
    d.rounded_rectangle((x1, y1, x1 + card_w, y1 + sh), radius=24, fill="#0F172A", outline="#38BDF8", width=3)
    d.rounded_rectangle((x1 + 10, y1 + 10, x1 + card_w - 10, y1 + 18), radius=4, fill="#38BDF8")
    if progress > 0.3:
        _center(d, x1 + card_w // 2, cy, str(left_text), FH2, WHITE, max_width=card_w - 30)
    
    # Right Card (Option B - Orange/Accent)
    x2 = x1 + card_w + 40
    d.rounded_rectangle((x2, y1, x2 + card_w, y1 + sh), radius=24, fill="#2A1512", outline="#EE6C4D", width=3)
    d.rounded_rectangle((x2 + 10, y1 + 10, x2 + card_w - 10, y1 + 18), radius=4, fill="#EE6C4D")
    if progress > 0.3:
        _center(d, x2 + card_w // 2, cy, str(right_text), FH2, WHITE, max_width=card_w - 30)
        
    # VS Center Circle Pill
    if progress > 0.4:
        d.ellipse((cx - 40, cy - 40, cx + 40, cy + 40), fill="#EE6C4D", outline="#1E293B", width=4)
        d.text((cx, cy - 2), "VS", font=FL, fill=WHITE, anchor="mm")


def _layers_stack(d, cx, cy, w=480, h=260, layers=None, progress=1.0):
    s = ease_out_cubic(progress)
    if s < 0.01: return
    if not layers: layers = ["App Code", "Docker Container", "OS Kernel", "Hardware"]
    n = len(layers)
    layer_h = min(50, (h - (n - 1) * 10) // n)
    total_h = n * layer_h + (n - 1) * 10
    sy = cy - total_h // 2
    
    layer_cols = ["#1A5CFF", "#00B4D8", "#EE6C4D", "#2B2D42"]
    for i, layer in enumerate(layers):
        l_progress = min(1.0, max(0.0, (progress - i * 0.15) / 0.4))
        if l_progress < 0.01: continue
        ls = ease_out_back(l_progress)
        lw = int(w * ls)
        lx = int(cx - lw // 2)
        ly = int(sy + i * (layer_h + 10))
        col = layer_cols[i % len(layer_cols)]
        
        d.rounded_rectangle((lx, ly, lx + lw, ly + layer_h), radius=12, fill=col, outline=WHITE, width=2)
        if l_progress > 0.3:
            d.text((cx, ly + layer_h // 2), f"LAYER {i+1}: {layer.upper()}", font=FL, fill=WHITE, anchor="mm")


def _timeline_road(d, cx, cy, w=540, h=140, steps=None, progress=1.0):
    s = ease_out_cubic(progress)
    if s < 0.01: return
    if not steps: steps = ["Input", "Process", "Output"]
    n = len(steps)
    if n < 2: return
    x1, x2 = int(cx - (w // 2) * s), int(cx + (w // 2) * s)
    
    # Connecting Line
    d.line([(x1, cy), (x2, cy)], fill="#1A5CFF", width=6)
    
    # Nodes along timeline
    step_gap = (x2 - x1) / (n - 1)
    for i, step in enumerate(steps):
        node_x = int(x1 + i * step_gap)
        node_p = min(1.0, max(0.0, (progress - i * 0.18) / 0.3))
        if node_p < 0.01: continue
        
        nr = int(22 * ease_out_back(node_p))
        d.ellipse((node_x - nr, cy - nr, node_x + nr, cy + nr), fill="#0D2A3D", outline="#1A5CFF", width=4)
        if node_p > 0.3:
            d.text((node_x, cy - 1), str(i+1), font=FL, fill=WHITE, anchor="mm")
            # Step label above or below
            lbl_y = cy - 40 if i % 2 == 0 else cy + 35
            _center(d, node_x, lbl_y, str(step), FS, INK if progress < 0.5 else WHITE, max_width=120)


def _impact_callout(d, cx, cy, w=500, h=220, title="KEY TAKEAWAY", detail="Containers isolate dependencies completely.", progress=1.0):
    s = ease_out_back(progress)
    if s < 0.01: return
    sw, sh = int(w * s), int(h * s)
    if sw < 20: return
    x1, y1 = int(cx - sw // 2), int(cy - sh // 2)
    
    # Glassmorphism callout container
    d.rounded_rectangle((x1, y1, x1 + sw, y1 + sh), radius=22, fill="#0D2133", outline="#1A5CFF", width=3)
    # Top accent highlight bar
    d.rounded_rectangle((x1 + 24, y1 + 16, x1 + sw - 24, y1 + 22), radius=3, fill="#EE6C4D")
    
    if progress > 0.2:
        d.text((x1 + 32, y1 + 36), f"⚡ {str(title).upper()}", font=FH2, fill="#EE6C4D")
    if detail and progress > 0.4:
        _center(d, cx, y1 + 120, str(detail), FB, WHITE, max_width=sw - 50)


def _data_flow(d, cx, cy, w=580, h=160, input_txt="Input Data", process_txt="Process Engine", output_txt="Result Hash", progress=1.0):
    s = ease_out_cubic(progress)
    if s < 0.01: return
    sw = int(w * s)
    if sw < 30: return
    
    # 3 Node positions
    node_w = 160
    node_h = 80
    x_input = int(cx - sw // 2 + node_w // 2)
    x_process = int(cx)
    x_output = int(cx + sw // 2 - node_w // 2)
    
    # 1. Input Node Box
    p1 = min(1.0, max(0.0, progress / 0.4))
    if p1 > 0.05:
        _box(d, x_input, cy, node_w, node_h, "#0D2A3D", 14, outline="#1A5CFF", stroke=2)
        _center(d, x_input, cy, str(input_txt), FS, WHITE, max_width=node_w - 20)
        
    # 2. Arrow 1 (Input -> Process)
    p2 = min(1.0, max(0.0, (progress - 0.25) / 0.3))
    if p2 > 0.05:
        _arrow(d, x_input + node_w // 2 + 5, cy, x_process - node_w // 2 - 5, cy, fill="#1A5CFF", width=4, progress=p2)

    # 3. Process Engine Node
    p3 = min(1.0, max(0.0, (progress - 0.45) / 0.4))
    if p3 > 0.05:
        _box(d, x_process, cy, node_w, node_h, "#2A1512", 14, outline="#EE6C4D", stroke=2)
        _center(d, x_process, cy, str(process_txt), FS, WHITE, max_width=node_w - 20)

    # 4. Arrow 2 (Process -> Output)
    p4 = min(1.0, max(0.0, (progress - 0.65) / 0.3))
    if p4 > 0.05:
        _arrow(d, x_process + node_w // 2 + 5, cy, x_output - node_w // 2 - 5, cy, fill="#EE6C4D", width=4, progress=p4)

    # 5. Output Result Node
    p5 = min(1.0, max(0.0, (progress - 0.75) / 0.25))
    if p5 > 0.05:
        _box(d, x_output, cy, node_w, node_h, "#16394B", 14, outline="#55A630", stroke=2)
        _center(d, x_output, cy, str(output_txt), FS, WHITE, max_width=node_w - 20)


def _dotted_grid_bg(img, t_seconds=0.0):
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, H), fill=PAPER_BG)
    # Draw dots
    spacing = 32
    for x in range(0, W, spacing):
        for y in range(0, H, spacing):
            d.ellipse((x-1, y-1, x+1, y+1), fill="#D1D5DB")
            
    # Draw thin technical corner crop marks
    padding = 48
    mark_len = 24
    thick = 2
    # Top Left
    d.line([(padding, padding), (padding + mark_len, padding)], fill=INK, width=thick)
    d.line([(padding, padding), (padding, padding + mark_len)], fill=INK, width=thick)
    # Top Right
    d.line([(W - padding, padding), (W - padding - mark_len, padding)], fill=INK, width=thick)
    d.line([(W - padding, padding), (W - padding, padding + mark_len)], fill=INK, width=thick)
    # Bottom Left
    d.line([(padding, H - padding), (padding + mark_len, H - padding)], fill=INK, width=thick)
    d.line([(padding, H - padding), (padding, H - padding - mark_len)], fill=INK, width=thick)
    # Bottom Right
    d.line([(W - padding, H - padding), (W - padding - mark_len, H - padding)], fill=INK, width=thick)
    d.line([(W - padding, H - padding), (W - padding, H - padding - mark_len)], fill=INK, width=thick)

def _top_status_bar(d, title, counter, progress, total_scenes, brand_name="AI SIMPLIFIED LAB"):
    """Sleek minimalist header bar — height 70px, completely non-intrusive."""
    s = min(1.0, progress * 2.0)
    if s < 0.01: return
    # Base header bar
    d.rectangle((0, 0, W, 70), fill="#0F172A")
    d.line([(0, 70), (W, 70)], fill="#38BDF8", width=1)
    
    # Left Project Pill — widened to fit full AI SIMPLIFIED LAB branding perfectly
    d.rounded_rectangle((20, 15, 300, 55), radius=20, fill="#1E293B", outline="#475569", width=2)
    _circle(d, 36, 35, 6, fill="#E03188")
    _center(d, 160, 35, str(brand_name).upper(), FMONO_S, "#F8FAFC", max_width=250)
    
    # Center Scene Title
    scene_txt = str(title or "TECH BREAKDOWN").strip().upper()
    _center(d, W // 2 + 30, 35, scene_txt, FMONO_S, "#CBD5E1", max_width=380)
    
    # Right Live Step Badge
    counter_txt = f"{counter:02d}/{total_scenes:02d}"
    d.rounded_rectangle((W - 140, 15, W - 20, 55), radius=8, fill="#1E293B", outline="#475569", width=1)
    _center(d, W - 80, 35, counter_txt, FMONO_S, "#F8FAFC")

def _mac_window_frame(d, cx, cy, w, h, title, progress, bg_col=WHITE):
    """Retro/minimalist modal shell with crisp borders."""
    s = ease_out_back(progress)
    if s < 0.01: return
    sw, sh = int(w * s), int(h * s)
    x1, y1 = int(cx - sw // 2), int(cy - sh // 2)
    
    # Box shadow (crisp, solid)
    d.rounded_rectangle((x1 + 12, y1 + 12, x1 + sw + 12, y1 + sh + 12), radius=16, fill=INK)
    # Window body
    d.rounded_rectangle((x1, y1, x1 + sw, y1 + sh), radius=16, fill=bg_col, outline=INK, width=4)
    # Header
    d.line([(x1, y1 + 60), (x1 + sw, y1 + 60)], fill=INK, width=4)
    # Mac buttons
    _circle(d, x1 + 30, y1 + 30, 8, fill=RED)
    _circle(d, x1 + 60, y1 + 30, 8, fill=ORANGE)
    _circle(d, x1 + 90, y1 + 30, 8, fill=GREEN)
    
    # Title
    _center(d, cx, y1 + 30, title, FMONO_S, INK)

def _decision_card(d, cx, cy, w, h, quote, options, active_idx, score, progress):
    """Radio button / checklist fields, selection animation, probability score."""
    s = ease_out_back(progress)
    if s < 0.01: return
    sw, sh = int(w * s), int(h * s)
    _mac_window_frame(d, cx, cy, w, h, "DECISION_MATRIX", progress, bg_col=PAPER_BG)
    
    if progress > 0.3:
        # Quote / Query
        _center(d, cx, cy - h // 2 + 120, quote, FH2, INK, max_width=w-80)
        
        quote_h = _measure_text_bounds(d, quote, FH2, max_width=w-80)[1]
        
        # Options
        start_y = cy - h // 2 + 120 + quote_h / 2 + 60
        for i, opt in enumerate(options):
            y_pos = start_y + i * 80
            # Radio button
            _circle(d, cx - w//2 + 100, y_pos, 16, fill=WHITE)
            d.ellipse((cx - w//2 + 84, y_pos - 16, cx - w//2 + 116, y_pos + 16), outline=INK, width=4)
            if i == active_idx and progress > 0.6:
                _circle(d, cx - w//2 + 100, y_pos, 8, fill=ACCENT)
            
            # Text
            col = ACCENT if (i == active_idx and progress > 0.6) else INK
            d.text((cx - w//2 + 150, y_pos), opt, font=FS, fill=col, anchor="lm")
            
        # Confidence Score Pill — bottom-right corner of frame (no text overlap!)
        if progress > 0.8:
            cur_score = int(score * min(1.0, (progress - 0.8) * 5))
            score_txt = f"{cur_score}% CONFIDENCE"
            bx1 = cx + w//2 - 230
            by1 = cy + h//2 - 65
            bx2 = cx + w//2 - 20
            by2 = cy + h//2 - 15
            d.rounded_rectangle((bx1, by1, bx2, by2), radius=25, fill=GREEN)
            _center(d, (bx1 + bx2) // 2, (by1 + by2) // 2, score_txt, FMONO_S, WHITE)

def _comparison_grid(d, cx, cy, left_title, left_data, right_title, right_data, progress):
    """Split-view card with bar charts and animated diagonal red strike-through."""
    s = ease_out_back(progress)
    if s < 0.01: return
    _mac_window_frame(d, cx, cy, 900, 700, "COMPARISON_BENCHMARK", progress)
    
    if progress > 0.3:
        # Split line
        d.line([(cx, cy - 290), (cx, cy + 350)], fill=INK, width=2)
        
        # Left Side
        _center(d, cx - 225, cy - 230, left_title, FL, MUTED)
        # Right Side
        _center(d, cx + 225, cy - 230, right_title, FL, ACCENT)
        
        # Bars
        for i, (l_val, r_val) in enumerate(zip(left_data, right_data)):
            y_pos = cy - 120 + i * 120
            
            try:
                l_val_f = float(l_val)
                r_val_f = float(r_val)
            except (ValueError, TypeError):
                l_val_f, r_val_f = 0.0, 0.0
                
            # Left bar
            l_w = int(250 * (l_val_f / 100))
            d.rectangle((cx - 50 - l_w, y_pos - 20, cx - 50, y_pos + 20), fill=MUTED)
            d.text((cx - 60 - l_w, y_pos), f"{l_val}", font=FMONO_S, fill=INK, anchor="rm")
            
            # Strike through left if progress > 0.6
            if progress > 0.6:
                d.line([(cx - 300, y_pos + 30), (cx - 20, y_pos - 30)], fill=RED, width=6)
                
            # Right bar (animated grow)
            if progress > 0.5:
                ps = min(1.0, (progress - 0.5) * 2)
                r_w = int(250 * (r_val_f / 100) * ps)
                d.rectangle((cx + 50, y_pos - 20, cx + 50 + r_w, y_pos + 20), fill=GREEN)
                d.text((cx + 60 + r_w, y_pos), f"{r_val}", font=FMONO_S, fill=INK, anchor="lm")


# ── Frame renderer ───────────────────────────────────────────────────────
def render_frame(elements: list[El], frame_idx: int, total_frames: int,
                 bg_color=PAPER_BG, bg_fn=None, fps=30, t_seconds=None) -> Image.Image:
    t = frame_idx / max(total_frames - 1, 1)
    if t_seconds is None:
        t_seconds = frame_idx / fps
    img = Image.new("RGB", (W, H), bg_color)
    if bg_fn: bg_fn(img, t_seconds)
    d = ImageDraw.Draw(img)
    d.t_seconds = t_seconds

    for el in elements:
        if t < el.enter_start: continue
        if t < el.enter_end:
            raw = (t - el.enter_start) / (el.enter_end - el.enter_start)
        else:
            raw = 1.0

        easing_fn = EASINGS.get(el.easing, ease_out_cubic)
        progress = easing_fn(min(raw, 1.0))

        if not el.hold and progress >= 1.0: continue
        
        # Handle Exit Animation
        if el.exit_start is not None and t > el.exit_start:
            exit_end = min(el.exit_start + 0.25, 1.0)
            if t > exit_end: continue  # Fully exited
            exit_raw = (t - el.exit_start) / max(exit_end - el.exit_start, 0.01)
            # Reversing the progress causes it to shrink/fade out using the exact same logic!
            progress = 1.0 - easing_fn(min(exit_raw, 1.0))

        # Interpolate position
        if el.from_x is not None and el.from_y is not None:
            cx = _lerp(el.from_x, el.x, progress)
            cy = _lerp(el.from_y, el.y, progress)
        else:
            cx, cy = el.x, el.y

        if el.draw_fn:
            el.draw_fn(d, cx, cy, progress, el.data)

    return img


def make_scene_frames(elements: list[El], scene_seconds: float, fps: int = FPS,
                      intro_seconds: float = 1.0, bg_color=PAPER_BG,
                      bg_fn=None, subs=None, camera_focus=None, camera_choreography="", scene_dict=None):
    """Generate all frames for a scene with dynamic focal camera tracking."""
    from viral_template import is_editorial_template_scene, is_viral_template_scene
    _is_editorial = bool(scene_dict and is_editorial_template_scene(scene_dict))
    _is_viral = bool(scene_dict and is_viral_template_scene(scene_dict) and not _is_editorial)

    # Caption renderer selection
    if _is_viral:
        from viral_renderer import render_viral_caption as _caption_fn
        _subtitle_fn = lambda img, t: _caption_fn(img, subs, t)
    else:
        _subtitle_fn = lambda img, t: _draw_subtitles_pill(img, t)

    # Apply motion defaults
    for el in elements:
        _apply_motion(el)

    # Scale timings to intro window
    target_frames = max(1, int(round(scene_seconds * fps)))
    intro_frames = min(target_frames, max(1, int(round(intro_seconds * fps))))
    hold_frames = max(0, target_frames - intro_frames)

    scaled = []
    for el in elements:
        s = El(
            x=el.x, y=el.y,
            from_x=el.from_x, from_y=el.from_y,
            enter_start=0.0 if el.persist else el.enter_start * intro_seconds / scene_seconds,
            enter_end=0.01 if el.persist else el.enter_end * intro_seconds / scene_seconds,
            easing=el.easing, motion=el.motion,
            draw_fn=el.draw_fn, data=el.data, hold=el.hold, persist=el.persist,
            exit_start=el.exit_start, exit_motion=el.exit_motion
        )
        scaled.append(s)

    # Determine camera focal target coordinates
    grid_foci = {
        "center": (W / 2, H / 2),
        "top": (W / 2, 380),
        "bottom": (W / 2, 780),
        "left": (240, 560),
        "right": (480, 560),
        "top_left": (240, 380),
        "top_right": (480, 380),
        "bottom_left": (240, 780),
        "bottom_right": (480, 780),
    }
    
    if isinstance(camera_focus, str):
        target_fx, target_fy = grid_foci.get(camera_focus.lower(), (W / 2, H / 2))
    elif isinstance(camera_focus, (tuple, list)) and len(camera_focus) == 2:
        target_fx, target_fy = float(camera_focus[0]), float(camera_focus[1])
    else:
        # Auto-calculate focal center of key main elements (excluding subtitles/top bars)
        valid_els = [e for e in elements if 120 < e.y < 1050]
        if valid_els:
            target_fx = sum(e.x for e in valid_els) / len(valid_els)
            target_fy = sum(e.y for e in valid_els) / len(valid_els)
        else:
            target_fx, target_fy = W / 2, H / 2

    def _draw_subtitles_pill(img, t):
        if not subs: return img
        active_sub = None
        for s in subs:
            if s["start"] <= t <= s["end"]:
                active_sub = s
                break
        if not active_sub: return img
        
        text = active_sub["text"]
        words = str(text).split()
        if not words: return img

        # Intelligent Clutter Avoidance: check if elements occupy the bottom screen area (y > 1620)
        # If crowded, push captions down to y=1820 to guarantee zero overlap with foreground visual cards
        cy = 1750
        for el in elements:
            if getattr(el, "y", 0) > 1620:
                cy = 1820
                break

        txt_img = Image.new("RGBA", img.size, (0,0,0,0))
        d = ImageDraw.Draw(txt_img)
        fnt = FB

        pad_x = 32
        word_widths = [d.textlength(w, font=fnt) for w in words]
        space_w = d.textlength(" ", font=fnt)
        total_w = sum(word_widths) + space_w * (len(words) - 1)
        max_pill_w = W - 120

        sw = min(total_w + pad_x * 2, max_pill_w)
        sh = 70
        x1, y1 = int(W/2 - sw / 2), int(cy - sh / 2)

        # Soft drop shadow + crisp white pill container
        d.rounded_rectangle((x1 + 4, y1 + 6, x1 + sw + 4, y1 + sh + 6), radius=20, fill=(0, 0, 0, 25))
        d.rounded_rectangle((x1, y1, x1 + sw, y1 + sh), radius=20, fill="#FFFFFF", outline="#18181B", width=2)

        # Determine active word index based on time progress in subtitle segment
        duration = max(active_sub["end"] - active_sub["start"], 0.1)
        progress_t = max(0.0, min(1.0, (t - active_sub["start"]) / duration))
        active_word_idx = min(int(progress_t * len(words)), len(words) - 1)

        # Render words with yellow highlight box behind active word
        curr_x = W/2 - total_w / 2
        for idx, (w_str, w_width) in enumerate(zip(words, word_widths)):
            if idx == active_word_idx:
                hx1 = curr_x - 4
                hy1 = cy - 18
                hx2 = curr_x + w_width + 4
                hy2 = cy + 18
                d.rounded_rectangle((hx1, hy1, hx2, hy2), radius=6, fill="#FDE047")
                d.text((curr_x, cy), w_str, font=fnt, fill="#18181B", anchor="lm")
            else:
                d.text((curr_x, cy), w_str, font=fnt, fill="#334155", anchor="lm")
            curr_x += w_width + space_w

        return Image.alpha_composite(img.convert("RGBA"), txt_img).convert("RGB")

    # Dynamic Camera Choreography parsing
    camera_choreography = str(camera_choreography).lower()
    if _is_editorial:
        render_plan = (scene_dict or {}).get("render_plan") or {}
        camera_plan = render_plan.get("camera") or {}
        camera_behavior = str(camera_plan.get("behavior", "static")).lower()
        cam_zoom_dir = -1.0 if camera_behavior in {"pull_back", "zoom_out"} else 1.0
        cam_zoom_amt = {
            "push_in": 0.12,
            "slow_push": 0.12,
            "pull_back": 0.10,
            "zoom_out": 0.10,
            "focus_shift": 0.06,
            "detail_zoom": 0.08,
            "tight_zoom": 0.12,
            "horizontal_tracking": 0.04,
            "side_swap": 0.04,
        }.get(camera_behavior, 0.0)
        cam_pan_weight = 0.40 if camera_behavior == "horizontal_tracking" else (0.25 if camera_behavior in {"focus_shift", "pan_left", "pan_right", "side_swap"} else 0.0)
    elif _is_viral:
        from viral_template import (
            ROLE_CAMERA_PRESETS, CAMERA_PUSH, CAMERA_PULL, CAMERA_SWEEP_LEFT,
            CAMERA_SWEEP_RIGHT, CAMERA_FOCUS, CAMERA_IMPACT, CAMERA_STATIC,
        )
        v_role = str((scene_dict or {}).get("role", "hook")).lower()
        v_preset = ROLE_CAMERA_PRESETS.get(v_role, CAMERA_PUSH)
        if v_preset == CAMERA_PUSH:
            cam_zoom_dir = 1.0; cam_zoom_amt = 0.035; cam_pan_weight = 0.15
        elif v_preset == CAMERA_PULL:
            cam_zoom_dir = -1.0; cam_zoom_amt = 0.035; cam_pan_weight = 0.15
        elif v_preset == CAMERA_SWEEP_LEFT:
            cam_zoom_dir = 1.0; cam_zoom_amt = 0.02; cam_pan_weight = -0.40
        elif v_preset == CAMERA_SWEEP_RIGHT:
            cam_zoom_dir = 1.0; cam_zoom_amt = 0.02; cam_pan_weight = 0.40
        elif v_preset == CAMERA_FOCUS:
            cam_zoom_dir = 1.0; cam_zoom_amt = 0.045; cam_pan_weight = 0.25
        elif v_preset == CAMERA_IMPACT:
            cam_zoom_dir = 1.0; cam_zoom_amt = 0.055; cam_pan_weight = 0.10
        else: # CAMERA_STATIC
            cam_zoom_dir = 1.0; cam_zoom_amt = 0.0; cam_pan_weight = 0.0
    else:
        cam_zoom_dir = -1.0 if "zoom out" in camera_choreography or "pull back" in camera_choreography else 1.0
        cam_zoom_amt = 0.05 if "fast" in camera_choreography or "quick" in camera_choreography else 0.02
        if "static" in camera_choreography or "still" in camera_choreography:
            cam_zoom_amt = 0.0
        cam_pan_weight = 0.8 if "pan" in camera_choreography or "track" in camera_choreography else 0.35

    def _apply_camera(img, t_seconds):
        t_norm = min(1.0, max(0.0, t_seconds / max(scene_seconds, 0.1)))
        eased_t = ease_in_out_quad(t_norm)
        
        # Dynamic cinematic zoom
        if cam_zoom_dir > 0:
            zoom = 1.0 + cam_zoom_amt * eased_t
        else:
            zoom = (1.0 + cam_zoom_amt) - (cam_zoom_amt * eased_t)
            
        # Smoothly shift camera viewport toward target focus based on choreography
        cur_fx = _lerp(W / 2, target_fx, eased_t * cam_pan_weight)
        cur_fy = _lerp(H / 2, target_fy, eased_t * 0.35)
        
        if abs(zoom - 1.0) < 0.002:
            return img

        nw, nh = int(W * zoom), int(H * zoom)
        res = img.resize((nw, nh), Image.BILINEAR)
        
        # Crop around scaled focal point
        scaled_cx = cur_fx * zoom
        scaled_cy = cur_fy * zoom
        crop_x1 = max(0, min(nw - W, int(scaled_cx - W / 2)))
        crop_y1 = max(0, min(nh - H, int(scaled_cy - H / 2)))
        
        return res.crop((crop_x1, crop_y1, crop_x1 + W, crop_y1 + H))

    for i in range(intro_frames):
        t_sec = i / fps
        img = render_frame(scaled, i, intro_frames, bg_color, bg_fn, fps=fps, t_seconds=t_sec)
        img = _apply_camera(img, t_sec)
        yield _subtitle_fn(img, t_sec)

    for i in range(hold_frames):
        t_sec = (intro_frames + i) / fps
        # Re-render the frame for animated background micro-motion
        img = render_frame(scaled, intro_frames - 1, intro_frames, bg_color, bg_fn, fps=fps, t_seconds=t_sec)
        img = _apply_camera(img, t_sec)
        yield _subtitle_fn(img, t_sec)


# ══════════════════════════════════════════════════════════════════════════
# SCENE BUILDERS
# ══════════════════════════════════════════════════════════════════════════



def _draw_subscribe_card(d, cx, cy, progress):
    """Ultra-premium YouTube Subscribe CTA Card with hand click animation & glowing badges."""
    s = ease_out_back(min(1.0, progress * 1.5))
    if s < 0.01: return

    # Force center placement if default is off-center
    cx = W // 2
    cy = H // 2 - 20

    # ── Top Hero Badge ──
    if progress > 0.15:
        top_s = ease_out_cubic(min(1.0, (progress - 0.15) * 3.0))
        d.rounded_rectangle((cx - 210, cy - 180, cx + 210, cy - 120), radius=30, fill="#1E293B", outline="#38BDF8", width=2)
        _center(d, cx, cy - 150, "⚡ JOIN THE AI REVOLUTION", FMONO_S, "#F8FAFC")

    # ── Main Subscribe Glassmorphic Card (Redesigned Centered) ──
    CW, CH = 640, 520
    cw, ch = int(CW * s), int(CH * s)
    if cw < 20 or ch < 20: return

    buf = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    db = ImageDraw.Draw(buf)

    # Premium dark glass card with brand accents
    db.rounded_rectangle((0, 0, CW, CH), radius=48, fill="#0F172ACC", outline="#7C5CFF88", width=4)
    db.rounded_rectangle((4, 4, CW-4, CH-4), radius=44, outline="#00D9FF33", width=2)

    # Brand mark / avatar
    AX, AY, AR = CW // 2, 140, 64
    db.ellipse((AX-AR-6, AY-AR-6, AX+AR+6, AY+AR+6), fill="#7C5CFF")
    db.ellipse((AX-AR, AY-AR, AX+AR, AY+AR), fill="#1E293B")
    db.text((AX, AY), "AI", font=FL, fill="#FFFFFF", anchor="mm")

    # Channel Name & Main CTA phrase
    NAME_Y = AY + AR + 40
    db.text((CW // 2, NAME_Y), "AI SIMPLIFIED LAB", font=FL, fill="#FFFFFF", anchor="mm")
    db.text((CW // 2, NAME_Y + 45), "Subscribe to AI Simplified Lab", font=FS, fill="#D9EEFF", anchor="mm")

    # Subscribe Button (Centered at bottom)
    BTN_W, BTN_H = 320, 72
    BTN_CX = CW // 2
    BTN_CY = CH - 100

    is_clicked = progress >= 0.52
    if is_clicked:
        bx = BTN_CX - BTN_W // 2
        by = BTN_CY - BTN_H // 2
        db.rounded_rectangle((bx, by, bx + BTN_W, by + BTN_H), radius=36, fill="#7C5CFF")
        db.text((BTN_CX, BTN_CY), "SUBSCRIBE", font=FL, fill="#FFFFFF", anchor="mm")
    else:
        press = 0.92 if 0.45 < progress < 0.52 else 1.0
        bw = int(BTN_W * press); bh = int(BTN_H * press)
        bx = BTN_CX - bw // 2
        by = BTN_CY - bh // 2
        db.rounded_rectangle((bx, by, bx + bw, by + bh), radius=36, fill="#00D9FF")
        db.text((BTN_CX, BTN_CY), "SUBSCRIBE", font=FL, fill="#0B1020", anchor="mm")

    # Paste Card Buffer
    resized = buf.resize((cw, ch), Image.LANCZOS)
    x1, y1 = int(cx - cw / 2), int(cy - ch / 2)
    d._image.paste(resized, (x1, y1), resized)

    # ── Bottom CTA Callout Pill (High Contrast) ──
    if progress > 0.40:
        bot_s = ease_out_cubic(min(1.0, (progress - 0.40) * 2.5))
        py_center = cy + 290
        d.rounded_rectangle((cx - 260, py_center - 32, cx + 260, py_center + 32), radius=32, fill="#7C5CFF", outline="#00D9FF", width=2)
        _center(d, cx, py_center, "Subscribe to AI Simplified Lab", FL, "#FFFFFF")

    # ── Hand Pointer Cursor ──
    if progress > 0.22:
        scale_x = cw / CW
        scale_y = ch / CH
        # Target the center of the subscribe button inside the card
        btn_mx = x1 + int(BTN_CX * scale_x)
        btn_my = y1 + int(BTN_CY * scale_y)

        if progress < 0.52:
            t = ease_out_cubic((progress - 0.22) / 0.30)
            hx = _lerp(cx + 400, btn_mx, t)
            hy = _lerp(cy + 500, btn_my, t)
            c_scale = 1.6
        else:
            t = ease_out_cubic(min(1.0, (progress - 0.52) / 0.48))
            hx = _lerp(btn_mx, cx + 400, t)
            hy = _lerp(btn_my, cy + 500, t)
            c_scale = max(1.0, 1.6 - 0.6 * t)
            
        shrink = 0.85 if 0.45 < progress < 0.55 else 1.0
        _draw_hand_pointer(d, int(hx), int(hy), scale=c_scale * shrink)


def _ui_card(d, cx, cy, w, h, progress):
    """A pristine glassmorphic white card with a subtle drop shadow."""
    s = ease_out_back(progress)
    if s < 0.01: return
    sw, sh = int(w * s), int(h * s)
    if sw < 10 or sh < 10: return
    x1, y1 = int(cx - sw // 2), int(cy - sh // 2)
    # Drop shadow
    d.rounded_rectangle((x1 + 4, y1 + 12, x1 + sw + 4, y1 + sh + 12), radius=16, fill=(0, 0, 0, 12))
    # Main card
    d.rounded_rectangle((x1, y1, x1 + sw, y1 + sh), radius=16, fill="#FFFFFF", outline="#F0EFEA", width=1)

def _tech_header(d, cx, cy, title, lesson_num, progress):
    """Masterclass style typography header."""
    s = ease_out_cubic(progress)
    if s < 0.05: return
    
    # We simulate a bold elegant serif by using FH1, but we can draw it cleanly
    if s > 0.3:
        _center(d, cx, cy, title, FBIG, INK, max_width=W-80)

def _progress_bar(d, cx, cy, w, h, p_fill, left_txt, right_txt, value_txt, progress):
    """Sleek pill-shaped progress bar that fills up."""
    s = ease_out_back(progress)
    if s < 0.01: return
    sw, sh = int(w * s), int(h * s)
    if sw < 10: return
    x1, y1 = int(cx - sw // 2), int(cy - sh // 2)
    
    # Background track
    d.rounded_rectangle((x1, y1, x1 + sw, y1 + sh), radius=sh//2, fill="#F0EFEA")
    
    try:
        p_fill_f = float(p_fill)
    except (ValueError, TypeError):
        p_fill_f = 0.5
        
    # Filled track
    fill_w = int(sw * p_fill_f * min(1.0, progress * 1.2))
    if fill_w > sh:
        d.rounded_rectangle((x1, y1, x1 + fill_w, y1 + sh), radius=sh//2, fill="#E76F51")
        
    # Labels
    if progress > 0.4:
        if left_txt:
            d.text((x1, y1 - 25), left_txt, font=FS, fill=INK, anchor="lm")
        if right_txt:
            d.text((x1 + sw, y1 - 25), right_txt, font=FS, fill=MUTED, anchor="rm")
        if value_txt:
            d.text((x1 + sw + 15, cy), value_txt, font=FB, fill=INK, anchor="lm")

def _dial(d, cx, cy, radius, value, label, progress):
    """Interactive curved gauge / knob."""
    s = ease_out_back(progress)
    if s < 0.01: return
    r = int(radius * s)
    if r < 5: return
    
    x1, y1 = cx - r, cy - r
    x2, y2 = cx + r, cy + r
    
    # Background arc (135 deg to 405 deg)
    d.arc((x1, y1, x2, y2), start=135, end=405, fill="#F0EFEA", width=max(4, r//4))
    
    try:
        value_f = float(value)
    except (ValueError, TypeError):
        value_f = 0.5
        
    # Filled arc
    fill_angle = 135 + int(270 * value_f * min(1.0, progress * 1.5))
    if fill_angle > 135:
        d.arc((x1, y1, x2, y2), start=135, end=fill_angle, fill="#E76F51", width=max(4, r//4))
        
    # Inner knob
    d.ellipse((cx - r//2, cy - r//2, cx + r//2, cy + r//2), fill="#FFFFFF", outline="#F0EFEA", width=2)
    
    # Label
    if progress > 0.5:
        d.text((cx, cy + r + 25), label, font=FS, fill=MUTED, anchor="mm")

def _token_list(d, cx, cy, w, h, tokens, active_idx, progress):
    """Horizontal pill toggle group."""
    s = ease_out_back(progress)
    if s < 0.01: return
    sw, sh = int(w * s), int(h * s)
    if sw < 10: return
    x1, y1 = int(cx - sw // 2), int(cy - sh // 2)
    
    # Container
    d.rounded_rectangle((x1, y1, x1 + sw, y1 + sh), radius=12, fill="#1A1A1A")
    
    if not tokens: return
    
    token_w = sw / len(tokens)
    for i, tok in enumerate(tokens):
        tx = x1 + i * token_w
        # Highlight active
        if i == active_idx and progress > 0.4:
            d.rounded_rectangle((tx + 4, y1 + 4, tx + token_w - 4, y1 + sh - 4), radius=8, fill="#E76F51")
        
        if progress > 0.2:
            col = "#FFFFFF" if i == active_idx else "#888888"
            d.text((tx + token_w/2, cy), tok, font=FB, fill=col, anchor="mm")

def custom(scene, idx, total):
    """Smart Grid System: AI explicitly requests elements and grid positions.
    Storyboard schema:
    {
        "kind": "custom",
        "bg_color": "PAPER_BG" | "DARK",
        "elements": [...]
    }
    """
    from viral_template import is_viral_template_scene
    if is_viral_template_scene(scene):
        raise RuntimeError("ERROR: viral job accidentally entered legacy renderer custom()")

    elements_json = scene.get("elements") or []
    v_scene = scene.get("visual_scene")
    if v_scene and isinstance(v_scene, dict) and v_scene.get("objects"):
        elements_json = v_scene.get("objects")
        if "visual_concept" in v_scene:
            print(f"  -> Rendering [{v_scene.get('render_strategy', 'hybrid')}]: {v_scene['visual_concept'][:50]}...")
    
    grid = {
        "top": (W/2, 250),
        "center": (W/2, 550),
        "bottom": (W/2, 850),
        "left": (160, 550),
        "right": (560, 550),
        "top_left": (160, 250),
        "top_right": (560, 250),
        "bottom_left": (160, 850),
        "bottom_right": (560, 850),
    }
    
    colors = {
        "INK": INK,
        "WHITE": WHITE,
        "MUTED": MUTED,
        "ACCENT": ACCENT,
        "ORANGE": ORANGE,
        "RED": RED,
        "GREEN": GREEN
    }
    
    fonts = {
        "FH1": FH1,
        "FH2": FH2,
        "FB": FB,
        "FMASS": FMASS,
        "FT": FT
    }
    
    bg_choice = scene.get("bg_color", "DARK")
    if bg_choice == "DARK":
        bg_col = DARK
        bg_fn = _dotted_grid_bg
        default_ink = WHITE
        default_muted = "#8CA4B3"
    elif bg_choice == "TECH_INTERN":
        bg_col = PAPER_BG
        bg_fn = _dotted_grid_bg
        default_ink = INK
        default_muted = MUTED
    else:
        bg_col = PAPER_BG
        bg_fn = _dotted_grid_bg
        default_ink = INK
        default_muted = MUTED
        
    # Dynamic Floating Particles Background
    unique_emojis = list(set([e.get("emoji") for e in elements_json if e.get("emoji")]))
    if unique_emojis:
        from asset_manager import get_highres_emoji
        import random
        rng = random.Random(idx)
        preloaded_particles = []
        for i in range(6):
            em = unique_emojis[i % len(unique_emojis)]
            path = get_highres_emoji(em)
            if path and path.exists():
                try:
                    icn = Image.open(path).convert("RGBA")
                    size = rng.randint(48, 72)
                    icn = icn.resize((size, size), Image.LANCZOS)
                    # Soft ambient particle opacity (6%) so it never clashes with or obscures foreground text
                    alpha = icn.split()[3].point(lambda a: a * 0.06)
                    icn.putalpha(alpha)
                    # Float predominantly in the peripheral margins (left or right third)
                    start_x = rng.choice([rng.randint(30, 160), rng.randint(W - 180, W - 40)])
                    start_y = rng.randint(100, H - 200)
                    phase = rng.uniform(0, math.pi * 2)
                    speed = rng.uniform(20, 40)
                    preloaded_particles.append((icn, start_x, start_y, phase, speed))
                except Exception:
                    pass
        
        if preloaded_particles:
            base_bg = bg_fn
            def _particle_bg(img, t_seconds=0.0):
                base_bg(img, t_seconds)
                for icn, sx, sy, phase, speed in preloaded_particles:
                    drift_x = math.sin(t_seconds * math.pi * 0.5 + phase) * 40
                    drift_y = -t_seconds * speed
                    curr_x = int((sx + drift_x) % (W - 60))
                    curr_y = int((sy + drift_y) % (H - 200) + 100)
                    img.paste(icn, (curr_x, curr_y), icn)
            bg_fn = _particle_bg
    
    raw_title = scene.get("title") or scene.get("heading") or ""
    if not raw_title:
        narration_words = str(scene.get("narration", "")).strip().split()
        raw_title = " ".join(narration_words[:3]).upper() if narration_words else f"SCENE {idx+1}"
    scene_title = str(raw_title).strip()[:28].upper()
    scene_num = idx + 1

    out_els = [
        El(x=W/2, y=35, enter_start=0.0, enter_end=0.05, motion="fade", hold=True, persist=True,
           draw_fn=lambda d,x,y,p,_, title=scene_title, num=scene_num, tot=total: _top_status_bar(d, title, num, p, tot))
    ]

    # --- ZERO-OBJECT FALLBACK ENGINE ---
    # Disabled per user request to force creativity and not fallback to anything.
    if not elements_json:
        raise RuntimeError("Scene has no elements! Bailing out instead of using a fallback layout.")

    # --- SEQUENCE & MOTION DIRECTOR OPTIMIZATION ---
    from sequence_director import optimize_scene_sequence
    elements_json = optimize_scene_sequence(elements_json, scene_title)
    
    from vo_composition_agent import arrange_scene_layout
    elements_json = arrange_scene_layout(elements_json, scene_title=scene_title)



    seen_positions = {}
    parsed_coords = {} # Store resolved coordinates by ID or type for relative positioning
    
    # --- AUTO-LAYOUT STACKING ENGINE ---
    # Intercept clustered components and space them vertically across the full canvas
    center_els = [e for e in elements_json if "y" not in e and e.get("position", "center") == "center" and not e.get("spatial_relationship")]
    if len(center_els) > 1:
        # Use 75% of canvas height for stacking, centred vertically
        total_stack_height = int(H * 0.75)
        spacing = min(total_stack_height // len(center_els), 400)
        start_y = 0.5 - ((len(center_els) - 1) * spacing / 2) / H
        for i, ce in enumerate(center_els):
            ce["y"] = max(0.07, min(0.93, start_y + (i * spacing / H)))
    
    for i, e in enumerate(elements_json):
        start_len = len(out_els)
        typ = e.get("type", "text")
        el_id = e.get("id", str(typ) + str(i))
        depth = float(e.get("depth", 1.0))
        rotation = float(e.get("rotation", 0.0))
        scale = float(e.get("scale", 1.0))
        
        # --- PROCEDURAL SPATIAL COMPOSITOR ---
        spatial = e.get("spatial_relationship", e.get("position", "center")).strip().lower()
        relative_to = str(e.get("relative_to", "")).strip()
        
        # 1. Base inference
        cx, cy = grid["center"]
        if spatial.startswith("legacy_grid:"):
            pos = spatial.replace("legacy_grid:", "")
            cx, cy = grid.get(pos, grid["center"])
        else:
            if "left" in spatial: cx = W/4
            if "right" in spatial: cx = W*0.75
            if "top" in spatial: cy = 250
            if "bottom" in spatial: cy = 800
            if "above" in spatial: cy -= 150
            if "below" in spatial: cy += 150

        # 2. Relative anchoring
        if relative_to and relative_to in parsed_coords:
            anchor_x, anchor_y = parsed_coords[relative_to]
            if "above" in spatial: cy = anchor_y - 200
            elif "below" in spatial: cy = anchor_y + 200
            elif "left" in spatial: cx = anchor_x - 300
            elif "right" in spatial: cx = anchor_x + 300
            else: cx, cy = anchor_x, anchor_y
            
        # 3. Explicit normalized coordinates (Overrides all)
        if "x" in e and isinstance(e["x"], (int, float)): cx = float(e["x"]) * W
        if "y" in e and isinstance(e["y"], (int, float)): cy = float(e["y"]) * H
        
        # Apply offsets
        cx += float(e.get("offset_x", 0))
        cy += float(e.get("offset_y", 0))
        
        # Clamp to keep elements inside vertical canvas bounds (leave 80px padding top/bottom)
        cy = max(80, min(H - 80, cy))
        
        parsed_coords[el_id] = (cx, cy)
        parsed_coords[typ] = (cx, cy)
        
        text = e.get("text", "").strip()
        if not text and typ not in ("text", "custom", "box", "circle"):
            text = str(typ).replace("_", " ").title()
            
        fnt = fonts.get(e.get("font", "FB"), FB)
        
        c_name = e.get("color", "INK")
        if c_name == "INK" and bg_choice == "DARK": color = default_ink
        elif c_name == "MUTED" and bg_choice == "DARK": color = default_muted
        elif c_name == "WHITE" and bg_choice == "PAPER_BG": color = INK
        else: color = colors.get(c_name, default_ink)
        
        start = float(e.get("enter_start", 0.05 if i == 0 else 0.15))
        if i == 0 and start > 0.05: start = 0.02
        
        if spatial.startswith("legacy_grid:") and "top" in spatial: cy -= 50

        end_t = min(1.0, start+0.3)
        
        # --- PROCEDURAL MOTION TRACK COMPOSITOR ---
        motion_track = e.get("motion_track", e.get("motion", "slide_up" if typ == "text" else "pop"))
        if motion_track.startswith("legacy_motion:"):
            motion = motion_track.replace("legacy_motion:", "")
        else:
            motion = motion_track
                
        easing = e.get("easing", "ease_out_back")
        if e.get("persist", False):
            end_t = 0.01
            motion = "fade"

        if typ == "text":
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion, easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, t=text, f=fnt, c=color: _center(d, x, y, t, f, c)))
        elif typ == "tech_header":
            lesson = e.get("lesson_num", "01")
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, t=text, l=lesson: _tech_header(d, x, y, t, l, p if not e.get("persist") else 1.0)))
        elif typ == "ui_card":
            cw = float(e.get("width", 0.6)) * W
            def _draw_dyn_ui_card(d, x, y, p, _, cw=cw, t=text, f=fnt, c=color, persist=e.get("persist", False)):
                actual_h = _measure_text_bounds(d, t, f, max_width=max(10, cw - 40))[1] + 80 if t else float(e.get("height", 0.2)) * H
                prog = p if not persist else 1.0
                _ui_card(d, x, y, cw, actual_h, prog)
                if t: _center(d, x, y, t, f, c, max_width=max(10, cw - 40))
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=_draw_dyn_ui_card))
        elif typ == "mac_window":
            cw = float(e.get("width", 0.8)) * W
            w_title = e.get("title", text)
            def _draw_dyn_mac_window(d, x, y, p, _, cw=cw, t=w_title, persist=e.get("persist", False)):
                actual_h = _measure_text_bounds(d, t, FL, max_width=max(10, cw - 60))[1] + 120 if t else float(e.get("height", 0.6)) * H
                prog = p if not persist else 1.0
                _mac_window_frame(d, x, y, cw, actual_h, t, prog)
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=_draw_dyn_mac_window))
        elif typ == "decision_card":
            cw = float(e.get("width", 0.7)) * W
            quote_txt = e.get("quote", text)
            opts = e.get("options", ["Option A", "Option B", "Option C"])
            active_i = int(e.get("active_index", 0))
            score = float(e.get("score", 95))
            def _draw_dyn_decision(d, x, y, p, _, cw=cw, q=quote_txt, o=opts, ai=active_i, s=score, persist=e.get("persist", False)):
                quote_h = _measure_text_bounds(d, q, FH2, max_width=cw-80)[1]
                actual_h = quote_h + len(o) * 80 + 200
                prog = p if not persist else 1.0
                _decision_card(d, x, y, cw, actual_h, q, o, ai, s, prog)
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=_draw_dyn_decision))
        elif typ == "comparison_grid":
            l_title = e.get("left_title", "Before")
            r_title = e.get("right_title", "After")
            l_data = e.get("left_data", [80, 60, 90])
            r_data = e.get("right_data", [20, 40, 10])
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, lt=l_title, rt=r_title, ld=l_data, rd=r_data: _comparison_grid(d, x, y, lt, ld, rt, rd, p if not e.get("persist") else 1.0)))
        elif typ == "progress_bar":
            cw = float(e.get("width", 0.6)) * W
            ch = float(e.get("height", 0.05)) * H
            fill_p = float(e.get("fill_percentage", 0.6))
            lt = e.get("left_text", "")
            rt = e.get("right_text", "")
            vt = e.get("value_text", f"{int(fill_p*100)}%")
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, cw=cw, ch=ch, fp=fill_p, lt=lt, rt=rt, vt=vt: _progress_bar(d, x, y, cw, ch, fp, lt, rt, vt, p if not e.get("persist") else 1.0)))
        elif typ == "dial":
            r = float(e.get("radius", 60))
            val = float(e.get("value", 0.5))
            lbl = e.get("label", text)
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, r=r, v=val, l=lbl: _dial(d, x, y, r, v, l, p if not e.get("persist") else 1.0)))
        elif typ == "token_list":
            cw = float(e.get("width", 0.6)) * W
            ch = float(e.get("height", 0.08)) * H
            toks = e.get("tokens", ["Token1", "Token2", "Token3"])
            a_idx = int(e.get("active_index", 0))
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, cw=cw, ch=ch, toks=toks, a=a_idx: _token_list(d, x, y, cw, ch, toks, a, p if not e.get("persist") else 1.0)))
        elif typ == "icon":
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, t=text, c=color: _pop(d, x, y, t, FMASS, c, p) if not e.get("persist") else _center(d, x, y, t, FMASS, c)))
        elif typ == "box":
            t_str = str(text).strip()
            if not t_str:
                # Never draw an empty box without text!
                continue
            box_bg = "#0D2A3D" if bg_choice == "DARK" else ("#FFF0E7" if color == ACCENT else "#E8F0F2")
            box_stroke = ACCENT if color == ACCENT else BRAND_BLUE
            
            def _draw_text_box(d, x, y, p, _):
                s = ease_out_back(p) if not e.get("persist") else 1.0
                if s < 0.01: return
                # Calculate dynamic width/height from measured text bounds to prevent text scattering
                line_w = min(640, max(420, int(float(e.get("width", 0.80)) * W)))
                tw_m, th_m = _measure_text_bounds(d, t_str, FH2, max_width=line_w - 60)
                bw = int(max(380, tw_m + 60) * s)
                bh = int(max(130, th_m + 50) * s)
                if bw < 10 or bh < 10: return
                x1, y1 = int(x - bw // 2), int(y - bh // 2)
                d.rounded_rectangle((x1, y1, x1 + bw, y1 + bh), radius=int(20 * s), fill=box_bg, outline=box_stroke, width=2)
                if p > 0.3 or e.get("persist"):
                    _center(d, x, y, t_str, FH2, WHITE if bg_choice == "DARK" else INK, max_width=bw - 40)
                    
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=_draw_text_box))

        elif typ in ("subscribe", "subscribe_card", "outro_card"):
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_: _draw_subscribe_card(d, x, y, p)))
        elif typ == "arrow":
            from_pos = e.get("from", "left")
            to_pos = e.get("to", "right")
            
            # Check for explicit normalized coordinates first
            if "from_x" in e and "from_y" in e:
                fx, fy = float(e["from_x"]) * W, float(e["from_y"]) * H
            elif len(out_els) > start_len:
                # Link from preceding element center
                fx, fy = out_els[-1].x, out_els[-1].y
            else:
                fx, fy = grid.get(from_pos, grid["left"])
                
            if "to_x" in e and "to_y" in e:
                tx, ty = float(e["to_x"]) * W, float(e["to_y"]) * H
            elif i + 1 < len(elements_json) and "y" in elements_json[i+1]:
                # Link to succeeding element center
                next_e = elements_json[i+1]
                tx = float(next_e.get("x", 0.5)) * W
                ty = float(next_e.get("y", 0.5)) * H
            else:
                tx, ty = grid.get(to_pos, grid["right"])
            
            # Use 360-degree trig to dynamically shorten the arrow by 120px from BOTH ends
            # so it connects perfectly to the edge of the elements without piercing them.
            dist = math.hypot(tx - fx, ty - fy)
            if dist > 240:
                angle = math.atan2(ty - fy, tx - fx)
                fx += 120 * math.cos(angle)
                fy += 120 * math.sin(angle)
                tx -= 120 * math.cos(angle)
                ty -= 120 * math.sin(angle)
                
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion="draw_line" if not e.get("persist") else "fade", persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, c=color, fx=fx, fy=fy, tx=tx, ty=ty: _arrow(d, fx, fy, tx, ty, c, 5, p if not e.get("persist") else 1.0)))
        elif typ == "server":
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, c=color, t=text, f=fnt, c_txt=default_ink: (_server_icon(d, x, y, 100, 120, c, p if not e.get("persist") else 1.0), _center(d, x, y+90, t, f, c_txt))))
        elif typ == "database":
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, c=color, t=text, f=fnt, c_txt=default_ink: (_db_icon(d, x, y, 80, 100, c, p if not e.get("persist") else 1.0), _center(d, x, y+90, t, f, c_txt))))
        elif typ == "cloud":
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, c=color, t=text, f=fnt, c_txt=WHITE: (_cloud_icon(d, x, y, 120, c, p if not e.get("persist") else 1.0), _center(d, x, y+40, t, f, c_txt))))
        elif typ == "smartphone":
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, c=color, t=text, f=fnt, c_txt=default_ink: (_smartphone_icon(d, x, y, 70, 140, c, p if not e.get("persist") else 1.0), _center(d, x, y+100, t, f, c_txt))))
        elif typ in ("ai_icon", "icon", "emoji"):
            emoji_char = e.get("emoji")
            icon_path = None
            
            if emoji_char:
                from asset_manager import get_highres_emoji
                icon_path = get_highres_emoji(emoji_char)
                
            if not icon_path:
                prompt_str = e.get("prompt", "generic icon")
                fname = e.get("filename", "icon_default")
                from asset_manager import get_or_create_ai_icon
                icon_path = get_or_create_ai_icon(prompt_str, fname)
            
            base_icon_img = None
            if icon_path and icon_path.exists():
                try:
                    base_icon_img = Image.open(icon_path).convert("RGBA")
                except Exception:
                    base_icon_img = None
            
            def _draw_ai_icon(d, x, y, p, _d, icn_img=base_icon_img, t=text, f=fnt, c=color):
                s = ease_out_back(p)
                if s < 0.05 or not icn_img: return
                try:
                    iw, ih = int(icn_img.width * s), int(icn_img.height * s)
                    if iw < 5 or ih < 5: return
                    resized = icn_img.resize((iw, ih), Image.LANCZOS)
                    d._image.paste(resized, (int(x - iw // 2), int(y - ih // 2)), resized)
                    if t and (p > 0.3 or e.get("persist")):
                        _center(d, x, y + ih // 2 + 25, t, f, c)
                except Exception:
                    pass
                    
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_: _draw_ai_icon(d, x, y, p if not e.get("persist") else 1.0, _)))
        elif typ in ("terminal", "code", "code_block"):
            code_lines = e.get("lines") or text
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, c=color, cl=code_lines, t=text: _terminal_window(d, x, y, 480, 240, t or "bash", cl, p if not e.get("persist") else 1.0)))
        elif typ in ("metric", "stat", "counter"):
            val = e.get("value") or e.get("text") or "99.9%"
            if str(val).lower() in ("none", "null", ""):
                val = "99.9%"
            lbl = e.get("label") or e.get("subtext") or "METRIC"
            if str(lbl).lower() in ("none", "null", ""):
                lbl = "METRIC"
            sub = e.get("subtext", "") if e.get("label") else ""
            if str(sub).lower() in ("none", "null"):
                sub = ""
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, c=color, v=val, l=lbl, s=sub: _metric_card(d, x, y, 340, 180, v, l, s, c, p if not e.get("persist") else 1.0)))
        elif typ in ("badge", "pill"):
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, c=color, t=text: _badge(d, x, y, t or "⚡ HIGHLIGHT", c, p if not e.get("persist") else 1.0)))
        elif typ in ("vs_card", "vs", "comparison_card"):
            left = e.get("left", e.get("option_a", "Option A"))
            right = e.get("right", e.get("option_b", "Option B"))
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, l=left, r=right: _vs_card(d, x, y, 480, 220, l, r, p if not e.get("persist") else 1.0)))
        elif typ in ("layers_stack", "layers", "architecture"):
            lyrs = e.get("layers") or [l.strip() for l in text.split(",") if l.strip()] or ["App", "Container", "Kernel", "OS"]
            lw = int(float(e.get("width", 0.85)) * W)
            lh = int(float(e.get("height", 0.16)) * H)
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, lyrs=lyrs, lw=lw, lh=lh: _layers_stack(d, x, y, lw, lh, lyrs, p if not e.get("persist") else 1.0)))
        elif typ in ("timeline_road", "timeline", "pipeline", "process_steps"):
            stps = e.get("steps") or [s.strip() for s in text.split(",") if s.strip()] or ["Input", "Process", "Output"]
            tw = int(float(e.get("width", 0.88)) * W)
            th = int(float(e.get("height", 0.075)) * H)
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, stps=stps, tw=tw, th=th: _timeline_road(d, x, y, tw, th, stps, p if not e.get("persist") else 1.0)))
        elif typ in ("impact_callout", "callout", "takeaway", "key_point"):
            t_hdr = e.get("title", e.get("heading", "KEY TAKEAWAY"))
            t_det = e.get("detail", text)
            iw = int(float(e.get("width", 0.82)) * W)
            ih = int(float(e.get("height", 0.13)) * H)
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, th=t_hdr, td=t_det, iw=iw, ih=ih: _impact_callout(d, x, y, iw, ih, th, td, p if not e.get("persist") else 1.0)))
        elif typ in ("data_flow", "hash_flow", "pipeline_flow", "flow_diagram"):
            inp = e.get("input", e.get("left", "Input"))
            prc = e.get("process", e.get("center", "Engine"))
            out = e.get("output", e.get("right", "Output"))
            dfw = int(float(e.get("width", 0.85)) * W)
            dfh = int(float(e.get("height", 0.09)) * H)
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, i=inp, pr=prc, o=out, dfw=dfw, dfh=dfh: _data_flow(d, x, y, dfw, dfh, i, pr, o, p if not e.get("persist") else 1.0)))
        elif typ in ("alert", "warning"):
            msg = e.get("message", text)
            hdr = e.get("title", "WARNING")
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, c=color, h=hdr, m=msg: _alert_card(d, x, y, 480, 140, h, m, False, p if not e.get("persist") else 1.0)))
        elif typ in ("success", "check"):
            msg = e.get("message", text)
            hdr = e.get("title", "SUCCESS")
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, c=color, h=hdr, m=msg: _alert_card(d, x, y, 480, 140, h, m, True, p if not e.get("persist") else 1.0)))
        elif typ in ("decision_card", "decision", "checklist"):
            q_txt = e.get("quote", e.get("question", text or "WHICH TOOL SHOULD I CALL?"))
            opts = e.get("options") or ["search", "email", "refund"]
            a_idx = int(e.get("active_index", 0))
            scr = int(e.get("score", 95))
            cw = int(float(e.get("width", 0.85)) * W)
            ch = int(float(e.get("height", 0.35)) * H)
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, q=q_txt, o=opts, a=a_idx, s=scr, w=cw, h=ch: _decision_card(d, x, y, w, h, q, o, a, s, p if not e.get("persist") else 1.0)))
        elif typ in ("mac_window", "window"):
            w_title = e.get("title", text or "file.py")
            cw = int(float(e.get("width", 0.82)) * W)
            ch = int(float(e.get("height", 0.28)) * H)
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=lambda d,x,y,p,_, t=w_title, w=cw, h=ch: _mac_window_frame(d, x, y, w, h, t, p if not e.get("persist") else 1.0)))
        elif typ == "custom":
            code = e.get("python_draw_code", "")
            if isinstance(code, list):
                code = "\n".join(code)
            def custom_draw(d, x, y, p, _, code=code, c=color, t=text, f=fnt, p_flag=e.get("persist", False), c_txt=default_ink,
                            e_w=float(e.get("width", 0.7)), e_h=float(e.get("height", float(e.get("width", 0.35))))):
                s = ease_out_cubic(p) if not p_flag else 1.0
                if s < 0.01: return
                # Scale from element's normalized width/height
                base_w = int(e_w * W)
                base_h = int(e_h * H)
                w, h = int(base_w * s), int(base_h * s)

                # Safe clamped line helper — prevents lines going off-canvas
                def _safe_line(pts, fill, width=3):
                    clamped = [(max(0, min(W, px)), max(0, min(H, py))) for px, py in pts]
                    d.line(clamped, fill=fill, width=width)

                # Sanitize common AI string hallucinations
                import re
                safe_code = re.sub(r"['\"]ink['\"]", "INK", code, flags=re.IGNORECASE)
                safe_code = re.sub(r"['\"]white['\"]", "WHITE", safe_code, flags=re.IGNORECASE)
                safe_code = re.sub(r"['\"]accent['\"]", "ACCENT", safe_code, flags=re.IGNORECASE)
                safe_code = re.sub(r"['\"]muted['\"]", "MUTED", safe_code, flags=re.IGNORECASE)

                try:
                    exec(safe_code, {
                        # Position / size
                        "d": d, "cx": x, "cy": y, "w": w, "h": h,
                        "W": W, "H": H,
                        # Colors
                        "fill": c, "INK": c_txt, "WHITE": WHITE, "MUTED": default_muted,
                        "ACCENT": ACCENT, "DARK": DARK, "BLACK": "#000000", "RED": RED, "GREEN": GREEN, "ORANGE": ORANGE,
                        # Fonts — all sizes available
                        "FS": FS, "FB": FB, "FL": FL, "FH2": FH2, "FH1": FH1, "FH0": FT, "FBIG": FBIG,
                        "FMONO_S": FMONO_S, "FMONO": FMONO, "FMONO_L": FMONO_L,
                        # Helpers
                        "_box": _box, "_rect": _rect, "_center": _center, "_txt": _txt, "_circle": _circle,
                        "_arrow": _arrow, "_safe_line": _safe_line,
                        "math": math, "ease_out_cubic": ease_out_cubic, "ease_out_back": ease_out_back,
                    })
                except Exception as ex:
                    print(f"  [custom draw error] {ex}")
                    raise RuntimeError(f"Custom python_draw_code execution failed: {ex}. The LLM provided invalid code.")
            out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                draw_fn=custom_draw))
        else:
            # Dynamic Compositor Fallback: True generative capability.
            # If the AI invents a new object (e.g. "tangled_wires"), we render an actual image for it!
            from asset_manager import get_or_create_ai_icon
            prompt_str = str(typ).replace("_", " ")
            fname = f"dyn_{typ}_{idx}"
            
            # Force high-quality generative AI image creation instead of short-circuiting to emojis
            icon_path = get_or_create_ai_icon(prompt_str, fname)
            
            # If AI icon generation completely fails, fallback to emoji as a last resort
            if not icon_path or not icon_path.exists():
                emoji_char = e.get("emoji")
                if emoji_char:
                    from asset_manager import get_highres_emoji
                    icon_path = get_highres_emoji(emoji_char)
            
            base_img = None
            if icon_path and icon_path.exists():
                try:
                    base_img = Image.open(icon_path).convert("RGBA")
                except Exception:
                    pass
                    
            if base_img:
                # Use the element's specified width/height for target size, defaulting to ~40% of canvas width
                target_w = int(float(e.get("width", 0.4)) * W)
                target_h = int(float(e.get("height", target_w / base_img.width * base_img.height if base_img.width > 0 else target_w)) if "height" in e else (target_w * base_img.height // max(1, base_img.width)))
                target_w = max(80, target_w)
                target_h = max(80, target_h)
                
                def _draw_dyn(d, x, y, p, _d, img=base_img, persist_flag=e.get("persist", False), t_text=text, t_fnt=fnt, t_col=color, t_scale=scale, t_rot=rotation, m=motion, tw=target_w, th=target_h):
                    # Handle scaling based on motion
                    if m == "pop" or m == "scale":
                        s = (ease_out_back(p) if not persist_flag else 1.0) * t_scale
                    else:
                        s = t_scale
                        
                    if s < 0.05: return
                    iw, ih = int(tw * s), int(th * s)
                    if iw < 5 or ih < 5: return
                    res = img.resize((iw, ih), Image.LANCZOS)
                    if t_rot != 0.0:
                        res = res.rotate(-t_rot, resample=Image.BICUBIC, expand=True)
                        iw, ih = res.width, res.height
                        
                    # Handle fading
                    if (m == "fade" or m == "slide_up" or m == "slide_left" or m == "slide_right") and not persist_flag and p < 1.0:
                        alpha = int(255 * ease_out_cubic(p))
                        if alpha < 255:
                            res = res.copy()
                            # Multiply alpha channel
                            res.putalpha(res.split()[3].point(lambda v: int(v * alpha / 255.0)))
                            
                    d._image.paste(res, (int(x - iw // 2), int(y - ih // 2)), res)
                    if t_text and (p > 0.3 or persist_flag):
                        _center(d, x, y + ih // 2 + 35, t_text, t_fnt, t_col)
                
                out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                    draw_fn=lambda d,x,y,p,_, draw_fn=_draw_dyn: draw_fn(d, x, y, p, _)))
            else:
                # Absolute last resort — render as plain centered text
                fallback_text = text if text else str(typ).upper()
                out_els.append(El(x=cx, y=cy, enter_start=start, enter_end=end_t, motion=motion if not e.get("persist") else "fade", easing=easing, persist=e.get("persist", False),
                    draw_fn=lambda d,x,y,p,_, t=fallback_text, f=fnt, c=color: _center(d, x, y, t, f, c)))
        
        # Apply metadata to any elements generated by this json object
        for el in out_els[start_len:]:
            el.depth = depth
            el.id = el_id

    # Anti-Clustering Resolver: Prevent foreground cards and text elements from colliding
    for i in range(len(out_els)):
        for j in range(i + 1, len(out_els)):
            e1, e2 = out_els[i], out_els[j]
            # Keep persistent headers or top bars above y=120
            if e1.y < 120 or e2.y < 120: continue
            if abs(e1.x - e2.x) < 320 and abs(e1.y - e2.y) < 140:
                # Adjust e2.y to eliminate text/card overlap
                e2.y = min(1560, max(140, e1.y + 150))

    # Z-Index sort by depth
    out_els.sort(key=lambda el: el.depth)
                
    return out_els, bg_col, bg_fn








def ai_custom(scene, idx, total):
    """Dynamically construct scene elements from AI generated JSON blueprint.
    Storyboard schema:
    {
        "kind": "custom",
        "bg_color": "PAPER_BG" | "DARK",
        "elements": [...]
    }
    """
    raw_els = scene.get("elements", [])
    out = []
    
    bg_choice = scene.get("bg_color", "DARK")
    if bg_choice == "DARK":
        bg_col = DARK
        bg_fn = _dark_bg
        default_ink = WHITE
        default_muted = "#8CA4B3"
    else:
        bg_col = PAPER_BG
        bg_fn = _paper_bg
        default_ink = INK
        default_muted = MUTED

    # Color mapping
    colors = {
        "INK": default_ink, "WHITE": WHITE, "ACCENT": ACCENT, "MUTED": default_muted,
        "GREEN": GREEN, "ORANGE": ORANGE, "RED": RED, "DARK": DARK
    }
    
    # Font mapping
    fonts = {
        "FT": FT, "FH1": FH1, "FH2": FH2, "FB": FB, "FS": FS,
        "FL": FL, "FBIG": FBIG, "FMASS": FMASS
    }
    
    for el in raw_els:
        etype = str(el.get("type", "text")).lower()
        x = float(el.get("x", W/2))
        y = float(el.get("y", H/2))
        
        # Intelligent clamping to prevent off-screen glitches
        x = max(20, min(W - 20, x))
        y = max(20, min(H - 20, y))
        
        motion = el.get("motion", "fade")
        start = float(el.get("enter_start", 0.0))
        end = float(el.get("enter_end", 1.0))
        if el.get("persist", False):
            start = 0.0
            motion = "fade"
            end = 0.01
            
        c_name = el.get("color", "INK")
        if c_name == "INK" and bg_choice == "DARK": color = default_ink
        elif c_name == "MUTED" and bg_choice == "DARK": color = default_muted
        elif c_name == "WHITE" and bg_choice == "PAPER_BG": color = INK
        else: color = colors.get(c_name, default_ink)

        font = fonts.get(el.get("font", "FB"), FB)
        text = str(el.get("text", ""))
        w = float(el.get("w", 200))
        h = float(el.get("h", 100))
        r = float(el.get("r", 50))
        
        def make_draw_fn(t, txt, fnt, col, wd, ht, rad):
            if t == "text" or t == "icon":
                return lambda d, cx, cy, p, _: _center(d, cx, cy, txt, fnt, col) if motion != "pop" else _pop(d, cx, cy, txt, fnt, col, p)
            elif t == "box":
                return lambda d, cx, cy, p, _: _scale_box(d, cx, cy, wd, ht, col, 20, p) if motion == "scale" else _box(d, cx, cy, wd, ht, col, 20)
            elif t == "circle":
                return lambda d, cx, cy, p, _: _grow_circle(d, cx, cy, rad, col, p) if motion == "scale" else _circle(d, cx, cy, rad, fill=col)
            elif t == "line" or t == "arrow":
                return lambda d, cx, cy, p, _: _arrow(d, cx-wd/2, cy, cx+wd/2, cy, col, 5, p)
            return lambda d, cx, cy, p, _: None

        out.append(El(
            x=x, y=y,
            motion=motion,
            enter_start=start, enter_end=end,
            exit_start=el.get("exit_start"),
            draw_fn=make_draw_fn(etype, text, font, color, w, h, r)
        ))
        
    return out, bg_col, bg_fn


BUILDERS = {
    "custom": custom,
}


def viral_scene(scene: dict, idx: int, total: int):
    """
    VIRAL_SHORT_V2 scene builder.

    All layout is LOCKED by resolve_viral_template_layout().
    This function never calls sequence_director or vo_composition_agent.
    AI-provided python_draw_code is IGNORED (stripped at storyboard validation).
    """
    from viral_template import (
        resolve_viral_template_layout, get_element_stagger,
        sanitize_text, truncate_headline,
        BACKGROUND_0, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DIM,
        ACCENT, ACCENT_2, ZONE_A, ZONE_B, ZONE_C, ZONE_D,
        ROLE_ACCENTS,
        MOTION_ENERGY_MAP, MOTION_HERO_REVEAL,
    )
    from viral_renderer import (
        render_viral_background, render_viral_header, render_viral_headline,
        dispatch_hero, render_viral_impact, render_viral_caption,
        FH1_VIRAL, FB_VIRAL, FS_VIRAL, FL_VIRAL, FT_VIRAL,
    )

    # ── HARD ASSERTIONS: Prevent legacy accidental rendering ───────────────
    tc = scene.get("template_context") or {}
    template_version = tc.get("template_version", "VIRAL_SHORT_V2")
    assert template_version in ("VIRAL_SHORT_V1", "VIRAL_SHORT_V2"), f"Expected VIRAL_SHORT_V1/V2, got {template_version}"

    layout = resolve_viral_template_layout(scene, idx, total)
    role = str(scene.get("role", "")).strip().lower() or "process"
    headline  = truncate_headline(str(scene.get("headline", "")))
    hero_type = scene.get("hero_type", "hero_glow")
    hero_label = sanitize_text(str(scene.get("hero_label", "")), "")
    fact       = sanitize_text(str(scene.get("supporting_fact", "")), "")
    visual_data = scene.get("visual_data") or {}
    motion_energy = str(scene.get("motion_energy", "medium")).lower()

    color_a, color_b = ROLE_ACCENTS.get(role, (ACCENT, ACCENT_2))

    # ── Background (always DARK cinematic 3-layer parallax) ───────────────
    bg_col = BACKGROUND_0
    assert bg_col != PAPER_BG, "ERROR: viral job accidentally entered legacy renderer (PAPER_BG)"

    def _viral_bg(img: Image.Image, t_seconds: float = 0.0) -> None:
        render_viral_background(img, t_seconds, role=role)

    # ── Scene element list ────────────────────────────────────────────────
    out_els = []

    # 1. Brand header — persists through entire scene (Zone A)
    out_els.append(El(
        x=W/2, y=ZONE_A[1]//2,
        enter_start=0.0, enter_end=0.03, motion="fade", hold=True, persist=True,
        draw_fn=lambda d, x, y, p, _, counter=idx+1, tot=total:
            render_viral_header(d, counter, tot, p if p < 1.0 else 1.0,
                                d.t_seconds if hasattr(d, 't_seconds') else 0.0)
    ))

    # 2. Headline — Zone B
    hl_stagger = get_element_stagger(0)
    out_els.append(El(
        x=layout.headline_x, y=layout.headline_y,
        from_y=layout.headline_y + 60,
        enter_start=hl_stagger, enter_end=hl_stagger + 0.28,
        motion="slide_up", easing="ease_out_back", hold=True, persist=False,
        draw_fn=lambda d, x, y, p, _, hl=headline, L=layout, col=color_a:
            render_viral_headline(d, hl, L, p, accent_color=col,
                                  t_seconds=d.t_seconds if hasattr(d, 't_seconds') else 0.0)
    ))

    # 3. Hero visual — Zone C (dominant foreground footprint)
    hero_stagger = get_element_stagger(1)
    hero_end = hero_stagger + 0.35

    def _hero_draw(d, x, y, progress, _, _ht=hero_type, _L=layout,
                   _lbl=hero_label, _vd=visual_data):
        t_sec = d.t_seconds if hasattr(d, 't_seconds') else 0.0
        dispatch_hero(_ht, d._image, _L, _lbl, _vd, t_sec, progress)

    out_els.append(El(
        x=layout.hero_cx, y=layout.hero_cy,
        enter_start=hero_stagger, enter_end=hero_end,
        motion=MOTION_ENERGY_MAP.get(motion_energy, "hero_reveal"),
        easing="ease_out_back", hold=True, persist=False,
        draw_fn=_hero_draw
    ))

    # 4. Supporting fact — Zone D (OPTIONAL)
    if fact:
        fact_stagger = get_element_stagger(3)
        out_els.append(El(
            x=layout.impact_x, y=layout.impact_y,
            enter_start=fact_stagger, enter_end=fact_stagger + 0.25,
            motion="slide_up", easing="ease_out_cubic", hold=True, persist=False,
            draw_fn=lambda d, x, y, p, _, _fact=fact, _L=layout:
                render_viral_impact(d, _fact, _L, p)
        ))

    return out_els, bg_col, _viral_bg


def editorial_scene(scene: dict, idx: int, total: int):
    """Execute an editorial render plan into native pixel operations."""
    from editorial.executor import build_editorial_executor
    elements, bg_color, bg_fn, _manifest = build_editorial_executor(scene, idx, total)
    return elements, bg_color, bg_fn


def build_scene(scene: dict, idx: int, total: int):
    """Route to the appropriate scene builder based on scene kind."""
    from viral_template import is_viral_template_scene, is_editorial_template_scene
    if is_editorial_template_scene(scene):
        return editorial_scene(scene, idx, total)
    if is_viral_template_scene(scene):
        return viral_scene(scene, idx, total)
    return custom(scene, idx, total)
