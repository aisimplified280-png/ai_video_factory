#!/usr/bin/env python3
"""AI SIMPLIFIED LAB — Video Factory v2.

Full pipeline: Topic → Storyboard → Animated Scenes → Video with branding.
Just run: python create_short.py --topic "How does Docker work?"

Styles: explainer (default), interview, list, comparison
Auto-detects best style from topic if not specified.
"""
from __future__ import annotations

import envfile
envfile.load_dotenv()

import argparse
import atexit
import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

from channel import CHANNEL_NAME, LOGO, MUSIC_DIR, MUSIC_TRACKS, OUTROS, ROOT
from styles import list_styles, auto_detect_style
from storyboard import generate_storyboard, clean_concept
from animation import (
    FPS, W, H, PAPER_BG, ACCENT, INK, MUTED, WHITE, DARK,
    build_scene, make_scene_frames, render_frame, _dotted_grid_bg,
    _f as font, _box, _center, _grow_circle, _scale_box, _scale_circle, _pop,
    FT, FH1, FH2, FB, FS, FL, FMASS,
    ease_out_cubic, ease_out_back,
)


def safe_name(text):
    import re
    result = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return result[:48] or "explainer"


def get_scene_transition_config() -> dict:
    """Return the configured scene transition type and frame count."""
    transition_type = str(os.getenv("SCENE_TRANSITION_TYPE", "cut")).strip().lower()
    if transition_type not in {"none", "cut", "dissolve"}:
        transition_type = "cut"
    try:
        frames = int(str(os.getenv("SCENE_TRANSITION_FRAMES", "4") or "4"))
    except ValueError:
        frames = 4
    frames = max(0, frames)
    if transition_type == "none":
        frames = 0
    return {"type": transition_type, "frames": frames}


def _scene_kind(scene):
    return str(scene.get("kind", "")).strip().lower()


def render_scene_frames(scene, index, total, scene_seconds, intro_seconds=1.2, style_name="explainer", subs=None):
    from viral_template import is_editorial_template_scene, is_viral_template_scene, create_template_context
    _was_editorial = is_editorial_template_scene(scene)
    _was_viral = is_viral_template_scene(scene) and not _was_editorial

    if not _was_editorial:
        from vo_composition_agent import process_scene_composition
        scene = process_scene_composition(scene, subs=subs, scene_duration=scene_seconds)
    scene["_render_duration_seconds"] = float(scene_seconds)

    # Re-stamp viral attributes in case any agent or adapter altered them
    if _was_viral:
        tm = scene.get("_template_mode", "viral_explainer")
        role = scene.get("role", "process")
        scene["kind"] = "viral_short_v2"
        scene["_template_mode"] = tm
        scene["template_context"] = create_template_context(tm, role)

    elements, bg_color, bg_fn = build_scene(scene, index, total)
    focus = scene.get("focus") or scene.get("camera_focus")
    choreography = scene.get("visual_scene", {}).get("camera_choreography", "")
    if _was_editorial:
        camera_plan = scene.get("render_plan", {}).get("camera") or {}
        focus = camera_plan.get("focus")
        choreography = str(camera_plan.get("behavior", "static"))
    return make_scene_frames(elements, scene_seconds, FPS, intro_seconds, bg_color, bg_fn, subs, camera_focus=focus, camera_choreography=choreography, scene_dict=scene)


def render_thumbnail(scene, index, total, style_name="explainer"):
    elements, bg_color, bg_fn = build_scene(scene, index, total)
    return render_frame(elements, 1, 2, bg_color, bg_fn)


def add_watermark(img: Image.Image) -> Image.Image:
    d = ImageDraw.Draw(img)
    d.text((44, 1225), CHANNEL_NAME.upper(), font=font(20), fill="#9AA6AA")
    return img


