#!/usr/bin/env python3
"""Create a readable building elevation diagram with facts and callouts."""

from __future__ import annotations

import argparse
import html
import json
import random
from pathlib import Path

from preview_page import write_preview_html
from scene_primitives import diamond, line, make_run_dir, read_spec, rect, safe_name, scene, share_scene, text, validate_scene, write_scene


def default_levels() -> list[dict]:
    return [
        {"x": 350, "y": 785, "w": 440, "h": 50, "stroke": "#9ca3af", "fill": "#e5e7eb"},
        {"x": 375, "y": 735, "w": 390, "h": 50, "stroke": "#9ca3af", "fill": "#e5e7eb"},
        {"x": 400, "y": 690, "w": 340, "h": 45, "stroke": "#9ca3af", "fill": "#e5e7eb"},
        {"x": 430, "y": 625, "w": 280, "h": 65, "stroke": "#6b7280", "fill": "#d1d5db"},
        {"x": 455, "y": 560, "w": 230, "h": 65, "stroke": "#6b7280", "fill": "#d1d5db"},
        {"x": 480, "y": 455, "w": 180, "h": 105, "stroke": "#4b5563", "fill": "#cbd5e1"},
        {"x": 505, "y": 350, "w": 130, "h": 105, "stroke": "#4b5563", "fill": "#cbd5e1"},
        {"x": 525, "y": 270, "w": 90, "h": 80, "stroke": "#374151", "fill": "#cbd5e1"},
        {"x": 540, "y": 220, "w": 60, "h": 50, "stroke": "#374151", "fill": "#dbeafe"},
    ]


