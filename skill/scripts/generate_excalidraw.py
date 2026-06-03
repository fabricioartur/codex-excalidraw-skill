#!/usr/bin/env python3
"""Generate a simple editable Excalidraw node-and-edge diagram from JSON."""

from __future__ import annotations

import argparse
import html
import json
import random
import subprocess
import sys
import textwrap
import uuid
from pathlib import Path

from preview_page import render_preview_html


WIDTH = 220
HEIGHT = 88
GAP_X = 120
GAP_Y = 90
MARGIN_X = 80
MARGIN_Y = 130


def eid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def nonce() -> int:
    return random.randint(100000000, 2147483647)


def wrap_label(label: str, width: int = 20) -> str:
    return "\n".join(textwrap.wrap(str(label), width=width, break_long_words=False)) or str(label)


def base_element(element_type: str, x: float, y: float, width: float, height: float) -> dict:
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


def text_element(text: str, x: float, y: float, width: float, font_size: int = 20, align: str = "center") -> dict:
    wrapped = wrap_label(text)
    line_count = max(1, wrapped.count("\n") + 1)
    height = line_count * font_size * 1.25
    element = base_element("text", x, y, width, height)
    element.update(
        {
            "strokeColor": "#1e1e1e",
            "backgroundColor": "transparent",
            "fontSize": font_size,
            "fontFamily": 1,
            "text": wrapped,
            "textAlign": align,
            "verticalAlign": "middle",
            "containerId": None,
            "originalText": str(text),
            "autoResize": False,
            "lineHeight": 1.25,
        }
    )
    return element


def rectangle(label: str, x: float, y: float, accent: bool = False) -> list[dict]:
    rect = base_element("rectangle", x, y, WIDTH, HEIGHT)
    rect["backgroundColor"] = "#e7f5ff" if accent else "#f8f9fa"
    rect["strokeColor"] = "#1971c2" if accent else "#1e1e1e"
    label_text = text_element(label, x + 16, y + 24, WIDTH - 32)
    return [rect, label_text]


def arrow(start: tuple[float, float], end: tuple[float, float], label: str | None = None) -> list[dict]:
    sx, sy = start
    ex, ey = end
    arr = base_element("arrow", sx, sy, ex - sx, ey - sy)
    arr.update(
        {
            "backgroundColor": "transparent",
            "points": [[0, 0], [ex - sx, ey - sy]],
            "lastCommittedPoint": None,
            "startBinding": None,
            "endBinding": None,
            "startArrowhead": None,
            "endArrowhead": "arrow",
        }
    )
    elements = [arr]
    if label:
        mx = (sx + ex) / 2 - 70
        my = (sy + ey) / 2 - 30
        label_el = text_element(label, mx, my, 170, font_size=18)
        label_el["strokeColor"] = "#495057"
        elements.append(label_el)
    return elements


def node_positions(nodes: list[dict], direction: str) -> dict[str, tuple[float, float]]:
    positions = {}
    for index, node in enumerate(nodes):
        if direction == "TB":
            x = MARGIN_X
            y = MARGIN_Y + index * (HEIGHT + GAP_Y)
        else:
            x = MARGIN_X + index * (WIDTH + GAP_X)
            y = MARGIN_Y
        positions[str(node["id"])] = (x, y)
    return positions


def group_frame(label: str, node_ids: list[str], positions: dict[str, tuple[float, float]]) -> list[dict]:
    points = [positions[n] for n in node_ids if n in positions]
    if not points:
        return []
    min_x = min(x for x, _ in points) - 32
    min_y = min(y for _, y in points) - 48
    max_x = max(x for x, _ in points) + WIDTH + 32
    max_y = max(y for _, y in points) + HEIGHT + 32
    frame = base_element("rectangle", min_x, min_y, max_x - min_x, max_y - min_y)
    frame.update({"strokeColor": "#adb5bd", "backgroundColor": "transparent", "strokeStyle": "dashed", "strokeWidth": 1})
    title = text_element(label, min_x + 12, min_y + 10, max_x - min_x - 24, font_size=16, align="left")
    title["strokeColor"] = "#495057"
    return [frame, title]


def build_scene(spec: dict) -> dict:
    nodes = spec.get("nodes") or []
    if not nodes:
        raise ValueError("Spec must include at least one node in `nodes`.")
    direction = str(spec.get("direction", "LR")).upper()
    if direction not in {"LR", "TB"}:
        raise ValueError("`direction` must be `LR` or `TB`.")

    positions = node_positions(nodes, direction)
    elements: list[dict] = []

    title = spec.get("title")
    if title:
        elements.append(text_element(str(title), MARGIN_X, 48, 520, font_size=28, align="left"))

    for group in spec.get("groups", []):
        elements.extend(group_frame(str(group.get("label", "Group")), [str(n) for n in group.get("nodes", [])], positions))

    for index, node in enumerate(nodes):
        node_id = str(node["id"])
        elements.extend(rectangle(str(node.get("label", node_id)), *positions[node_id], accent=index == 0))

    for edge in spec.get("edges", []):
        from_id = str(edge.get("from"))
        to_id = str(edge.get("to"))
        if from_id not in positions or to_id not in positions:
            raise ValueError(f"Edge references missing node: {from_id} -> {to_id}")
        fx, fy = positions[from_id]
        tx, ty = positions[to_id]
        if direction == "TB":
            start = (fx + WIDTH / 2, fy + HEIGHT)
            end = (tx + WIDTH / 2, ty)
        else:
            start = (fx + WIDTH, fy + HEIGHT / 2)
            end = (tx, ty + HEIGHT / 2)
        elements.extend(arrow(start, end, edge.get("label")))

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"},
        "files": {},
    }


