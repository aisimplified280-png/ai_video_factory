import re

def refactor():
    with open("create_short.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace make_video_from_frames
    old_make_video = re.search(r"def make_video_from_frames.*?def generate_tts", content, re.DOTALL)
    new_make_video = """def concat_visual_scenes(scene_mp4s, target, transitions=None, on_progress=None):
    import subprocess
    if not scene_mp4s:
        raise ValueError("No scenes to concatenate")
    if len(scene_mp4s) == 1:
        import shutil
        shutil.copy(scene_mp4s[0], target)
        return

    if on_progress:
        on_progress(0.55, "Concatenating scenes with FFmpeg")
        
    concat_list = target.with_name("concat_visuals.txt")
    lines = [f"file '{p.name}'" for p in scene_mp4s]
    concat_list.write_text("\\n".join(lines), encoding="utf-8")
    
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", 
           "-i", str(concat_list), "-c", "copy", str(target)]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, cwd=str(target.parent))
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="ignore") if e.stderr else "Unknown error"
        raise RuntimeError(f"FFmpeg concat failed:\\n{err}")
    finally:
        try: concat_list.unlink(missing_ok=True)
        except Exception: pass

def generate_tts"""
    if old_make_video:
        content = content.replace(old_make_video.group(0), new_make_video)

    # 2. Replace the scene loop logic
    old_scene_loop = re.search(r"        prog\(base \+ 0\.1, f\"Scene \{idx\+1\}/\{total_scenes\}: \{scene\.get\('kind','scene'\)\} thumbnail\"\).*?all_scene_frames\.append\(frames\)", content, re.DOTALL)
    
    new_scene_loop = """        prog(base + 0.1, f"Scene {idx+1}/{total_scenes}: {scene.get('kind','scene')} thumbnail")
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
            
        all_scene_mp4s.append(scene_mp4)"""
    
    if old_scene_loop:
        content = content.replace(old_scene_loop.group(0), new_scene_loop)

    # 3. Rename all_scene_frames initialization
    content = content.replace("all_scene_frames = []", "all_scene_mp4s = []")

    # 4. Call concat_visual_scenes instead of make_video_from_frames
    content = content.replace("make_video_from_frames(all_scene_frames, total_frames, visual_vid, transitions=transitions, on_progress=enc_prog)", "concat_visual_scenes(all_scene_mp4s, visual_vid, transitions=transitions, on_progress=enc_prog)")

    with open("create_short.py", "w", encoding="utf-8") as f:
        f.write(content)
        print("Successfully updated create_short.py")

if __name__ == "__main__":
    refactor()