def add_windows(elements: list[dict], levels: list[dict]) -> None:
    for level in levels[:-1]:
        x, y, w, h = level["x"], level["y"], level["w"], level["h"]
        cols = max(2, int(w // 42))
        rows = max(1, int(h // 28))
        start = x + 18
        for row in range(rows):
            for col in range(cols):
                wx = start + col * ((w - 36) / cols) + 3
                wy = y + 12 + row * ((h - 18) / rows)
                if wx + 12 < x + w - 8 and wy + 15 < y + h - 5:
                    elements.append(rect(wx, wy, 12, 15, "#94a3b8", "#eff6ff", 1))


def build_scene(spec: dict) -> dict:
    random.seed(int(spec.get("seed", 1931)))
    elements: list[dict] = []
    levels = spec.get("levels") or default_levels()
    facts = spec.get("facts") or []
    callouts = spec.get("callouts") or []

    elements.append(text(spec.get("title", "Building elevation"), 250, 35, 920, 36, "#1f2937"))
    elements.append(text(spec.get("subtitle", "Conceptual elevation diagram"), 385, 82, 650, 23, "#64748b"))
    elements.append(rect(55, 130, 1050, 805, "#cbd5e1", "#f8fafc", 2))
    elements.append(rect(55, 855, 1050, 80, "#334155", "#1e293b", 3))
    elements.append(text(spec.get("ground_label", "Urban base"), 395, 878, 420, 23, "#e2e8f0"))

    for level in levels:
        elements.append(rect(level["x"], level["y"], level["w"], level["h"], level.get("stroke", "#6b7280"), level.get("fill", "#d1d5db"), 3))
    add_windows(elements, levels)

    spire = spec.get("spire", {"x": 570, "top": 70, "base": 220})
    elements.append(rect(spire["x"] - 18, spire["base"] - 50, 36, 50, "#1d4ed8", "#bfdbfe", 3))
    elements.append(diamond(spire["x"] - 22, spire["base"] - 80, 44, 38, "#1d4ed8", "#bfdbfe", 3))
    elements.append(line(spire["x"], spire["base"] - 80, spire["x"], spire["top"], "#1d4ed8", 4))

    for band in spec.get("bands", []):
        elements.append(rect(band["x"], band["y"], band["w"], band.get("h", 22), band.get("stroke", "#ca8a04"), band.get("fill", "#fef3c7"), 3))
        elements.append(text(band["label"], band.get("label_x", band["x"] + band["w"] + 20), band["y"] - 10, band.get("label_w", 240), 21, band.get("stroke", "#92400e"), "left"))

    elements.append(line(250, 835, 250, spire["top"], "#475569", 3))
    for label in spec.get("height_labels", []):
        elements.append(text(label["text"], label["x"], label["y"], label.get("w", 160), 22, "#334155"))

    for callout in callouts:
        elements.append(text(callout["label"], callout["x"], callout["y"], callout.get("w", 230), 23, callout.get("color", "#334155"), "left"))
        if "from" in callout and "to" in callout:
            elements.append(line(callout["from"][0], callout["from"][1], callout["to"][0], callout["to"][1], callout.get("color", "#334155"), 2, True))

    px, py = 1160, 170
    elements.append(rect(px, py, 360, 575, "#334155", "#f8fafc", 3))
    elements.append(text("Quick facts", px + 24, py + 28, 310, 30, "#1f2937"))
    colors = ["#dbeafe", "#dcfce7", "#fef3c7", "#ede9fe", "#cffafe", "#fee2e2"]
    y = py + 95
    for index, fact in enumerate(facts[:6]):
        elements.append(rect(px + 28, y, 304, 58, "#64748b", colors[index % len(colors)], 2))
        elements.append(text(fact["label"], px + 45, y + 9, 95, 18, "#334155", "left"))
        elements.append(text(fact["value"], px + 145, y + 9, 165, 20, "#111827", "left"))
        y += 72

    elements.append(rect(110, 955, 1380, 58, "#2563eb", "#eff6ff", 3))
    elements.append(text(spec.get("note", "Illustrative and editable diagram; proportions are simplified."), 135, 972, 1325, 22, "#1e3a8a", "left"))
    return scene(elements)


def svg_preview(spec: dict) -> str:
    data = build_scene(spec)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1050" viewBox="0 0 1600 1050">']
    parts.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    for element in data["elements"]:
        kind = element["type"]
        x, y, w, h = element["x"], element["y"], element["width"], element["height"]
        stroke = element.get("strokeColor", "#111827")
        fill = element.get("backgroundColor", "transparent")
        sw = element.get("strokeWidth", 2)
        if kind == "rectangle":
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        elif kind == "diamond":
            parts.append(f'<polygon points="{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        elif kind in {"line", "arrow"}:
            x2 = x + element["points"][1][0]
            y2 = y + element["points"][1][1]
            parts.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"/>')
        elif kind == "text":
            safe = html.escape(element.get("text", ""))
            anchor = "middle" if element.get("textAlign") == "center" else "start"
            tx = x + (w / 2 if anchor == "middle" else 0)
            parts.append(f'<text x="{tx}" y="{y + element.get("fontSize", 20)}" text-anchor="{anchor}" font-family="Inter, Arial" font-size="{element.get("fontSize", 20)}" font-weight="750" fill="{stroke}">{safe}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", help="Spec JSON path, or '-' for stdin.")
    parser.add_argument("--name", default="building-elevation")
    parser.add_argument("--tmp-dir", default="/private/tmp")
    parser.add_argument("--web-link", action="store_true")
    args = parser.parse_args()

    spec = read_spec(args.spec)
    run_dir = make_run_dir(args.tmp_dir, "excalidraw-building-")
    name = safe_name(args.name, "building-elevation")
    scene_path = run_dir / f"{name}.excalidraw"
    svg_path = run_dir / f"{name}-preview.svg"
    html_path = run_dir / f"{name}-preview.html"

    data = build_scene(spec)
    write_scene(scene_path, data)
    svg = svg_preview(spec)
    svg_path.write_text(svg + "\n", encoding="utf-8")
    validate_scene(scene_path)

    url = None
    if args.web_link:
        url = share_scene(scene_path)
    write_preview_html(html_path, spec.get("title", "Building elevation"), svg, scene_path.name, data, url)

    result = {
        "url": url,
        "preview_svg": str(svg_path),
        "preview_html": str(html_path),
        "excalidraw": str(scene_path),
        "element_count": len(data["elements"]),
        "temporary_dir": str(run_dir),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