def render_preview_svg(spec: dict) -> str:
    nodes = spec.get("nodes") or []
    edges = spec.get("edges") or []
    groups = spec.get("groups") or []
    direction = str(spec.get("direction", "LR")).upper()
    positions = node_positions(nodes, direction)

    if direction == "TB":
        canvas_w = 620
        canvas_h = MARGIN_Y * 2 + len(nodes) * HEIGHT + max(0, len(nodes) - 1) * GAP_Y
    else:
        canvas_w = MARGIN_X * 2 + len(nodes) * WIDTH + max(0, len(nodes) - 1) * GAP_X
        canvas_h = 380

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#1e1e1e"/></marker><filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.14"/></filter></defs>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]

    title = spec.get("title")
    if title:
        parts.append(
            f'<text x="{MARGIN_X}" y="64" font-family="Inter, Arial, sans-serif" font-size="30" font-weight="700" fill="#1e1e1e">{html.escape(str(title))}</text>'
        )

    for group in groups:
        group_nodes = [str(n) for n in group.get("nodes", []) if str(n) in positions]
        if not group_nodes:
            continue
        points = [positions[node_id] for node_id in group_nodes]
        min_x = min(x for x, _ in points) - 32
        min_y = min(y for _, y in points) - 54
        max_x = max(x for x, _ in points) + WIDTH + 32
        max_y = max(y for _, y in points) + HEIGHT + 40
        parts.append(
            f'<rect x="{min_x}" y="{min_y}" width="{max_x - min_x}" height="{max_y - min_y}" rx="10" fill="none" stroke="#adb5bd" stroke-width="1.5" stroke-dasharray="7 7"/>'
        )
        parts.append(
            f'<text x="{min_x + 14}" y="{min_y + 28}" font-family="Inter, Arial, sans-serif" font-size="16" fill="#495057">{html.escape(str(group.get("label", "Group")))}</text>'
        )

    for edge in edges:
        from_id = str(edge.get("from"))
        to_id = str(edge.get("to"))
        if from_id not in positions or to_id not in positions:
            continue
        fx, fy = positions[from_id]
        tx, ty = positions[to_id]
        if direction == "TB":
            sx, sy = fx + WIDTH / 2, fy + HEIGHT
            ex, ey = tx + WIDTH / 2, ty
        else:
            sx, sy = fx + WIDTH, fy + HEIGHT / 2
            ex, ey = tx, ty + HEIGHT / 2
        parts.append(f'<line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" stroke="#1e1e1e" stroke-width="2.2" marker-end="url(#arrow)"/>')
        if edge.get("label"):
            mx, my = (sx + ex) / 2, (sy + ey) / 2 - 16
            parts.append(f'<rect x="{mx - 62}" y="{my - 20}" width="124" height="28" rx="5" fill="#ffffff" stroke="#dee2e6"/>')
            parts.append(
                f'<text x="{mx}" y="{my}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="13" fill="#495057">{html.escape(str(edge["label"]))}</text>'
            )

    for index, node in enumerate(nodes):
        node_id = str(node["id"])
        x, y = positions[node_id]
        fill = "#e7f5ff" if index == 0 else "#f8f9fa"
        stroke = "#1971c2" if index == 0 else "#1e1e1e"
        parts.append(
            f'<rect x="{x}" y="{y}" width="{WIDTH}" height="{HEIGHT}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2.5" filter="url(#shadow)"/>'
        )
        for line_index, line in enumerate(wrap_label(str(node.get("label", node_id)), 18).split("\n")):
            line_y = y + HEIGHT / 2 + 7 + (line_index - 0.5) * 22 if "\n" in wrap_label(str(node.get("label", node_id)), 18) else y + HEIGHT / 2 + 7
            parts.append(
                f'<text x="{x + WIDTH / 2}" y="{line_y}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="20" font-weight="600" fill="#1e1e1e">{html.escape(line)}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def create_excalidraw_web_url(scene_path: Path) -> str:
    script = Path(__file__).with_name("share_excalidraw.mjs")
    result = subprocess.run(
        ["node", str(script), str(scene_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Input JSON spec.")
    parser.add_argument("output", type=Path, help="Output .excalidraw file.")
    parser.add_argument("--preview", action="store_true", help="Also generate <output-stem>-preview.svg and <output-stem>-preview.html.")
    parser.add_argument("--preview-svg", type=Path, help="Optional path for preview SVG.")
    parser.add_argument("--preview-html", type=Path, help="Optional path for preview HTML.")
    parser.add_argument("--web-link", action="store_true", help="Upload encrypted scene to Excalidraw storage and use a preloaded excalidraw.com URL in the preview HTML.")
    parser.add_argument("--web-url-file", type=Path, help="Optional path to write the generated Excalidraw web URL.")
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    scene = build_scene(spec)
    args.output.write_text(json.dumps(scene, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    json.loads(args.output.read_text(encoding="utf-8"))

    web_url = None
    if args.web_link:
        web_url = create_excalidraw_web_url(args.output)
        if args.web_url_file:
            args.web_url_file.write_text(web_url + "\n", encoding="utf-8")

    if args.preview or args.preview_svg or args.preview_html or args.web_link:
        svg = render_preview_svg(spec)
        svg_path = args.preview_svg or args.output.with_name(f"{args.output.stem}-preview.svg")
        html_path = args.preview_html or args.output.with_name(f"{args.output.stem}-preview.html")
        svg_path.write_text(svg + "\n", encoding="utf-8")
        html_path.write_text(render_preview_html(str(spec.get("title", args.output.stem)), svg, args.output.name, scene, web_url), encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