def concat_visual_scenes(scene_mp4s, target, transitions=None, on_progress=None):
    import subprocess
    if not scene_mp4s:
        raise ValueError("No scenes to concatenate")
    if len(scene_mp4s) == 1:
        import shutil
        shutil.copy(scene_mp4s[0], target)
        return

    cfg = get_scene_transition_config()
    transition_type = str((transitions[0] if transitions else cfg["type"])).lower() if transitions else cfg["type"]
    transition_frames = cfg["frames"]
    if transition_type not in {"none", "cut", "dissolve"}:
        transition_type = "cut"

    if on_progress:
        on_progress(0.55, "Concatenating scenes with FFmpeg")

    if transition_type == "dissolve":
        durations = [get_video_duration(p) for p in scene_mp4s]
        if any(d <= 0 for d in durations):
            transition_type = "cut"
        else:
            filters = []
            current_label = "[0:v]"
            trans_dur = max(0.04, min(0.25, transition_frames / 24.0 if transition_frames else 0.17))
            for idx in range(1, len(scene_mp4s)):
                offset = max(0.0, durations[idx - 1] - trans_dur)
                out_label = f"[v{idx}]"
                filters.append(f"{current_label}[{idx}:v]xfade=transition=fade:duration={trans_dur:.3f}:offset={offset:.3f}{out_label}")
                current_label = out_label
            filter_complex = ";".join(filters)
            ffmpeg_cmd = ["ffmpeg", "-y", "-loglevel", "error"]
            for p in scene_mp4s:
                ffmpeg_cmd.extend(["-i", str(p)])
            ffmpeg_cmd.extend(["-filter_complex", filter_complex, "-map", f"{current_label}", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(target)])
            try:
                subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, cwd=str(target.parent))
                return
            except subprocess.CalledProcessError as e:
                err = e.stderr.decode("utf-8", errors="ignore") if e.stderr else "Unknown error"
                raise RuntimeError(f"FFmpeg dissolve transition failed:\n{err}")

    concat_list = target.with_name("concat_visuals.txt")
    lines = [f"file '{p.name}'" for p in scene_mp4s]
    concat_list.write_text("\n".join(lines), encoding="utf-8")

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
           "-i", str(concat_list), "-c", "copy", str(target)]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, cwd=str(target.parent))
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="ignore") if e.stderr else "Unknown error"
        raise RuntimeError(f"FFmpeg concat failed:\n{err}")
    finally:
        try: concat_list.unlink(missing_ok=True)
        except Exception: pass

