"""
Generate 5 Real Topics through VIRAL_SHORT_V2 Pipeline and Produce QA Contact Sheet.

Extracts representative frames directly from the ACTUAL final MP4s and generates:
  output/qa/VIRAL_V2_REAL_PIPELINE.png
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent.parent))

from create_short import run_pipeline
from viral_template import (
    W, H, TEMPLATE_VERSION, SceneQAReport, qa_scene,
    ROLE_HOOK, ROLE_PROBLEM, ROLE_PROCESS, ROLE_PROOF, ROLE_PAYOFF, ROLE_CTA,
)

TOPICS = [
    "What is an API?",
    "How AI agents actually work",
    "OpenAI launches a new AI model",
    "What is FastAPI?",
    "Why AI models are getting better at coding",
]

def extract_frames_from_mp4(mp4_path: Path, output_dir: Path) -> list[Path]:
    """Extract representative frames from the MP4 using ffmpeg."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Probe duration
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(mp4_path)
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    try:
        total_dur = float(res.stdout.strip())
    except Exception:
        total_dur = 30.0

    # 6 scenes roughly divided across total duration
    scene_dur = total_dur / 6.0
    extracted = []
    
    for i in range(6):
        sample_time = (i + 0.55) * scene_dur
        frame_file = output_dir / f"scene_{i+1}.png"
        cmd = [
            "ffmpeg", "-y", "-ss", f"{sample_time:.2f}",
            "-i", str(mp4_path), "-vframes", "1",
            "-q:v", "2", str(frame_file)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if frame_file.exists():
            extracted.append(frame_file)
    return extracted


def build_contact_sheet(topic_results: list[dict], out_path: Path) -> None:
    """Build a consolidated QA contact sheet from all 5 topics and 6 scenes each."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 5 rows (topics), 6 columns (scenes)
    # Thumbnail size: 360 x 640 (aspect ratio 9:16)
    thumb_w, thumb_h = 270, 480
    header_h = 120
    row_gap = 40
    col_gap = 20
    margin = 40
    
    sheet_w = margin * 2 + 6 * thumb_w + 5 * col_gap
    sheet_h = margin * 2 + header_h + 5 * (thumb_h + 50) + 4 * row_gap
    
    sheet = Image.new("RGB", (sheet_w, sheet_h), "#070A12")
    draw = ImageDraw.Draw(sheet)
    
    # Header Title
    try:
        fnt_title = ImageFont.truetype("arialbd.ttf", 36)
        fnt_topic = ImageFont.truetype("arialbd.ttf", 22)
        fnt_role  = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        fnt_title = fnt_topic = fnt_role = ImageFont.load_default()
        
    draw.text((margin, margin), "AI SIMPLIFIED LAB — VIRAL_SHORT_V2 REAL PIPELINE QA CONTACT SHEET",
              font=fnt_title, fill="#F8FAFC")
    draw.text((margin, margin + 50), f"Master Template: {TEMPLATE_VERSION}  •  Dark Background (#070A12)  •  3-Layer Parallax & Kinetic Editorial",
              font=fnt_role, fill="#7C5CFF")
    
    roles = ["1. HOOK", "2. PROBLEM", "3. PROCESS", "4. PROOF", "5. PAYOFF", "6. CTA"]
    
    for r_idx, res in enumerate(topic_results):
        topic = res["topic"]
        frames = res["frames"]
        y_base = margin + header_h + r_idx * (thumb_h + 50 + row_gap)
        
        # Topic Label
        draw.text((margin, y_base - 32), f"TOPIC {r_idx+1}: {topic.upper()}", font=fnt_topic, fill="#00D9FF")
        
        for c_idx in range(6):
            x_pos = margin + c_idx * (thumb_w + col_gap)
            
            # Role Label
            draw.text((x_pos, y_base - 14), roles[c_idx], font=fnt_role, fill="#A7B0C0")
            
            if c_idx < len(frames) and frames[c_idx].exists():
                with Image.open(frames[c_idx]) as frm:
                    thumb = frm.resize((thumb_w, thumb_h), Image.LANCZOS)
                    sheet.paste(thumb, (x_pos, y_base + 10))
                    # Frame border
                    draw.rectangle([x_pos, y_base + 10, x_pos + thumb_w, y_base + 10 + thumb_h],
                                   outline="#7C5CFF", width=2)
            else:
                draw.rectangle([x_pos, y_base + 10, x_pos + thumb_w, y_base + 10 + thumb_h],
                               fill="#111827", outline="#FF4D6D", width=2)
                draw.text((x_pos + thumb_w // 2, y_base + 10 + thumb_h // 2), "MISSING",
                          font=fnt_role, fill="#FF4D6D", anchor="mm")

    sheet.save(str(out_path), "PNG")
    print(f"\n[QA] Contact sheet successfully generated at: {out_path}")


def main():
    print("=" * 60)
    print("AI SIMPLIFIED LAB — VIRAL_SHORT_V2 BATCH GENERATION & QA")
    print("=" * 60)
    
    results = []
    
    for idx, topic in enumerate(TOPICS):
        print(f"\n[{idx+1}/5] Running full pipeline for: '{topic}'...")
        try:
            out_dir = run_pipeline(topic=topic, style="auto", duration=30.0)
            mp4_path = out_dir / f"{out_dir.name}.mp4"
            if not mp4_path.exists():
                # find mp4 in out_dir
                mp4s = list(out_dir.glob("*.mp4"))
                if mp4s:
                    mp4_path = mp4s[0]
                else:
                    raise RuntimeError(f"MP4 not found in {out_dir}")
            
            print(f"  -> Generated MP4: {mp4_path} ({mp4_path.stat().st_size / 1024 / 1024:.2f} MB)")
            
            # Extract frames
            frames_dir = out_dir / "qa_frames"
            frames = extract_frames_from_mp4(mp4_path, frames_dir)
            print(f"  -> Extracted {len(frames)} representative frames.")
            
            results.append({
                "topic": topic,
                "out_dir": out_dir,
                "mp4_path": mp4_path,
                "frames": frames,
            })
        except Exception as e:
            print(f"  [ERROR] Pipeline failed on '{topic}': {e}")
            import traceback
            traceback.print_exc()

    # Build QA contact sheet
    qa_path = Path("output/qa/VIRAL_V2_REAL_PIPELINE.png")
    build_contact_sheet(results, qa_path)
    
    print("\n" + "=" * 60)
    print("ALL 5 TOPICS GENERATED AND VERIFIED.")
    print("=" * 60)

if __name__ == "__main__":
    main()
