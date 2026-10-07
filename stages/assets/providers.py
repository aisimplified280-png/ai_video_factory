"""Asset generation provider adapters, native diagram engine, and deterministic caching."""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from PIL import Image, ImageDraw, ImageFont

from .asset_manifest import AssetItem


@runtime_checkable
class AssetProvider(Protocol):
    """Protocol for concrete asset generation or retrieval providers."""
    name: str

    def is_available(self) -> bool:
        ...

    def generate(self, item: AssetItem, output_dir: Path) -> dict[str, Any]:
        """Execute asset generation. Return result dict with file_path, cost, latency."""
        ...


class AssetCache:
    """Deterministic local cache for generated or fetched assets."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def compute_cache_key(self, item: AssetItem) -> str:
        content = f"{item.provider}:{item.model}:{item.prompt}:{item.type}:{item.subject}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, item: AssetItem) -> Path | None:
        key = self.compute_cache_key(item)
        cached_file = self.cache_dir / f"{key[:16]}_{item.asset_id}.png"
        if cached_file.exists() and cached_file.stat().st_size > 0:
            return cached_file
        return None

    def put(self, item: AssetItem, source_file: Path) -> Path:
        key = self.compute_cache_key(item)
        cached_file = self.cache_dir / f"{key[:16]}_{item.asset_id}{source_file.suffix}"
        if source_file.resolve() != cached_file.resolve():
            import shutil
            shutil.copy2(source_file, cached_file)
        return cached_file


class NativeDiagramProvider:
    """Generates crisp native vector and raster technical diagrams, flowcharts, and dashboards."""
    name = "native_diagram"

    def is_available(self) -> bool:
        return True

    def generate(self, item: AssetItem, output_dir: Path) -> dict[str, Any]:
        start_t = time.time()
        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / f"{item.asset_id}.png"

        # Generate 1080x1920 (9:16 vertical) technical diagram
        width, height = 1080, 1920
        spec = item.diagram_spec or {}
        bg_hex = spec.get("background_color", "#0A0D14")
        accent_hex = spec.get("color_accent", "#38BDF8")

        img = Image.new("RGB", (width, height), color=bg_hex)
        draw = ImageDraw.Draw(img)

        # Draw subtle technical grid background
        grid_step = 80
        for x in range(0, width, grid_step):
            draw.line([(x, 0), (x, height)], fill="#141B2D", width=1)
        for y in range(0, height, grid_step):
            draw.line([(0, y), (width, y)], fill="#141B2D", width=1)

        # Header section
        draw.rectangle([(60, 120), (width - 60, 240)], fill="#111827", outline=accent_hex, width=2)
        title_text = spec.get("subject", item.subject).upper()
        draw.text((100, 155), title_text[:38], fill="#F8FAFC")
        draw.text((100, 195), f"TECHNIQUE: {item.metadata.get('visual_technique', 'SYSTEM_ASSEMBLY').upper()}", fill=accent_hex)

        # Draw core system nodes & connections
        nodes = spec.get("nodes", [
            {"id": "n1", "label": item.subject, "type": "primary"},
            {"id": "n2", "label": "Operational Load", "type": "metric"},
            {"id": "n3", "label": "Telemetry Output", "type": "flow"},
        ])

        y_positions = [480, 880, 1280]
        for i, node in enumerate(nodes[:3]):
            ny = y_positions[i]
            box = [(120, ny), (width - 120, ny + 220)]
            node_fill = "#1E293B" if node.get("type") != "primary" else "#0F2642"
            border_color = accent_hex if node.get("type") == "primary" else "#64748B"
            
            draw.rectangle(box, fill=node_fill, outline=border_color, width=3)
            draw.text((160, ny + 40), f"[{node.get('type', 'NODE').upper()}]", fill=accent_hex)
            draw.text((160, ny + 90), str(node.get("label", "Subsystem")), fill="#FFFFFF")
            draw.text((160, ny + 145), f"STATE: {item.subject_action[:45]}", fill="#94A3B8")

            # Connector arrows between nodes
            if i < len(nodes[:3]) - 1:
                next_y = y_positions[i + 1]
                mid_x = width // 2
                draw.line([(mid_x, ny + 220), (mid_x, next_y)], fill=accent_hex, width=4)
                # Arrowhead
                draw.polygon([
                    (mid_x - 12, next_y - 20),
                    (mid_x + 12, next_y - 20),
                    (mid_x, next_y),
                ], fill=accent_hex)

        # Footer telemetry signature
        draw.rectangle([(60, height - 200), (width - 60, height - 100)], fill="#0B132B", outline="#1E293B", width=1)
        draw.text((100, height - 165), "AI SIMPLIFIED LAB // ARCHITECTURAL SCHEMATIC ENGINE v2.0", fill="#64748B")

        img.save(out_file, format="PNG")
        dur = time.time() - start_t
        return {
            "success": True,
            "file_path": str(out_file),
            "cost_usd": 0.0,
            "latency": dur,
            "provider": self.name,
            "model": "native_pil_svg",
        }


class LocalLibraryProvider:
    """Provides local channel branding, logos, and curated library assets."""
    name = "local_library"

    def is_available(self) -> bool:
        return True

    def generate(self, item: AssetItem, output_dir: Path) -> dict[str, Any]:
        start_t = time.time()
        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / f"{item.asset_id}.png"

        # Check if branding asset already exists in assets_library/
        branding_dir = Path(__file__).resolve().parent.parent.parent / "assets_library"
        candidates = list(branding_dir.glob("*logo*.png")) + list(branding_dir.glob("*brand*.png"))
        
        if candidates and candidates[0].exists():
            import shutil
            shutil.copy2(candidates[0], out_file)
        else:
            # Generate clean high-contrast branded card
            width, height = 1080, 1920
            img = Image.new("RGB", (width, height), color="#090D16")
            draw = ImageDraw.Draw(img)

            # Central brand medallion
            cx, cy = width // 2, height // 2 - 100
            r = 220
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill="#0F172A", outline="#00FF88", width=6)
            draw.text((cx - 120, cy - 30), "AI SIMPLIFIED", fill="#FFFFFF")
            draw.text((cx - 40, cy + 20), "LAB", fill="#00FF88")

            # Call to Action box
            draw.rectangle([(140, cy + 320), (width - 140, cy + 460)], fill="#00FF88", outline="#FFFFFF", width=2)
            draw.text((cx - 140, cy + 370), "SUBSCRIBE FOR MORE", fill="#090D16")

            img.save(out_file, format="PNG")

        dur = time.time() - start_t
        return {
            "success": True,
            "file_path": str(out_file),
            "cost_usd": 0.0,
            "latency": dur,
            "provider": self.name,
            "model": "local_brand_engine",
        }


class DallEProvider:
    """Calls OpenAI Images API for photorealistic and cinematic generation."""
    name = "dall_e"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("mock_"))

    def generate(self, item: AssetItem, output_dir: Path) -> dict[str, Any]:
        start_t = time.time()
        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / f"{item.asset_id}.png"

        # DALL-E-3 only supports 1024x1792 (approx 9:16 vertical) or 1024x1024
        prompt = (item.prompt or item.subject)[:950]  # Respect limits
        body = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1792",
            "quality": "standard",
            "response_format": "url",
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.load(resp)
            img_url = data["data"][0]["url"]

            # Download image
            dl_req = urllib.request.Request(img_url, headers={"User-Agent": "AISimplifiedLab/2.0"})
            with urllib.request.urlopen(dl_req, timeout=60) as dl_resp:
                img_data = dl_resp.read()

            with open(out_file, "wb") as f:
                f.write(img_data)

            dur = time.time() - start_t
            return {
                "success": True,
                "file_path": str(out_file),
                "cost_usd": 0.040,  # Standard DALL-E-3 1024x1792 cost
                "latency": dur,
                "provider": self.name,
                "model": "dall-e-3",
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "cost_usd": 0.0,
                "latency": time.time() - start_t,
                "provider": self.name,
            }


class MockAssetProvider:
    """Deterministic mock provider for unit testing without network or GPU dependency."""
    name = "mock_provider"

    def __init__(self, should_fail: bool = False, simulated_cost: float = 0.01) -> None:
        self.should_fail = should_fail
        self.simulated_cost = simulated_cost

    def is_available(self) -> bool:
        return True

    def generate(self, item: AssetItem, output_dir: Path) -> dict[str, Any]:
        if self.should_fail:
            return {
                "success": False,
                "error": "Simulated generation failure",
                "cost_usd": 0.0,
                "latency": 0.05,
                "provider": self.name,
            }

        output_dir.mkdir(parents=True, exist_ok=True)
        ext = ".mp4" if item.type == "video" else ".png"
        out_file = output_dir / f"{item.asset_id}{ext}"

        if item.type == "video":
            # Write a deterministic valid mock video file header
            out_file.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42" + b"\x00" * 4096)
        else:
            # Create valid PNG image
            img = Image.new("RGB", (1080, 1920), color="#1E293B")
            draw = ImageDraw.Draw(img)
            draw.text((100, 200), f"MOCK ASSET: {item.asset_id}", fill="#38BDF8")
            draw.text((100, 260), f"SUBJECT: {item.subject}", fill="#FFFFFF")
            img.save(out_file, format="PNG")

        return {
            "success": True,
            "file_path": str(out_file),
            "cost_usd": self.simulated_cost,
            "latency": 0.05,
            "provider": self.name,
            "model": "mock_generator_v1",
        }
