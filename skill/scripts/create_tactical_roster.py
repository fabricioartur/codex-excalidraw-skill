#!/usr/bin/env python3
"""Create a readable soccer tactical roster Excalidraw scene and SVG preview."""

from __future__ import annotations

import argparse
import html
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

from preview_page import write_preview_html


CANVAS_W = 2200
CANVAS_H = 1320


def eid(prefix: str) -> str:
    return f"{prefix}_{random.getrandbits(48):012x}"


def nonce() -> int:
    return random.randint(100000000, 2147483647)


def base_el(element_type: str, x: float, y: float, w: float, h: float) -> dict:
    return {
        "id": eid(element_type),
        "type": element_type,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
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


def rect(x: float, y: float, w: float, h: float, stroke: str, fill: str, sw: int = 2) -> dict:
    element = base_el("rectangle", x, y, w, h)
    element.update({"strokeColor": stroke, "backgroundColor": fill, "strokeWidth": sw})
    return element


def ellipse(x: float, y: float, w: float, h: float, stroke: str, fill: str, sw: int = 3) -> dict:
    element = base_el("ellipse", x, y, w, h)
    element.update({"strokeColor": stroke, "backgroundColor": fill, "strokeWidth": sw})
    return element


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, sw: int = 2) -> dict:
    element = base_el("line", x1, y1, x2 - x1, y2 - y1)
    element.update(
        {
            "strokeColor": stroke,
            "strokeWidth": sw,
            "points": [[0, 0], [x2 - x1, y2 - y1]],
            "lastCommittedPoint": None,
            "startBinding": None,
            "endBinding": None,
            "startArrowhead": None,
            "endArrowhead": None,
        }
    )
    return element


