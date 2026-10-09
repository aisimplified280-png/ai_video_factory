"""Phase 17 Visual Language Quality Evaluator.

Priority: does the sequence explain the narration clearly?

Evaluates from rendered pixels:
1. Subject presence: the explained content actually occupies the frame.
2. Depth & Parallax: verified depth strategy and multi-layer composition evidence.
3. Transition continuity: simple cuts/dissolves are correct; only unsupported intents fail.
4. Layout progression: advisory — two scenes may legitimately look alike when the
   explanation requires it (clarity beats variety).
5. Perceived production quality: typography hierarchy, contrast, intentional whitespace.

Evidence-based & Fail-closed:
- Evaluates actual encoded frame pixels.
- Fails closed if frame evidence is missing entirely.
- A calm, mostly-static explanatory scene is NOT a failure (§14): motion is never a floor.
- Produces structured scene-level evidence with motion_delta, layout_signature, and background_similarity.
  Observations that do not block comprehension are reported as advisory notes, not rejections.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Sequence
from PIL import Image, ImageStat

from .transition_director import FORBIDDEN_TRANSITIONS, ALLOWED_TRANSITIONS


@dataclass
class VisualLanguageEvaluation:
    environment_variety_score: float   # 0-10: Max 8s per background
    depth_parallax_score: float        # 0-10: Multi-layer depth presence
    transition_score: float            # 0-10: Transformative transitions
    scale_progression_score: float     # 0-10: Micro -> Machine -> Fleet -> Brand
    cinematic_feel_score: float        # 0-10: Contrast, typography, lighting
    visual_language_score: float       # 0-10: Composite weighted score
    passed: bool
    rejection_reasons: list[str] = field(default_factory=list)
    advisory_notes: list[str] = field(default_factory=list)
    scene_evaluations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment_variety_score": round(self.environment_variety_score, 2),
            "depth_parallax_score": round(self.depth_parallax_score, 2),
            "transition_score": round(self.transition_score, 2),
            "scale_progression_score": round(self.scale_progression_score, 2),
            "cinematic_feel_score": round(self.cinematic_feel_score, 2),
            "visual_language_score": round(self.visual_language_score, 2),
            "passed": self.passed,
            "rejection_reasons": self.rejection_reasons,
            "advisory_notes": self.advisory_notes,
            "scene_evaluations": self.scene_evaluations,
        }


def _gray_values(image: Image.Image, size: tuple[int, int] = (96, 170)) -> list[int]:
    """Return flattened grayscale pixel values for fast comparative analysis."""
    return list(image.convert("L").resize(size, Image.Resampling.BILINEAR).getdata())


def _frame_difference(img1: Image.Image, img2: Image.Image) -> float:
    """Compute average absolute pixel difference between two images (0.0 to 255.0)."""
    vals1 = _gray_values(img1)
    vals2 = _gray_values(img2)
    if not vals1 or not vals2:
        return 0.0
    return sum(abs(a - b) for a, b in zip(vals1, vals2)) / max(1, len(vals1))


def _compute_histogram_correlation(img1: Image.Image, img2: Image.Image) -> float:
    """Compute Pearson correlation coefficient between two 64-bin grayscale histograms."""
    h1 = img1.convert("L").histogram()
    h2 = img2.convert("L").histogram()
    s1 = sum(h1) or 1
    s2 = sum(h2) or 1
    norm1 = [v / s1 for v in h1]
    norm2 = [v / s2 for v in h2]
    mean1 = sum(norm1) / len(norm1)
    mean2 = sum(norm2) / len(norm2)
    num = sum((a - mean1) * (b - mean2) for a, b in zip(norm1, norm2))
    den1 = math.sqrt(sum((a - mean1) ** 2 for a in norm1))
    den2 = math.sqrt(sum((b - mean2) ** 2 for b in norm2))
    if den1 == 0 or den2 == 0:
        return 0.0
    return max(-1.0, min(1.0, num / (den1 * den2)))


def _layout_signature(img: Image.Image) -> str:
    """Compute a 4-quadrant layout signature representing spatial mass distribution."""
    gray = img.convert("L").resize((100, 100), Image.Resampling.BILINEAR)
    w, h = gray.size
    mid_x, mid_y = w // 2, h // 2
    q1 = ImageStat.Stat(gray.crop((0, 0, mid_x, mid_y))).mean[0]
    q2 = ImageStat.Stat(gray.crop((mid_x, 0, w, mid_y))).mean[0]
    q3 = ImageStat.Stat(gray.crop((0, mid_y, mid_x, h))).mean[0]
    q4 = ImageStat.Stat(gray.crop((mid_x, mid_y, w, h))).mean[0]
    return f"Q1:{q1:.1f}|Q2:{q2:.1f}|Q3:{q3:.1f}|Q4:{q4:.1f}"


def _background_similarity(img1: Image.Image, img2: Image.Image) -> float:
    """Compute visual similarity of outer border/background zones between two frames."""
    w, h = 100, 100
    g1 = img1.convert("L").resize((w, h), Image.Resampling.BILINEAR)
    g2 = img2.convert("L").resize((w, h), Image.Resampling.BILINEAR)
    # Outer margins (top 20% and bottom 20%)
    top1 = g1.crop((0, 0, w, 20))
    top2 = g2.crop((0, 0, w, 20))
    bot1 = g1.crop((0, 80, w, h))
    bot2 = g2.crop((0, 80, w, h))
    corr_top = max(0.0, _compute_histogram_correlation(top1, top2))
    corr_bot = max(0.0, _compute_histogram_correlation(bot1, bot2))
    return round((corr_top + corr_bot) / 2.0, 3)


def _measure_layer_occupancy(img: Image.Image) -> float:
    """Measure structural content occupancy from contrast variance.

    A blank frame measures 0 — an empty render must never read as "healthy depth".
    """
    stat = ImageStat.Stat(img.convert("L"))
    std = stat.stddev[0]
    return min(100.0, max(0.0, round(std * 1.5, 2)))


def _find_frame_files(search_dirs: list[Path]) -> list[Path]:
    """Find all rendered frame images in given candidate directories."""
    frames: list[Path] = []
    for d in search_dirs:
        if d.is_dir():
            found = sorted([p for p in d.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg")])
            if found:
                frames.extend(found)
    return sorted(list(dict.fromkeys(frames)), key=lambda p: p.name)


def evaluate_visual_language(
    project_root: Path,
    scenes_data: list[dict[str, Any]],
    timeline_events: list[dict[str, Any]],
    frames_dir: Path | None = None,
    video_path: Path | None = None,
) -> VisualLanguageEvaluation:
    """Evaluates the perceived cinematic visual language of a production.

    FAIL-CLOSED: If no frame evidence exists at all, evaluation fails.
    Static explanatory scenes and simple cuts are valid outcomes, not failures.
    """
    rejection_reasons: list[str] = []
    advisory_notes: list[str] = []
    scene_evals: list[dict[str, Any]] = []

    # 1. Locate Frame Samples
    if frames_dir and Path(frames_dir).is_dir():
        frame_files = _find_frame_files([Path(frames_dir), Path(frames_dir) / "frame_samples"])
    else:
        candidate_dirs = [
            project_root / "qa" / "frame_samples",
            project_root / "qa" / "frames",
            project_root / "qa",
            project_root,
        ]
        frame_files = _find_frame_files(candidate_dirs)

    # FAIL-CLOSED: No frame evidence available
    if not frame_files:
        return VisualLanguageEvaluation(
            environment_variety_score=0.0,
            depth_parallax_score=0.0,
            transition_score=0.0,
            scale_progression_score=0.0,
            cinematic_feel_score=0.0,
            visual_language_score=0.0,
            passed=False,
            rejection_reasons=["No visual frame evidence available: cannot evaluate visual language without rendered frames."],
            scene_evaluations=[],
        )

    # 2. Scene-Level Evidence Mapping
    num_scenes = max(1, len(scenes_data))
    # Map frames to scenes
    scene_frames_map: dict[str, list[Path]] = {
        sc.get("scene_id", f"scene_{idx+1:02d}"): [] for idx, sc in enumerate(scenes_data)
    }

    # Attempt smart matching by scene_id in filename, otherwise partition frames across scenes
    matched_any = False
    for f in frame_files:
        for sc_id in scene_frames_map:
            if sc_id in f.stem:
                scene_frames_map[sc_id].append(f)
                matched_any = True
                break

    if not matched_any:
        # Partition sequential frames across scenes
        chunk_size = max(1, len(frame_files) // num_scenes)
        scene_ids = list(scene_frames_map.keys())
        for idx, sc_id in enumerate(scene_ids):
            start_i = idx * chunk_size
            end_i = (idx + 1) * chunk_size if idx < num_scenes - 1 else len(frame_files)
            assigned = frame_files[start_i:end_i]
            if not assigned and frame_files:
                assigned = [frame_files[min(idx, len(frame_files) - 1)]]
            scene_frames_map[sc_id] = assigned

    # Load and evaluate scene frames
    prev_scene_last_img: Image.Image | None = None
    all_motion_deltas: list[float] = []
    all_layout_signatures: list[str] = []
    static_scenes_count = 0
    near_identical_transitions = 0

    for idx, sc in enumerate(scenes_data):
        sc_id = sc.get("scene_id", f"scene_{idx+1:02d}")
        sc_frames = scene_frames_map.get(sc_id, [])
        if not sc_frames and frame_files:
            sc_frames = [frame_files[min(idx, len(frame_files) - 1)]]

        # Open images for this scene
        images = []
        for fp in sc_frames:
            try:
                images.append(Image.open(fp))
            except Exception:
                pass

        if not images:
            # Fallback to single frame if open failed
            images = [Image.new("RGB", (100, 100), color="black")]

        # Measure motion delta within scene
        if len(images) >= 2:
            deltas = [_frame_difference(images[i], images[i + 1]) for i in range(len(images) - 1)]
            scene_motion_delta = sum(deltas) / len(deltas)
        elif prev_scene_last_img is not None:
            scene_motion_delta = _frame_difference(prev_scene_last_img, images[0])
        else:
            scene_motion_delta = 5.0  # single first frame baseline

        all_motion_deltas.append(scene_motion_delta)

        # Layout signature & occupancy
        key_img = images[len(images) // 2]
        layout_sig = _layout_signature(key_img)
        all_layout_signatures.append(layout_sig)
        occupancy = _measure_layer_occupancy(key_img)

        # Background similarity with previous scene
        if prev_scene_last_img is not None:
            bg_sim = _background_similarity(prev_scene_last_img, images[0])
            boundary_delta = _frame_difference(prev_scene_last_img, images[0])
            if boundary_delta < 3.0:
                near_identical_transitions += 1
        else:
            bg_sim = 0.0

        prev_scene_last_img = images[-1]

        # §14: a still explanatory scene is valid. Motion is evidence, never a floor.
        is_static = len(images) >= 2 and scene_motion_delta < 2.0
        if is_static:
            static_scenes_count += 1
            advisory_notes.append(
                f"Scene {sc_id} is still (motion delta {scene_motion_delta:.2f}) — appropriate when the narration states one idea."
            )

        # Scene score: how much explained content is present; motion contributes only a little.
        scene_score = min(10.0, max(2.0, 7.0 + min(2.0, occupancy / 30.0) + min(1.0, scene_motion_delta / 12.0)))

        scene_evals.append({
            "scene_id": sc_id,
            "score": round(scene_score, 2),
            "evidence": {
                "frame_samples": [p.name for p in sc_frames],
                "motion_delta": round(scene_motion_delta, 2),
                "layout_signature": layout_sig,
                "background_similarity": round(bg_sim, 2),
                "layer_occupancy": round(occupancy, 2),
                "is_static": is_static,
            },
        })

    # 3. Environment Variety Score (Pixel-evidence + Metadata)
    env_durations: dict[str, float] = {}
    for sc in scenes_data:
        env = sc.get("environment", "default")
        start = sc.get("start", sc.get("start_seconds", 0.0))
        end = sc.get("end", sc.get("end_seconds", 5.0))
        dur = end - start
        env_durations[env] = env_durations.get(env, 0.0) + dur

    longest_env = max(env_durations.values(), default=0.0)
    if longest_env > 8.0:
        advisory_notes.append(f"Environment persists for {longest_env:.1f}s (editorial guideline is 8.0s).")
        env_score = max(6.0, 10.0 - (longest_env - 8.0) * 0.3)
    else:
        env_score = 9.8

    # Check for visual environment repetition from evidence
    avg_bg_sim = sum(ev["evidence"]["background_similarity"] for ev in scene_evals[1:]) / max(1, len(scene_evals) - 1)
    if avg_bg_sim > 0.85:
        env_score = min(env_score, 7.0)
        advisory_notes.append(f"Successive scenes share a similar background ({avg_bg_sim:.2f}); acceptable when the subject is continuous.")

    # 4. Depth & Parallax Verification (Pixel contrast + Strategy)
    depth_strategies = [sc.get("depth_strategy") for sc in scenes_data]
    has_layered_depth = any("background" in str(d).lower() and "foreground" in str(d).lower() for d in depth_strategies)
    avg_occupancy = sum(ev["evidence"]["layer_occupancy"] for ev in scene_evals) / max(1, len(scene_evals))

    if not has_layered_depth:
        rejection_reasons.append("Missing 3-layer parallax depth strategy in metadata.")
        depth_score = 4.0
    elif avg_occupancy < 1.0:
        # Nothing is depicted at all. This fails regardless of motion: the explained
        # subject must be visible (§21). Stillness alone is never the problem (§14).
        rejection_reasons.append(
            f"No visual content detected (occupancy {avg_occupancy:.1f}%): the frames are empty, so the explained subject is missing."
        )
        depth_score = 3.0
    elif avg_occupancy < 5.0:
        # §4: don't fill empty space — but the explained subject must be readable.
        advisory_notes.append(f"Low content occupancy ({avg_occupancy:.1f}%): the subject may be too small to read.")
        depth_score = 6.0
    else:
        depth_score = min(10.0, 8.5 + (avg_occupancy / 50.0))

    # 5. Transition continuity: simple cuts/dissolves are correct for explanation (§16).
    transitions_used = [ev.get("transition_in") for ev in timeline_events if ev.get("transition_in")]
    bad_transitions = [t for t in transitions_used if str(t).lower() in FORBIDDEN_TRANSITIONS]
    if bad_transitions:
        rejection_reasons.append(f"Unresolvable transitions detected: {bad_transitions}")
        trans_score = max(2.0, 10.0 - len(bad_transitions) * 2.5)
    elif near_identical_transitions > 0:
        advisory_notes.append(
            f"{near_identical_transitions} scene boundaries changed very little in pixels — fine when the subject is continuous."
        )
        trans_score = 8.0
    else:
        trans_score = 9.5

    # 6. Layout progression & cinematic feel from frame pixels (variety is advisory, §6)
    unique_layouts = len(set(all_layout_signatures))
    layout_diversity_ratio = unique_layouts / max(1, len(all_layout_signatures))
    if layout_diversity_ratio < 0.4:
        advisory_notes.append("Scenes share a similar layout — allowed when the explanation repeats a relationship.")
        scale_score = 7.0
    else:
        scale_score = min(10.0, 7.5 + (layout_diversity_ratio * 2.5))

    # Cinematic feel from pixel luminance contrast
    stats = []
    for fp in frame_files[:20]:
        try:
            im = Image.open(fp).convert("L")
            st = ImageStat.Stat(im)
            stats.append({"mean": st.mean[0], "stddev": st.stddev[0]})
        except Exception:
            pass

    if stats:
        avg_stddev = sum(s["stddev"] for s in stats) / len(stats)
        cinematic_score = round(min(10.0, max(5.0, 6.5 + (avg_stddev / 18.0))), 2)
        if avg_occupancy < 1.0:
            # No contrast anywhere: there is no picture to grade.
            cinematic_score = 2.0
    else:
        cinematic_score = 5.0

    # No global penalty for stillness: §14 explicitly permits static explanatory scenes.

    # Composite Visual Language Score
    # 25% Environment + 25% Depth + 25% Transitions + 15% Scale + 10% Cinematic
    vl_score = (
        0.25 * env_score
        + 0.25 * depth_score
        + 0.25 * trans_score
        + 0.15 * scale_score
        + 0.10 * cinematic_score
    )

    passed = len(rejection_reasons) == 0 and vl_score >= 8.0

    return VisualLanguageEvaluation(
        environment_variety_score=round(env_score, 2),
        depth_parallax_score=round(depth_score, 2),
        transition_score=round(trans_score, 2),
        scale_progression_score=round(scale_score, 2),
        cinematic_feel_score=round(cinematic_score, 2),
        visual_language_score=round(vl_score, 2),
        passed=passed,
        rejection_reasons=rejection_reasons,
        advisory_notes=advisory_notes,
        scene_evaluations=scene_evals,
    )

