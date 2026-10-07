"""Extract full-video editorial QA artifacts from a rendered generation."""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_TIMES = list(range(0, 37, 3))
CONTACT_WIDTH = 300
CONTACT_HEIGHT = 533


def _run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stderr}")
    return result


def _probe(video_path):
    result = _run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_type,codec_name,width,height,sample_rate,channels",
        "-of", "json", str(video_path),
    ])
    return json.loads(result.stdout)


def _extract_frame(video_path, timestamp, target):
    _run([
        "ffmpeg", "-y", "-loglevel", "error", "-ss", f"{timestamp:.3f}",
        "-i", str(video_path), "-frames:v", "1", str(target),
    ])


def _extract_motion_frames(video_path, target_dir):
    target_dir.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(video_path),
        "-vf", "fps=2,scale=96:170:flags=area",
        str(target_dir / "frame_%04d.png"),
    ])
    return sorted(target_dir.glob("frame_*.png"))


def _gray_values(image):
    return list(image.convert("L").resize((96, 170), Image.Resampling.BILINEAR).get_flattened_data())


def _frame_delta(first, second):
    first_values = _gray_values(first)
    second_values = _gray_values(second)
    return sum(abs(a - b) for a, b in zip(first_values, second_values)) / max(1, len(first_values))


def _dark_ink_percent(image):
    pixels = list(image.convert("RGB").resize((160, 284), Image.Resampling.BILINEAR).get_flattened_data())
    dark = sum(1 for red, green, blue in pixels if max(red, green, blue) < 95)
    return round(100 * dark / max(1, len(pixels)), 3)