def text(label: str, x: float, y: float, w: float, fs: int = 24, color: str = "#111827", align: str = "center") -> dict:
    element = base_el("text", x, y, w, fs * 1.3)
    element.update(
        {
            "strokeColor": color,
            "backgroundColor": "transparent",
            "fontSize": fs,
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


POSITION_STYLE = {
    "gk": ("#f59e0b", "#92400e", "#451a03"),
    "def": ("#bfdbfe", "#2563eb", "#1e3a8a"),
    "mid": ("#ddd6fe", "#7c3aed", "#4c1d95"),
    "fwd": ("#bbf7d0", "#16a34a", "#14532d"),
    "star": ("#fecaca", "#dc2626", "#991b1b"),
}


DEFAULT_POSITIONS = {
    "gk": [(730, 250)],
    "def": [(230, 420), (540, 420), (850, 420), (1160, 420)],
    "mid": [(420, 590), (730, 590), (1040, 590)],
    "fwd": [(330, 750), (730, 735), (1130, 750)],
}


def marker_label(player: dict) -> str:
    return str(player.get("short") or player.get("name") or "").strip()


def validate_roster(spec: dict) -> None:
    starters = spec.get("starters", [])
    reserves = spec.get("reserves", [])
    if len(starters) != 11:
        raise ValueError("tactical roster requires exactly 11 starters")
    if not reserves:
        raise ValueError("tactical roster requires reserves grouped by position")
    for player in starters:
        label = marker_label(player)
        if not label:
            raise ValueError("starter missing `short` or `name`")
        if len(label) > 14:
            raise ValueError(f"starter label too long for marker: {label!r}")


def build_scene(spec: dict) -> dict:
    random.seed(int(spec.get("seed", 26)))
    validate_roster(spec)
    elems: list[dict] = []
    title = spec.get("title", "Tactical Roster")
    subtitle = spec.get("subtitle", "")
    footer = spec.get("footer", "")
    caveat = spec.get("caveat", "Formation is illustrative, not official.")

    elems.append(text(title, 360, 38, 1080, 38, "#0f9f3f"))
    if subtitle:
        elems.append(text(subtitle, 430, 86, 900, 24, "#6b7280"))

    elems.append(rect(70, 150, 1320, 840, "#16a34a", "#166534", 6))
    elems.append(line(70, 570, 1390, 570, "#bbf7d0", 3))
    elems.append(rect(495, 150, 470, 120, "#bbf7d0", "transparent", 2))
    elems.append(rect(495, 870, 470, 120, "#bbf7d0", "transparent", 2))
    elems.append(ellipse(610, 492, 240, 156, "#bbf7d0", "transparent", 2))
    elems.append(text(spec.get("formation", "Formation"), 560, 805, 340, 28, "#dcfce7"))
    elems.append(text(caveat, 330, 1030, 780, 22, "#065f46"))

    counters = {"gk": 0, "def": 0, "mid": 0, "fwd": 0}
    for player in spec["starters"]:
        role = player.get("role", "mid")
        coords = player.get("xy")
        if coords:
            x, y = coords
        else:
            x, y = DEFAULT_POSITIONS[role][counters[role]]
            counters[role] += 1
        style = POSITION_STYLE["star" if player.get("featured") else role]
        fill, stroke, color = style
        label = marker_label(player)
        elems.append(ellipse(x - 72, y - 46, 144, 92, stroke, fill, 4))
        elems.append(text(label, x - 64, y - 16, 128, 26, color))

    elems.append(rect(1440, 150, 690, 840, "#60a5fa", "#1f2333", 4))
    elems.append(text("Full roster by position", 1500, 180, 570, 30, "#ffffff"))
    y = 235
    for section in spec["reserves"]:
        name = section["title"]
        color = section.get("color", "#60a5fa")
        players = section["players"]
        elems.append(text(name, 1470, y, 260, 26, color, "left"))
        y += 40
        cols = 2 if len(players) > 5 else 1
        card_w = 300 if cols == 2 else 610
        for index, player in enumerate(players):
            col = index % cols
            row = index // cols
            x = 1470 + col * (card_w + 18)
            cy = y + row * 54
            label = player if isinstance(player, str) else player["name"]
            if len(label) > 26:
                label = label[:23] + "..."
            elems.append(rect(x, cy, card_w, 42, color, "transparent", 2))
            elems.append(text(label, x + 12, cy + 8, card_w - 24, 22, color))
        y += ((len(players) + cols - 1) // cols) * 54 + 24

    elems.append(rect(70, 1055, 2060, 118, "#2563eb", "#1e3a5f", 3))
    elems.append(text("Quick read", 100, 1074, 230, 25, "#dbeafe", "left"))
    elems.append(text(footer, 100, 1114, 1600, 23, "#dbeafe", "left"))
    elems.append(text(spec.get("source_note", ""), 100, 1147, 1700, 19, "#bfdbfe", "left"))
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elems,
        "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
        "files": {},
    }


def svg_preview(spec: dict) -> str:
    starters = spec["starters"]
    sections = spec["reserves"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="1100" y="70" text-anchor="middle" font-family="Inter, Arial" font-size="44" font-weight="800" fill="#0f9f3f">{html.escape(spec.get("title", "Tactical Roster"))}</text>',
        f'<text x="1100" y="112" text-anchor="middle" font-family="Inter, Arial" font-size="25" font-weight="700" fill="#6b7280">{html.escape(spec.get("subtitle", ""))}</text>',
        '<rect x="70" y="150" width="1320" height="840" rx="34" fill="#166534" stroke="#16a34a" stroke-width="6"/>',
        '<line x1="70" y1="570" x2="1390" y2="570" stroke="#bbf7d0" stroke-width="3" opacity="0.8"/>',
        '<rect x="495" y="150" width="470" height="120" rx="16" fill="none" stroke="#bbf7d0" stroke-width="2" opacity="0.75"/>',
        '<rect x="495" y="870" width="470" height="120" rx="16" fill="none" stroke="#bbf7d0" stroke-width="2" opacity="0.75"/>',
    ]
    counters = {"gk": 0, "def": 0, "mid": 0, "fwd": 0}
    for player in starters:
        role = player.get("role", "mid")
        if player.get("xy"):
            x, y = player["xy"]
        else:
            x, y = DEFAULT_POSITIONS[role][counters[role]]
            counters[role] += 1
        fill, stroke, color = POSITION_STYLE["star" if player.get("featured") else role]
        label = marker_label(player)
        parts.append(f'<ellipse cx="{x}" cy="{y}" rx="72" ry="46" fill="{fill}" stroke="{stroke}" stroke-width="5"/>')
        parts.append(f'<text x="{x}" y="{y + 8}" text-anchor="middle" font-family="Inter, Arial" font-size="25" font-weight="800" fill="{color}">{html.escape(label)}</text>')
    parts.extend(
        [
            f'<text x="730" y="835" text-anchor="middle" font-family="Inter, Arial" font-size="30" font-weight="800" fill="#dcfce7">{html.escape(spec.get("formation", "Formation"))}</text>',
            f'<text x="730" y="1058" text-anchor="middle" font-family="Inter, Arial" font-size="23" font-weight="700" fill="#065f46">{html.escape(spec.get("caveat", ""))}</text>',
            '<rect x="1440" y="150" width="690" height="840" rx="28" fill="#1f2333" stroke="#60a5fa" stroke-width="4"/>',
            '<text x="1785" y="205" text-anchor="middle" font-family="Inter, Arial" font-size="32" font-weight="800" fill="#ffffff">Full roster by position</text>',
        ]
    )
    y = 250
    for section in sections:
        color = section.get("color", "#60a5fa")
        players = section["players"]
        parts.append(f'<text x="1470" y="{y}" font-family="Inter, Arial" font-size="27" font-weight="800" fill="{color}">{html.escape(section["title"])}</text>')
        y += 16
        cols = 2 if len(players) > 5 else 1
        card_w = 300 if cols == 2 else 610
        for index, player in enumerate(players):
            label = player if isinstance(player, str) else player["name"]
            if len(label) > 26:
                label = label[:23] + "..."
            col = index % cols
            row = index // cols
            x = 1470 + col * (card_w + 18)
            cy = y + row * 54
            parts.append(f'<rect x="{x}" y="{cy}" width="{card_w}" height="42" rx="8" fill="none" stroke="{color}" stroke-width="2.4"/>')
            parts.append(f'<text x="{x + card_w / 2}" y="{cy + 28}" text-anchor="middle" font-family="Inter, Arial" font-size="22" font-weight="750" fill="{color}">{html.escape(label)}</text>')
        y += ((len(players) + cols - 1) // cols) * 54 + 24
    parts.extend(
        [
            '<rect x="70" y="1055" width="2060" height="118" rx="12" fill="#1e3a5f" stroke="#2563eb" stroke-width="3"/>',
            '<text x="100" y="1100" font-family="Inter, Arial" font-size="26" font-weight="850" fill="#dbeafe">Quick read</text>',
            f'<text x="100" y="1134" font-family="Inter, Arial" font-size="23" font-weight="650" fill="#dbeafe">{html.escape(spec.get("footer", ""))}</text>',
            f'<text x="100" y="1166" font-family="Inter, Arial" font-size="19" fill="#bfdbfe">{html.escape(spec.get("source_note", ""))}</text>',
            "</svg>",
        ]
    )
    return "\n".join(parts)


def read_spec(path: str) -> dict:
    if path == "-":
        import sys

        return json.loads(sys.stdin.read())
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", help="Spec JSON path, or '-' for stdin.")
    parser.add_argument("--name", default="tactical-roster")
    parser.add_argument("--tmp-dir", default="/private/tmp")
    parser.add_argument("--web-link", action="store_true")
    args = parser.parse_args()

    spec = read_spec(args.spec)
    tmp_root = Path(args.tmp_dir)
    tmp_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="excalidraw-roster-", dir=tmp_root))
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in args.name).strip("-") or "tactical-roster"
    scene_path = run_dir / f"{safe_name}.excalidraw"
    svg_path = run_dir / f"{safe_name}-preview.svg"
    html_path = run_dir / f"{safe_name}-preview.html"

    scene = build_scene(spec)
    svg = svg_preview(spec)
    scene_path.write_text(json.dumps(scene, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    svg_path.write_text(svg + "\n", encoding="utf-8")
    validate_script = Path(__file__).with_name("validate_scene.py")
    subprocess.run(["python3", str(validate_script), str(scene_path)], check=True)

    url = None
    if args.web_link:
        share_script = Path(__file__).with_name("share_excalidraw.mjs")
        upload = subprocess.run(["node", str(share_script), str(scene_path)], check=True, capture_output=True, text=True)
        url = upload.stdout.strip()
    write_preview_html(html_path, spec.get("title", "Tactical Roster"), svg, scene_path.name, scene, url)

    result = {
        "url": url,
        "preview_svg": str(svg_path),
        "preview_html": str(html_path),
        "excalidraw": str(scene_path),
        "element_count": len(scene["elements"]),
        "temporary_dir": str(run_dir),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
