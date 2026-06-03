#!/usr/bin/env python3
"""Persist and retrieve the latest Excalidraw diagram for incremental edits."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path


DEFAULT_STATE_DIR = Path(os.environ.get("CODEX_EXCALIDRAW_STATE_DIR", Path.home() / "Codex" / "excalidraw" / "state"))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_if_present(src: str | None, dst: Path) -> str | None:
    if not src:
        return None
    source = Path(src)
    if not source.exists():
        return None
    ensure_dir(dst.parent)
    shutil.copy2(source, dst)
    return str(dst)


def save(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir)
    current_dir = state_dir / "current"
    ensure_dir(current_dir)

    scene_path = copy_if_present(args.scene, current_dir / "last.excalidraw")
    preview_path = copy_if_present(args.preview, current_dir / "last-preview.svg")
    html_path = copy_if_present(args.html, current_dir / "last-preview.html")
    spec_path = copy_if_present(args.spec, current_dir / "last-spec.json")

    metadata = {
        "updated_at": int(time.time()),
        "request": args.request or "",
        "template": args.template or "",
        "url": args.url or "",
        "scene": scene_path,
        "preview_svg": preview_path,
        "preview_html": html_path,
        "spec": spec_path,
        "notes": args.notes or "",
    }
    (state_dir / "last.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


def show(args: argparse.Namespace) -> int:
    path = Path(args.state_dir) / "last.json"
    if not path.exists():
        print(json.dumps({"exists": False}, ensure_ascii=False, indent=2))
        return 1
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def clear(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir)
    if state_dir.exists():
        shutil.rmtree(state_dir)
    print(json.dumps({"cleared": True, "state_dir": str(state_dir)}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    sub = parser.add_subparsers(dest="command", required=True)

    save_parser = sub.add_parser("save", help="Persist latest diagram artifacts.")
    save_parser.add_argument("--scene", required=True)
    save_parser.add_argument("--preview")
    save_parser.add_argument("--html")
    save_parser.add_argument("--spec")
    save_parser.add_argument("--url")
    save_parser.add_argument("--request")
    save_parser.add_argument("--template")
    save_parser.add_argument("--notes")
    save_parser.set_defaults(func=save)

    show_parser = sub.add_parser("show", help="Show latest diagram metadata.")
    show_parser.set_defaults(func=show)

    clear_parser = sub.add_parser("clear", help="Clear latest diagram metadata and copied artifacts.")
    clear_parser.set_defaults(func=clear)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
