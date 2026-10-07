# legacy_adapter.py
"""Legacy Storyboard Adapter.

Converts older widget-based `elements` JSON structures into the new 
dynamic `visual_scene` object for the procedural compositor.
"""

def adapt_scene(scene: dict) -> dict:
    """Adapts a legacy scene to the new compositor schema.

    Viral scenes (kind=viral_short_v1) are returned unchanged \u2014 they have no
    elements array and must NOT be wrapped in a visual_scene block.
    """
    # \u2500\u2500 VIRAL BYPASS: viral scenes use deterministic primitives, not legacy elements
    kind = str(scene.get("kind", "")).lower()
    if kind in ("viral_short_v1", "viral"):
        return scene
    if scene.get("_template_mode") in ("viral_explainer", "viral_news", "viral_short_v1", "editorial_explainer", "editorial_viral"):
        return scene

    # If it's already using the new schema, just return it
    if "visual_scene" in scene:
        return scene

    # If it has no elements, wrap it in an empty visual_scene
    if "elements" not in scene:
        scene["visual_scene"] = {
            "visual_concept": "Empty scene",
            "environment": "Minimalist space",
            "camera_choreography": "static",
            "render_strategy": "cinematic_2d",
            "visual_uniqueness_score": 50,
            "objects": []
        }
        return scene

    # Convert old elements to new objects
    elements = scene.pop("elements")
    objects = []
    
    for el in elements:
        typ = el.get("type", "unknown")
        
        # In the old system, position was a 9-point grid string like "center"
        # We preserve it in 'spatial_relationship' so the compositor can handle it
        pos = el.get("position", "center")
        spatial_rel = f"legacy_grid:{pos}"
        
        motion = el.get("motion", "pop")
        
        new_obj = {
            "type": typ,
            "spatial_relationship": spatial_rel,
            "motion_track": f"legacy_motion:{motion}",
            "text": el.get("text", ""),
            "sync_word": el.get("sync_word", ""),
            "emoji": el.get("emoji", "💡"),
            "persist": el.get("persist", False)
        }
        
        # Carry over legacy specific fields for the compositor to parse
        if "python_draw_code" in el:
            new_obj["python_draw_code"] = el["python_draw_code"]
        for key in ["lines", "value", "label", "subtext", "left", "right", "option_a", "option_b", "layers", "steps", "title", "detail", "input", "process", "output", "message", "color", "font", "filename", "prompt", "w", "h", "r"]:
            if key in el:
                new_obj[key] = el[key]
                
        objects.append(new_obj)

    scene["visual_scene"] = {
        "visual_concept": "Legacy widget layout",
        "environment": "Legacy whiteboard",
        "camera_choreography": "static",
        "render_strategy": "legacy",
        "visual_uniqueness_score": 50,
        "objects": objects
    }
    
    return scene