def generate_tts(text: str, outfile: Path) -> Path:
    subfile = outfile.with_suffix(".vtt")
    cmd = ["edge-tts", "--voice", "en-US-ChristopherNeural", "--text", text, 
           "--write-media", str(outfile), "--write-subtitles", str(subfile)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        raise RuntimeError("edge-tts not found on PATH — run pip install edge-tts")
    return subfile

def parse_vtt(vtt_file: Path) -> list:
    if not vtt_file.exists():
        return []
    lines = vtt_file.read_text(encoding="utf-8").splitlines()
    subs = []
    for i, line in enumerate(lines):
        if "-->" in line:
            times = line.split(" --> ")
            def pt(t):
                parts = t.strip().split(":")
                if len(parts) == 3:
                    return float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
                elif len(parts) == 2:
                    return float(parts[0])*60 + float(parts[1])
                return 0.0
            try:
                start = pt(times[0])
                end = pt(times[1])
                text = lines[i+1].strip()
                subs.append({"start": start, "end": end, "text": text})
            except Exception:
                pass
    return subs

def get_audio_duration(filepath: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(filepath)]
    try:
        out = subprocess.check_output(cmd, text=True)
        return float(out.strip())
    except Exception:
        return 3.0


def get_video_duration(filepath: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(filepath)]
    try:
        out = subprocess.check_output(cmd, text=True)
        return max(0.0, float(out.strip() or "0.0"))
    except Exception:
        return 0.0


import legacy_adapter

def run_pipeline(topic, style="auto", notes="", duration=30.0, intro=1.2, music="auto", visual_debug=False, on_progress=None):
    """Full pipeline, importable so the web UI can run it in-process with progress.

    on_progress(frac 0..1, message) is called throughout. Returns output dir Path.
    Raises RuntimeError with a human-readable message on failure.
    """
    def prog(frac, msg):
        if on_progress:
            on_progress(max(0.0, min(1.0, frac)), msg)

    style_name = style if style != "auto" else auto_detect_style(topic)
    prog(0.02, f"Style: {style_name} — writing storyboard")
    story = generate_storyboard(topic, style_name, notes, duration)
    if not story:
        raise RuntimeError("Failed to generate storyboard")

    from viral_template import is_viral_template_scene, is_editorial_template_scene, create_template_context
    is_editorial = any(is_editorial_template_scene(s) for s in story.get("scenes", []))
    is_viral = any(is_viral_template_scene(s) and not is_editorial_template_scene(s) for s in story.get("scenes", []))

    # Run non-viral scenes through Legacy Adapter
    for scene in story.get("scenes", []):
        scene_is_editorial = is_editorial_template_scene(scene)
        scene_is_viral = is_viral_template_scene(scene) and not scene_is_editorial
        if scene_is_viral:
            tm = scene.get("_template_mode", style_name if style_name in ("viral_explainer", "viral_news", "editorial_explainer", "editorial_viral") else "viral_explainer")
            role = scene.get("role", "process")
            scene["kind"] = "viral_short_v2"
            scene["_template_mode"] = tm
            scene["template_context"] = create_template_context(tm, role)
        elif scene_is_editorial:
            mode = scene.get("_template_mode") or (scene.get("template_context") or {}).get("template_mode") or style_name
            scene["kind"] = mode if mode in ("editorial_explainer", "editorial_viral") else "editorial_explainer"
            scene["_template_mode"] = mode
        else:
            legacy_adapter.adapt_scene(scene)

    if is_viral or is_editorial:
        # Enforce exactly 6 scenes for story-driven jobs
        story["scenes"] = story["scenes"][:6]
        # Pipeline Debug Logging
        print(f"\n[PIPELINE]")
        print(f"topic={topic}")
        print(f"\n[PIPELINE]")
        print(f"template_version={'EDITORIAL_RENDER_PLAN' if is_editorial else 'VIRAL_SHORT_V2'}")
        print(f"\n[PIPELINE]")
        print(f"template_mode={style_name}")
        print(f"\n[PIPELINE]")
        print(f"scene_count={len(story['scenes'])}")
        for i, s in enumerate(story["scenes"]):
            print(f"\n[PIPELINE]")
            print(f"scene_{i+1}_role={s.get('role', '')}")
        print(f"\n[PIPELINE]")
        print(f"renderer={'editorial_executor' if is_editorial else 'viral_renderer'}")
        print(f"\n[PIPELINE]")
        print(f"background={'#F6F8FC' if is_editorial else '#070A12'}")
        print(f"\n[PIPELINE]")
        print(f"legacy_renderer=FALSE")
        
    import random
    outro_dir = ROOT / "AI SIMPLIFIED LAB" / "outro"
    outro_video = None

    # Auto-append Subscribe Outro CTA scene ONLY for legacy non-viral scenes
    if not outro_video and not is_viral and not is_editorial:
        if story.get("scenes") and story["scenes"][-1].get("kind") not in ("cta", "outro", "conclusion"):
            story["scenes"].append({
                "kind": "cta",
                "heading": "SUBSCRIBE NOW",
                "subheading": "AI SIMPLIFIED LAB",
                "narration": f"Subscribe to AI SIMPLIFIED LAB for more quick tech breakdowns on {topic.strip()}!",
                "transition": "zoom_in",
                "bg_color": "DARK",
                "elements": [
                    {"type": "subscribe_card", "position": "center", "enter_start": 0.05, "motion": "pop"},
                    {"type": "text", "position": "bottom", "text": "Save & Share this Short!", "color": "WHITE", "enter_start": 0.25, "motion": "slide_up"}
                ]
            })

    import random
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{random.randint(100,999)}"
    out = ROOT / "output" / f"{safe_name(topic)}-{stamp}"
    assets = out / "scenes"
    assets.mkdir(parents=True, exist_ok=True)
    
    success_flag = [False]
    import shutil

    total_scenes = len(story["scenes"])
    all_scene_mp4s = []
    audio_files = []
    transitions = []

    # Pre-fetch all Pollinations AI assets in parallel
    prog(0.04, "Pre-fetching AI visual assets concurrently...")
    ai_prompts = []
    for s in story.get("scenes", []):
        for el in s.get("elements", []):
            typ = str(el.get("type", "")).lower()
            if typ == "ai_icon" and el.get("prompt"):
                ai_prompts.append((el["prompt"], safe_name(el["prompt"])[:48]))
            elif typ not in ("text", "emoji", "box", "image", "subscribe_card", "brand_badge") and typ:
                ai_prompts.append((typ, safe_name(typ)[:48]))
                
    if ai_prompts:
        from concurrent.futures import ThreadPoolExecutor
        from asset_manager import get_or_create_ai_icon
        ai_prompts = list(set(ai_prompts))
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(get_or_create_ai_icon, p, f) for p, f in ai_prompts]
            for fut in futures:
                try: fut.result(timeout=60)
                except Exception as e: print(f"Warning parallel fetch: {e}")

    current_time = 0.0
    for idx, scene in enumerate(story["scenes"]):
        transitions.append(scene.get("transition", "cut"))
        base = 0.05 + 0.45 * (idx / total_scenes)
        
        narration = scene.get("narration", "").strip() or " "
        audio_path = out / f"audio_{idx:02d}.mp3"
        prog(base, f"Scene {idx+1}/{total_scenes}: Generating TTS")
        sub_path = generate_tts(narration, audio_path)
        
        # Determine exact scene duration from audio
        audio_dur = get_audio_duration(audio_path)
        # Pad slightly if needed to let animations breathe
        scene_seconds = max(audio_dur, intro + 0.5)
        
        # Pad audio with exact silence if scene was extended to guarantee 1:1 sync with video frames
        if scene_seconds > audio_dur + 0.05:
            padded_path = out / f"audio_padded_{idx:02d}.mp3"
            pad_amount = scene_seconds - audio_dur
            cmd_pad = ["ffmpeg", "-y", "-i", str(audio_path), "-af", f"apad=pad_dur={pad_amount:.3f}", str(padded_path)]
            subprocess.run(cmd_pad, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audio_files.append(padded_path)
        else:
            audio_files.append(audio_path)
            
        subs = parse_vtt(sub_path)
        
        # Audio Sync Logic: map "sync_word" in elements to absolute VTT timestamps
        for el in scene.get("elements", []):
            sync = el.get("sync_word")
            if sync and isinstance(sync, str):
                target = sync.lower()
                for s in subs:
                    sub_text = s["text"].lower()
                    if target in sub_text or any(w.startswith(target) for w in sub_text.split()):
                        # Override element's enter_start dynamically
                        el["enter_start"] = max(0.05, min(0.95, round(s["start"] / scene_seconds, 3)))
                        break
        
        scene["start_seconds"] = round(current_time, 2)
        scene["end_seconds"] = round(current_time + scene_seconds, 2)
        current_time += scene_seconds

        prog(base + 0.1, f"Scene {idx+1}/{total_scenes}: {scene.get('kind','scene')} thumbnail")
        thumb = render_thumbnail(scene, idx, total_scenes, style_name)
        thumb = add_watermark(thumb)
        kind = str(scene.get("kind", "scene")).lower()
        path = assets / f"{idx+1:02d}-{kind}.png"
        thumb.save(path)
        scene["asset"] = f"scenes/{path.name}"

        anim_duration = scene_seconds
        prog(base + 0.2, f"Scene {idx+1}/{total_scenes}: animating elements")
        
        from auditor import audit_thumbnail, auto_heal_scene_blueprint
        is_valid, audit_msg = audit_thumbnail(thumb, idx)
        if not is_valid:
            print(f"  -> [Auditor Guard Alert] {audit_msg} Auto-healing scene {idx+1}...")
            scene = auto_heal_scene_blueprint(scene, topic, idx)
            # Re-render thumbnail if healed
            thumb = render_thumbnail(scene, idx, total_scenes, style_name)
            thumb = add_watermark(thumb)
            thumb.save(path)
            
        scene_mp4 = out / f"scene_{idx:02d}.mp4"
        import hashlib
        import json
        scene_hash = hashlib.sha256(json.dumps(scene, sort_keys=True).encode()).hexdigest()
        meta_path = out / f"scene_{idx:02d}.meta.json"
        
        if scene_mp4.exists() and meta_path.exists() and json.loads(meta_path.read_text()).get("hash") == scene_hash:
            print(f"Skipping rendering, using cached {scene_mp4.name}")
            render_manifest_path = out / f"scene_{idx:02d}.render_manifest.json"
            if render_manifest_path.exists():
                scene["render_manifest"] = json.loads(render_manifest_path.read_text(encoding="utf-8"))
        else:
            from video_encoder import FFmpegRawVideoEncoder
            encoder = FFmpegRawVideoEncoder(scene_mp4, fps=FPS, width=W, height=H)
            encoder.start()
            
            frame_gen = render_scene_frames(scene, idx, total_scenes, scene_seconds, anim_duration, style_name, subs=subs)
            for f_idx, frame in enumerate(frame_gen):
                encoder.encode_frame(frame)
                
            encoder.close()
            subprocess.run(["ffprobe", "-v", "error", "-show_streams", str(scene_mp4)], check=True)
            meta_path.write_text(json.dumps({"hash": scene_hash}))

        if is_editorial and scene.get("render_manifest"):
            (out / f"scene_{idx:02d}.render_manifest.json").write_text(
                json.dumps(scene["render_manifest"], indent=2), encoding="utf-8"
            )
            
        all_scene_mp4s.append(scene_mp4)

    story["style"] = style_name

    with (out / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(story, f, indent=2, ensure_ascii=False)

    attempts = story.get("provider_attempts", [])
    winners = [a for a in attempts if a.get("status") == "success"]
    source_line = (f"Storyboard: {story.get('source', '?')} "
                   f"({winners[-1].get('detail', '')})" if winners
                   else f"Storyboard: {story.get('source', 'local-template')} (generic layout)")
    lines = [f"VOICE-OVER SCRIPT — {story['title']}", "",
             f"Style: {style_name}", source_line, "Timing is approximate.", ""]
    for s in story["scenes"]:
        heading = s.get('heading', 'Scene')
        lines += [f"[{s['start_seconds']:05.2f}s–{s['end_seconds']:05.2f}s] {heading}",
                  textwrap.fill(s.get("narration", ""), 88), ""]
    (out / "vo_script.txt").write_text("\n".join(lines), encoding="utf-8")

    total_frames = int(current_time * FPS)
    print(f"Rendering ~{total_frames} frames across {total_scenes} scenes directly to FFmpeg...")

    def enc_prog(frac, msg):
        prog(0.50 + frac, msg)
        
    visual_vid = out / "visual_only.mp4"
    concat_visual_scenes(all_scene_mp4s, visual_vid, transitions=transitions, on_progress=enc_prog)
    
    prog(0.92, "Mixing final audio")
    # Concat audios cleanly with MP3 re-encoding to eliminate timestamp drift
    audio_concat = out / "audio_concat.txt"
    audio_concat_lines = [f"file '{p.name}'" for p in audio_files]
    audio_concat.write_text("\n".join(audio_concat_lines), encoding="utf-8")
    
    voiceover = out / "voiceover.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_concat), "-c:a", "libmp3lame", "-b:a", "192k", str(voiceover)],
                   cwd=str(out), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                   
    prog(0.95, "Multiplexing final video")
    final_vid = out / "final_video.mp4"
    
    # Select track via music_catalog (category, track, auto smart mood, or none)
    from music_catalog import get_music_track
    bgm = get_music_track(music, topic, style_name)
    
    # Kinetic SFX placeholder (User can drop a pre-timed SFX track here)
    sfx_track = ROOT / "AI SIMPLIFIED LAB" / "sfx" / "kinetic_sfx_master.mp3"
    has_sfx = sfx_track.exists()
    
    if bgm and bgm.exists():
        print(f"Background Music: {bgm.name}")
        if has_sfx:
            print(f"SFX Track: {sfx_track.name}")
            cmd = [
                "ffmpeg", "-y", 
                "-i", str(visual_vid), 
                "-i", str(voiceover), 
                "-stream_loop", "-1", "-i", str(bgm),
                "-i", str(sfx_track),
                "-filter_complex", "[1:a]volume=1.0[a1];[2:a]volume=0.08[a2];[3:a]volume=0.5[a3];[a1][a2][a3]amix=inputs=3:duration=first:dropout_transition=1[a]",
                "-map", "0:v:0", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final_vid)
            ]
        else:
            cmd = [
                "ffmpeg", "-y", 
                "-i", str(visual_vid), 
                "-i", str(voiceover), 
                "-stream_loop", "-1", "-i", str(bgm),
                "-filter_complex", "[1:a]volume=1.0[a1];[2:a]volume=0.08[a2];[a1][a2]amix=inputs=2:duration=first:dropout_transition=1[a]",
                "-map", "0:v:0", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final_vid)
            ]
    else:
        print("Background Music: None (Voiceover only)")
        if has_sfx:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(visual_vid),
                "-i", str(voiceover),
                "-i", str(sfx_track),
                "-filter_complex", "[1:a]volume=1.0[a1];[2:a]volume=0.5[a2];[a1][a2]amix=inputs=2:duration=first:dropout_transition=1[a]",
                "-map", "0:v:0", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final_vid)
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(visual_vid),
                "-i", str(voiceover),
                "-c:v", "copy", "-c:a", "aac",
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest", str(final_vid)
            ]
            
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if outro_video:
        prog(0.96, "Appending channel outro video")
        outro_norm = out / "outro_norm.mp4"
        cmd_check = ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "default=noprint_wrappers=1:nokey=1", str(outro_video)]
        try:
            has_audio = "audio" in subprocess.check_output(cmd_check, text=True).lower()
        except Exception:
            has_audio = False
            
        cmd_norm = ["ffmpeg", "-y", "-i", str(outro_video)]
        if not has_audio:
            cmd_norm.extend(["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"])
            
        cmd_norm.extend([
            "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1,setsar=1,fps=24[v]",
            "-map", "[v]",
            "-map", "1:a" if not has_audio else "0:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k"
        ])
        if not has_audio: cmd_norm.append("-shortest")
        cmd_norm.append(str(outro_norm))
        subprocess.run(cmd_norm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        concat_list = out / "concat_outro.txt"
        concat_list.write_text(f"file '{final_vid.name}'\nfile '{outro_norm.name}'\n", encoding="utf-8")
        final_out = out / "final_video_with_outro.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(final_out)], cwd=str(out), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if final_out.exists():
            final_vid.unlink()
            final_out.rename(final_vid)

    prog(0.98, "Cleaning up intermediate assets")
    import shutil
    # Preserve single preview thumbnail for UI, auto-delete individual scene images
    if assets.exists():
        pngs = sorted(assets.glob("*.png"))
        if pngs:
            try: shutil.copy(pngs[0], out / "preview.png")
            except Exception: pass
        try: shutil.rmtree(assets, ignore_errors=True)
        except Exception: pass

    # Auto-delete intermediate audios, temporary concat script, and intermediate video streams
    for f in list(out.glob("audio_*.*")):
        try: f.unlink(missing_ok=True)
        except Exception: pass
    for f in [visual_vid, voiceover, audio_concat]:
        try:
            if f.exists(): f.unlink(missing_ok=True)
        except Exception: pass

    if visual_debug:
        from editorial import write_debug_manifest, build_render_qa_report
        write_debug_manifest(story, out)
        qa = build_render_qa_report(story, out, final_vid)
        (out / "render_qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")

    prog(1.0, "Done")
    print(f"Created: {out}\n")

    if is_viral:
        print(f"\n[PIPELINE]")
        print(f"FINAL TEMPLATE=VIRAL_SHORT_V1\n")
    elif is_editorial:
        print(f"\n[PIPELINE]")
        print(f"FINAL TEMPLATE=EDITORIAL_EXPLAINER\n")
    
    # ── Print Token Usage ──
    attempts = story.get("provider_attempts", [])
    if attempts:
        print("[Token Usage Summary]")
        for att in attempts:
            if att.get("status") == "success" and att.get("tokens", 0) > 0:
                print(f"  - {att['provider'].title()} ({att['detail']}): {att['tokens']} tokens")
        print()
        
    success_flag[0] = True
        
    return out


def main():
    parser = argparse.ArgumentParser(description="AI SIMPLIFIED LAB — Video Factory v2")
    parser.add_argument("--topic", required=True, help="Video topic")
    parser.add_argument("--style", default="auto",
                        choices=["auto", "viral_explainer", "viral_news", "viral_short_v1", "editorial_explainer", "editorial_viral", "explainer", "interview", "list", "comparison"],
                        help="Video style (default: auto-detect from topic)")
    parser.add_argument("--notes", default="", help="Additional context for storyboard")
    parser.add_argument("--duration", type=float, default=30.0, help="Total video seconds")
    parser.add_argument("--intro", type=float, default=1.2, help="Seconds for element animation intro")
    parser.add_argument("--visual-debug", action="store_true", help="Enable visual debugging output")
    args = parser.parse_args()

    if args.duration < 12:
        parser.error("--duration must be at least 12")

    try:
        out = run_pipeline(args.topic, args.style, args.notes, args.duration, args.intro,
                           visual_debug=args.visual_debug,
                           on_progress=lambda f, m: print(f"[{int(f*100):3d}%] {m}"))
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
