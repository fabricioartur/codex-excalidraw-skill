#!/usr/bin/env python3
"""Create a temporary Excalidraw web handoff from a spec JSON.

Reads a diagram spec from a file or stdin, writes all intermediate artifacts to
a temporary folder, uploads an encrypted scene to Excalidraw by default, and
prints a small JSON result containing the ready-to-open web URL and preview paths.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def read_spec(path: str) -> dict:
    if path == "-":
        import sys

        return json.loads(sys.stdin.read())
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", help="Spec JSON path, or '-' to read from stdin.")
    parser.add_argument("--name", default="diagram", help="Base filename for temporary artifacts.")
    parser.add_argument("--tmp-dir", default="/private/tmp", help="Directory for temporary artifact folders.")
    parser.add_argument("--web-link", action="store_true", default=True, help="Upload encrypted scene and return a preloaded Excalidraw Web URL. Enabled by default.")
    parser.add_argument("--no-web-link", action="store_false", dest="web_link", help="Skip web upload and create a local-only preview.")
    args = parser.parse_args()

    spec = read_spec(args.spec)
    tmp_root = Path(args.tmp_dir)
    tmp_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="excalidraw-", dir=tmp_root))

    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in args.name).strip("-") or "diagram"
    spec_path = run_dir / f"{safe_name}-spec.json"
    excalidraw_path = run_dir / f"{safe_name}.excalidraw"
    url_path = run_dir / f"{safe_name}.url"

    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    generator = Path(__file__).with_name("generate_excalidraw.py")
    subprocess.run(
        [
            "python3",
            str(generator),
            str(spec_path),
            str(excalidraw_path),
            "--preview",
        ]
        + (["--web-link", "--web-url-file", str(url_path)] if args.web_link else []),
        check=True,
    )

    scene = json.loads(excalidraw_path.read_text(encoding="utf-8"))
    required = {"type", "version", "source", "elements", "appState", "files"}
    missing = required - set(scene)
    if missing:
        raise ValueError(f"Generated scene missing keys: {sorted(missing)}")

    result = {
        "url": url_path.read_text(encoding="utf-8").strip() if url_path.exists() else None,
        "preview_svg": str(excalidraw_path.with_name(f"{excalidraw_path.stem}-preview.svg")),
        "preview_html": str(excalidraw_path.with_name(f"{excalidraw_path.stem}-preview.html")),
        "excalidraw": str(excalidraw_path),
        "spec": str(spec_path),
        "element_count": len(scene["elements"]),
        "temporary_dir": str(run_dir),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
