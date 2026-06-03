"""Small helpers for generating editable Excalidraw scenes quickly."""

from __future__ import annotations

import json
import random
import subprocess
import tempfile
from pathlib import Path


def eid(prefix: str) -> str:
    return f"{prefix}_{random.getrandbits(48):012x}"


def nonce() -> int:
    return random.randint(100000000, 2147483647)


def element_base(element_type: str, x: float, y: float, width: float, height: float) -> dict:
    return {
        "id": eid(element_type),
        "type": element_type,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 3},
        "seed": nonce(),
        "version": 1,
        "versionNonce": nonce(),
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
    }


def rect(x: float, y: float, width: float, height: float, stroke: str = "#1e1e1e", fill: str = "transparent", stroke_width: int = 2) -> dict:
    element = element_base("rectangle", x, y, width, height)
    element.update({"strokeColor": stroke, "backgroundColor": fill, "strokeWidth": stroke_width})
    return element


def ellipse(x: float, y: float, width: float, height: float, stroke: str = "#1e1e1e", fill: str = "transparent", stroke_width: int = 2) -> dict:
    element = element_base("ellipse", x, y, width, height)
    element.update({"strokeColor": stroke, "backgroundColor": fill, "strokeWidth": stroke_width})
    return element


def diamond(x: float, y: float, width: float, height: float, stroke: str = "#1e1e1e", fill: str = "transparent", stroke_width: int = 2) -> dict:
    element = element_base("diamond", x, y, width, height)
    element.update({"strokeColor": stroke, "backgroundColor": fill, "strokeWidth": stroke_width})
    return element


def line(x1: float, y1: float, x2: float, y2: float, stroke: str = "#1e1e1e", stroke_width: int = 2, arrow: bool = False) -> dict:
    element = element_base("arrow" if arrow else "line", x1, y1, x2 - x1, y2 - y1)
    element.update(
        {
            "strokeColor": stroke,
            "strokeWidth": stroke_width,
            "points": [[0, 0], [x2 - x1, y2 - y1]],
            "lastCommittedPoint": None,
            "startBinding": None,
            "endBinding": None,
            "startArrowhead": None,
            "endArrowhead": "arrow" if arrow else None,
        }
    )
    return element


def text(label: str, x: float, y: float, width: float, font_size: int = 24, color: str = "#111827", align: str = "center") -> dict:
    element = element_base("text", x, y, width, font_size * 1.35)
    element.update(
        {
            "strokeColor": color,
            "backgroundColor": "transparent",
            "fontSize": font_size,
            "fontFamily": 1,
            "text": label,
            "textAlign": align,
            "verticalAlign": "middle",
            "containerId": None,
            "originalText": label,
            "autoResize": False,
            "lineHeight": 1.25,
        }
    )
    return element


def scene(elements: list[dict], background: str = "#ffffff") -> dict:
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"gridSize": None, "viewBackgroundColor": background},
        "files": {},
    }


def read_spec(path: str) -> dict:
    if path == "-":
        import sys

        return json.loads(sys.stdin.read())
    return json.loads(Path(path).read_text(encoding="utf-8"))


def make_run_dir(tmp_dir: str = "/private/tmp", prefix: str = "excalidraw-") -> Path:
    root = Path(tmp_dir)
    root.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=root))


def safe_name(name: str, fallback: str = "diagram") -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in name).strip("-")
    return cleaned or fallback


def write_scene(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_scene(path: Path) -> None:
    script = Path(__file__).with_name("validate_scene.py")
    subprocess.run(["python3", str(script), str(path)], check=True)


def share_scene(path: Path) -> str:
    script = Path(__file__).with_name("share_excalidraw.mjs")
    result = subprocess.run(["node", str(script), str(path)], check=True, capture_output=True, text=True)
    return result.stdout.strip()
