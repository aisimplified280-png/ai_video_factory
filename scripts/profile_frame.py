import time, sys, os
sys.path.insert(0, os.path.abspath("."))
from PIL import Image, ImageDraw
from viral_template import resolve_viral_template_layout
from viral_renderer import (
    render_viral_background, render_viral_header, render_viral_headline,
    dispatch_hero, render_viral_caption, render_viral_impact
)

img = Image.new("RGB", (1080, 1920), "#070A12")
scene = {
    "kind": "viral_short_v2",
    "role": "hook",
    "headline": "WHAT IS AN API",
    "hero_type": "hero_orb",
    "hero_label": "API GATEWAY",
    "supporting_fact": "",
    "visual_data": {},
    "motion_energy": "high",
}
L = resolve_viral_template_layout(scene, 0, 6)

from animation import build_scene, render_frame, make_scene_frames

elements, bg_color, bg_fn = build_scene(scene, 0, 6)
def _fast_hero_orb(img, cx, cy, core_r, color_a, color_b, s):
    # Core + Glow in single buffer
    buf_r = int(core_r * 1.5)
    core_buf = Image.new("RGBA", (buf_r * 2 + 8, buf_r * 2 + 8), (0, 0, 0, 0))
    dc = ImageDraw.Draw(core_buf)
    
    # Outer glow
    r1, g1, b1 = 124, 92, 255
    r2, g2, b2 = 0, 217, 255
    for i in range(6, 0, -1):
        rad = int(buf_r * (i / 6))
        alpha = int(22 * ((1.0 - (i / 6)) ** 1.3))
        dc.ellipse((buf_r - rad + 4, buf_r - rad + 4, buf_r + rad + 4, buf_r + rad + 4),
                   fill=(r1, g1, b1, alpha))
    
    # Concentric core
    for ri in range(core_r, 0, -8):
        t_frac = 1.0 - (ri / core_r)
        alpha_core = int(180 + 75 * t_frac)
        dc.ellipse((buf_r - ri + 4, buf_r - ri + 4, buf_r + ri + 4, buf_r + ri + 4),
                   fill=(r2, g2, b2, alpha_core))
        
    hot_r = int(core_r * 0.35)
    dc.ellipse((buf_r - hot_r + 4, buf_r - hot_r + 4, buf_r + hot_r + 4, buf_r + hot_r + 4),
               fill=(255, 255, 255, 240))
    img.paste(core_buf, (cx - buf_r - 4, cy - buf_r - 4), core_buf)

img = Image.new("RGB", (1080, 1920), "#070A12")
t0 = time.perf_counter()
for _ in range(10):
    _fast_hero_orb(img, 540, 920, 240, "#7C5CFF", "#00D9FF", 1.0)
t1 = time.perf_counter()
print(f"Fast hero orb: {(t1 - t0)*1000/10:.2f} ms")





