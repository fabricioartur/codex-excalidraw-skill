#!/usr/bin/env python3
"""Validate a generated Excalidraw scene for common structural and readability issues."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_TOP_LEVEL = {"type", "version", "source", "elements", "appState", "files"}


def validate(path: Path) -> list[str]:
    scene = json.loads(path.read_text(encoding="utf-8"))
    issues: list[str] = []

    missing = REQUIRED_TOP_LEVEL - set(scene)
    if missing:
        issues.append(f"missing top-level keys: {', '.join(sorted(missing))}")
    if scene.get("type") != "excalidraw":
        issues.append("top-level `type` must be `excalidraw`")
    if not isinstance(scene.get("elements"), list):
        issues.append("top-level `elements` must be an array")
        return issues

    element_ids = set()
    for index, element in enumerate(scene["elements"]):
        label = element.get("id", f"index {index}")
        if not element.get("id"):
            issues.append(f"element {index} is missing id")
        elif element["id"] in element_ids:
            issues.append(f"duplicate element id: {element['id']}")
        element_ids.add(element.get("id"))

        if element.get("isDeleted"):
            continue
        if element.get("type") in {"line", "arrow"}:
            points = element.get("points") or []
            if len(points) < 2:
                issues.append(f"linear element {label} has fewer than 2 points")
            elif all(float(point[0] or 0) == 0 and float(point[1] or 0) == 0 for point in points):
                issues.append(f"linear element {label} has no visible length")
        elif element.get("type") != "text":
            width = float(element.get("width") or 0)
            height = float(element.get("height") or 0)
            if width <= 0 or height <= 0:
                issues.append(f"element {label} is invisibly small")
        else:
            text = str(element.get("text") or "")
            font_size = float(element.get("fontSize") or 0)
            width = float(element.get("width") or 0)
            line_count = max(1, text.count("\n") + 1)
            longest_line = max((len(line) for line in text.splitlines()), default=0)
            if font_size < 18:
                issues.append(f"text {label} uses small font size {font_size:g}")
            if line_count > 2 and width < 260:
                issues.append(f"text {label} has {line_count} lines in a narrow box")
            if longest_line > 24 and width < 300:
                issues.append(f"text {label} likely too long for width {width:g}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    args = parser.parse_args()

    issues = validate(args.scene)
    if issues:
        for issue in issues:
            print(f"error: {issue}", file=sys.stderr)
        return 1
    print("valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