def _audio_window_metrics(video_path, start, duration):
    command = [
        "ffmpeg", "-hide_banner", "-ss", f"{start:.3f}", "-t", f"{duration:.3f}",
        "-i", str(video_path), "-af", "volumedetect,silencedetect=noise=-45dB:d=0.25",
        "-f", "null", "-",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    log = result.stderr
    mean_match = re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB", log)
    max_match = re.search(r"max_volume:\s*(-?[\d.]+)\s*dB", log)
    silence = re.findall(r"silence_start:\s*([\d.]+)|silence_end:\s*([\d.]+)", log)
    return {
        "mean_volume_db": float(mean_match.group(1)) if mean_match else None,
        "max_volume_db": float(max_match.group(1)) if max_match else None,
        "silence_markers": [float(value) for pair in silence for value in pair if value],
        "probe_return_code": result.returncode,
    }


def _build_contact_sheet(samples, target):
    columns = 4
    rows = math.ceil(len(samples) / columns)
    cell_height = CONTACT_HEIGHT + 42
    sheet = Image.new("RGB", (columns * CONTACT_WIDTH, rows * cell_height), "#E8EDF4")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, (timestamp, path) in enumerate(samples):
        x = (index % columns) * CONTACT_WIDTH
        y = (index // columns) * cell_height
        image = Image.open(path).convert("RGB")
        image.thumbnail((CONTACT_WIDTH, CONTACT_HEIGHT), Image.Resampling.LANCZOS)
        sheet.paste(image, (x, y + 28))
        draw.text((x + 10, y + 7), f"{timestamp:.0f}s", fill="#132238", font=font)
    sheet.save(target)


def analyze_generation(output_dir: Path):
    output_dir = output_dir.resolve()
    video_path = output_dir / "final_video.mp4"
    manifest_path = output_dir / "manifest.json"
    if not video_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(f"Expected final_video.mp4 and manifest.json in {output_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    probe = _probe(video_path)
    duration = float(probe["format"]["duration"])
    qa_dir = output_dir / "qa"
    frame_dir = qa_dir / "frame_samples"
    frame_dir.mkdir(parents=True, exist_ok=True)

    sample_records = []
    for timestamp in SAMPLE_TIMES:
        if timestamp > duration:
            continue
        actual_time = min(float(timestamp), max(0.0, duration - 0.05))
        frame_path = frame_dir / f"frame_{timestamp:02d}s.png"
        _extract_frame(video_path, actual_time, frame_path)
        sample_records.append((actual_time, frame_path))
    _build_contact_sheet(sample_records, qa_dir / "contact_sheet.png")

    scene_records = []
    all_shots = []
    layout_counts = {}
    for index, scene in enumerate(manifest.get("scenes", [])):
        plan = scene.get("render_plan") or {}
        layout = plan.get("layout_family") or (plan.get("layout") or {}).get("family") or "unknown"
        layout_counts[layout] = layout_counts.get(layout, 0) + 1
        sidecar = output_dir / f"scene_{index:02d}.render_manifest.json"
        execution = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {}
        start = float(scene.get("start_seconds", 0.0))
        end = float(scene.get("end_seconds", start))
        scene_records.append({
            "index": index,
            "role": scene.get("role"),
            "headline": scene.get("headline"),
            "narration": scene.get("narration", ""),
            "start": start,
            "end": end,
            "duration": round(end - start, 3),
            "layout": layout,
            "primitive": plan.get("primitive"),
            "action": plan.get("action"),
            "motion": (plan.get("motion") or {}).get("primary"),
            "camera": (plan.get("camera") or {}).get("behavior"),
            "legacy_template_bypassed": execution.get("legacy_template_bypassed"),
            "shots_executed": execution.get("shots_executed", []),
        })
        for shot in execution.get("shots_executed", []):
            all_shots.append({
                "scene_index": index,
                "start": round(start + float(shot.get("start", 0.0)), 3),
                "end": round(start + float(shot.get("end", 0.0)), 3),
                "focus": shot.get("focus"),
                "visual_story": shot.get("visual_story"),
                "action": shot.get("action"),
            })

    ordered_scenes = sorted(scene_records, key=lambda item: item["start"])
    gaps = []
    overlaps = []
    for left, right in zip(ordered_scenes, ordered_scenes[1:]):
        delta = round(right["start"] - left["end"], 3)
        if delta > 0.05:
            gaps.append({"after_scene": left["index"], "seconds": delta})
        elif delta < -0.05:
            overlaps.append({"scenes": [left["index"], right["index"]], "seconds": abs(delta)})
    timeline = {
        "duration": duration,
        "scene_count": len(scene_records),
        "scene_coverage_seconds": round(sum(item["duration"] for item in scene_records), 3),
        "gaps": gaps,
        "overlaps": overlaps,
        "full_coverage": not gaps and not overlaps and bool(ordered_scenes)
        and ordered_scenes[0]["start"] <= 0.05
        and abs(ordered_scenes[-1]["end"] - duration) <= 0.25,
        "scenes": scene_records,
        "shots": all_shots,
    }
    (qa_dir / "timeline_analysis.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")

    image_deltas = []
    ink_density = []
    for _, sample_path in sample_records:
        ink_density.append(_dark_ink_percent(Image.open(sample_path)))
    for left, right in zip(sample_records, sample_records[1:]):
        image_deltas.append(_frame_delta(Image.open(left[1]), Image.open(right[1])))
    with tempfile.TemporaryDirectory(prefix="editorial-qa-") as temporary:
        motion_paths = _extract_motion_frames(video_path, Path(temporary))
        motion_deltas = [
            _frame_delta(Image.open(left), Image.open(right))
            for left, right in zip(motion_paths, motion_paths[1:])
        ]
    motion_active_threshold = 1.5
    active_motion = [value for value in motion_deltas if value >= motion_active_threshold]
    layout_unique = len(layout_counts)
    layout_diversity = 100 * layout_unique / max(1, len(scene_records))
    repeated_scene_fraction = max(0, len(scene_records) - layout_unique) / max(1, len(scene_records))
    visual_diversity = min(100.0, round(0.65 * layout_diversity + 0.35 * min(100, (sum(image_deltas) / max(1, len(image_deltas))) * 1.8), 1))
    visual_report = {
        "layout_counts": layout_counts,
        "unique_layout_count": layout_unique,
        "layout_diversity_percent": round(layout_diversity, 1),
        "layout_repetition_percent": round(100 * repeated_scene_fraction, 1),
        "sample_times_seconds": [round(time, 2) for time, _ in sample_records],
        "adjacent_sample_mean_absolute_luma_deltas": [round(value, 2) for value in image_deltas],
        "motion_sampling_fps": 2,
        "motion_frame_pairs": len(motion_deltas),
        "motion_active_pairs": len(active_motion),
        "motion_active_percent": round(100 * len(active_motion) / max(1, len(motion_deltas)), 1),
        "motion_mean_luma_delta": round(sum(motion_deltas) / max(1, len(motion_deltas)), 2),
        "text_density_proxy": "percent of downsampled pixels with all RGB channels below 95; OCR not installed",
        "sampled_dark_ink_pixel_percent": ink_density,
        "mean_dark_ink_pixel_percent": round(sum(ink_density) / max(1, len(ink_density)), 2),
        "score": visual_diversity,
        "score_note": "Heuristic only; layout variety and image deltas do not establish semantic alignment.",
    }
    (qa_dir / "visual_diversity.json").write_text(json.dumps(visual_report, indent=2), encoding="utf-8")

    audio_streams = [stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"]
    last_scene = scene_records[-1] if scene_records else {}
    cta_start = float(last_scene.get("start", duration))
    cta_duration = max(0.1, min(duration - cta_start, float(last_scene.get("duration", 0.1))))
    cta_audio = _audio_window_metrics(video_path, cta_start, cta_duration) if audio_streams else {}
    cta_text = str(last_scene.get("narration", ""))
    cta_brand = "AI Simplified Lab" in cta_text
    audio_report = {
        "audio_stream_present": bool(audio_streams),
        "audio_streams": audio_streams,
        "cta_window": {"start": cta_start, "duration": cta_duration, **cta_audio},
        "cta_voice_activity_detected": bool(cta_audio.get("max_volume_db") is not None and cta_audio["max_volume_db"] > -35),
        "cta_narration_contains_subscribe_brand": bool(re.search(r"subscribe.*AI Simplified Lab", cta_text, re.I)),
        "cta_asr_verified": False,
        "asr_note": "No local speech-recognition package is installed; source narration and CTA-window audio activity are verified, exact words in muxed audio are not transcribed.",
    }
    (qa_dir / "audio_analysis.json").write_text(json.dumps(audio_report, indent=2), encoding="utf-8")

    video_streams = [stream for stream in probe.get("streams", []) if stream.get("codec_type") == "video"]
    assembly_ok = bool(video_streams and audio_streams and abs(duration - float(ordered_scenes[-1]["end"])) <= 0.25) if ordered_scenes else False
    all_bypassed = bool(scene_records) and all(item["legacy_template_bypassed"] is True for item in scene_records)
    scorecard = {
        "semantic_alignment": None,
        "visual_diversity": visual_report["score"],
        "layout_repetition": visual_report["layout_repetition_percent"],
        "motion_quality": visual_report["motion_active_percent"],
        "text_density": visual_report["mean_dark_ink_pixel_percent"],
        "shot_rhythm": 100.0 if timeline["full_coverage"] and all_shots else 0.0,
        "cta_presence": 100.0 if cta_brand and "subscribe" in str(last_scene.get("headline", "")).lower() else 0.0,
        "audio_presence": 100.0 if audio_report["audio_stream_present"] and audio_report["cta_voice_activity_detected"] else 0.0,
        "assembly_integrity": 100.0 if assembly_ok else 0.0,
    }
    qa_report = {
        "video": str(video_path.relative_to(ROOT)).replace("\\", "/"),
        "style": manifest.get("style"),
        "template_mode": manifest.get("template_mode"),
        "duration_seconds": duration,
        "resolution": f"{video_streams[0].get('width')}x{video_streams[0].get('height')}" if video_streams else None,
        "scene_count": len(scene_records),
        "legacy_template_bypassed": all_bypassed,
        "cta": {
            "last_scene": last_scene.get("index"),
            "last_scene_role": last_scene.get("role"),
            "headline": last_scene.get("headline"),
            "narration": cta_text,
            "source_script_contains_brand_subscribe": cta_brand,
            "cta_audio_window_has_voice_activity": audio_report["cta_voice_activity_detected"],
            "spoken_words_asr_verified": False,
        },
        "timeline_full_coverage": timeline["full_coverage"],
        "scores": scorecard,
        "manual_review_required": [
            "semantic_alignment: automated image metrics cannot establish that every visual explains its narration",
            "text_density: reported as dark-pixel proxy because OCR is unavailable",
            "CTA spoken wording: audio activity and narration source verified, but no ASR transcription was available",
            "transitions: contact sheet samples at 3-second intervals; transitions need frame-by-frame human review",
        ],
        "artifacts": [
            "frame_samples/", "contact_sheet.png", "visual_diversity.json",
            "timeline_analysis.json", "audio_analysis.json", "final_qa_report.json",
        ],
    }
    (qa_dir / "final_qa_report.json").write_text(json.dumps(qa_report, indent=2), encoding="utf-8")
    print(json.dumps({"qa_dir": str(qa_dir), "scorecard": scorecard, "cta_audio": cta_audio}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, help="Generation directory; defaults to newest output with final_video.mp4")
    args = parser.parse_args()
    if args.output_dir:
        output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    else:
        output_dirs = [path for path in (ROOT / "output").iterdir() if (path / "final_video.mp4").is_file()]
        if not output_dirs:
            raise FileNotFoundError("No output directory with final_video.mp4 found")
        output_dir = max(output_dirs, key=lambda path: path.stat().st_mtime)
    analyze_generation(output_dir)


if __name__ == "__main__":
    main()