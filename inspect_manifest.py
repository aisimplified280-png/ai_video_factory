import json, pathlib, sys

folder_path = sys.argv[1] if len(sys.argv) > 1 else "output/what-is-mcp-model-context-protocol-20260925-162724-775"
folder = pathlib.Path(folder_path)
manifest_file = folder / "manifest.json"
if manifest_file.exists():
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    print(f"Total scenes: {len(manifest.get('scenes', []))}")
    for i, scene in enumerate(manifest.get("scenes", [])):
        v_scene = scene.get("visual_scene", {})
        objs = v_scene.get("objects", []) or scene.get("elements", [])
        print(f"\n--- Scene {i+1} ---")
        print(f"  Narration: {scene.get('narration', '')[:60]}...")
        print(f"  Objects count: {len(objs)}")
        for j, obj in enumerate(objs):
            print(f"    Obj {j+1}: type={obj.get('type')}, text={obj.get('text')}, y={obj.get('y')}")
else:
    print("No manifest.json found in folder", folder)
