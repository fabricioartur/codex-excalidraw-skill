"""Create local preview HTML with lazy Excalidraw Web upload."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def _script_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")


def render_preview_html(title: str, svg: str, excalidraw_name: str, scene_data: dict, web_url: str | None = None) -> str:
    safe_title = html.escape(title or "Excalidraw Diagram")
    safe_file = html.escape(excalidraw_name)
    safe_web_url = html.escape(web_url or "")
    scene_json = _script_json(scene_data)
    open_action = (
        f'<a href="{safe_web_url}" target="_blank" rel="noreferrer">Open in Excalidraw</a>'
        if web_url
        else '<button id="open-web" type="button">Open in Excalidraw</button>'
    )
    note = (
        "This opens the diagram already loaded in Excalidraw Web. The scene is encrypted before upload; the key stays in the URL fragment."
        if web_url
        else "Preview is local. Click Open in Excalidraw only when you want to upload an encrypted copy and edit it on the web."
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ margin: 0; background: #1f1f1f; color: #f8f9fa; }}
    .card {{ margin: 32px auto; max-width: min(1120px, calc(100vw - 32px)); border: 1px solid #3d3d3d; border-radius: 8px; overflow: hidden; background: #2a2a2a; box-shadow: 0 18px 60px rgba(0,0,0,.28); }}
    header {{ min-height: 54px; display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 10px 16px; border-bottom: 1px solid #3d3d3d; }}
    .brand {{ display: flex; gap: 10px; align-items: center; font-weight: 650; white-space: nowrap; }}
    .mark {{ width: 18px; height: 18px; border-radius: 5px; background: #6965db; display: inline-grid; place-items: center; color: white; font-size: 13px; }}
    .actions {{ display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }}
    a, button {{ border: 1px solid #d8d8d8; border-radius: 7px; background: #ffffff; color: #1e1e1e; padding: 8px 11px; text-decoration: none; font-size: 14px; cursor: pointer; }}
    button[disabled] {{ opacity: .68; cursor: wait; }}
    main {{ background: #ffffff; overflow: auto; }}
    .canvas {{ min-width: max-content; padding: 20px; }}
    .note {{ color: #adb5bd; font-size: 13px; padding: 0 16px 16px; line-height: 1.45; }}
  </style>
</head>
<body>
  <section class="card">
    <header>
      <div class="brand"><span class="mark">E</span><span>Excalidraw</span></div>
      <div class="actions">
        <a href="{safe_file}" download>Download .excalidraw</a>
        {open_action}
      </div>
    </header>
    <main><div class="canvas">{svg}</div></main>
    <div class="note" id="note">{html.escape(note)}</div>
  </section>
  <script>
    const SCENE = {scene_json};
    const POST_URL = "https://json.excalidraw.com/api/v2/post/";
    const EXCALIDRAW_URL = "https://excalidraw.com/";

    function base64url(buffer) {{
      const bytes = new Uint8Array(buffer);
      let binary = "";
      for (const byte of bytes) binary += String.fromCharCode(byte);
      return btoa(binary).replace(/\\+/g, "-").replace(/\\//g, "_").replace(/=+$/g, "");
    }}

    function concatBuffers(...buffers) {{
      const totalLength = 4 + buffers.length * 4 + buffers.reduce((sum, buffer) => sum + buffer.byteLength, 0);
      const output = new ArrayBuffer(totalLength);
      const view = new DataView(output);
      const bytes = new Uint8Array(output);
      let cursor = 0;
      view.setUint32(cursor, 1);
      cursor += 4;
      for (const buffer of buffers) {{
        view.setUint32(cursor, buffer.byteLength);
        cursor += 4;
        bytes.set(new Uint8Array(buffer), cursor);
        cursor += buffer.byteLength;
      }}
      return output;
    }}

    async function deflate(buffer) {{
      if (!("CompressionStream" in window)) {{
        throw new Error("Your browser does not support CompressionStream. Download the .excalidraw file and import it manually.");
      }}
      const stream = new Blob([buffer]).stream().pipeThrough(new CompressionStream("deflate"));
      return await new Response(stream).arrayBuffer();
    }}

    async function createUrl(scene) {{
      const key = crypto.getRandomValues(new Uint8Array(16));
      const iv = crypto.getRandomValues(new Uint8Array(12));
      const cryptoKey = await crypto.subtle.importKey("raw", key, "AES-GCM", false, ["encrypt"]);
      const databaseScene = {{
        type: scene.type || "excalidraw",
        version: scene.version || 2,
        source: scene.source || "https://excalidraw.com",
        elements: scene.elements || [],
        appState: scene.appState || {{}},
      }};
      const encoder = new TextEncoder();
      const data = encoder.encode(JSON.stringify(databaseScene, null, 2)).buffer;
      const encodingMetadata = encoder.encode(JSON.stringify({{ version: 2, compression: "pako@1", encryption: "AES-GCM" }})).buffer;
      const contentsMetadata = encoder.encode("null").buffer;
      const contents = concatBuffers(contentsMetadata, data);
      const compressed = await deflate(contents);
      const encrypted = await crypto.subtle.encrypt({{ name: "AES-GCM", iv, tagLength: 128 }}, cryptoKey, compressed);
      const payload = concatBuffers(encodingMetadata, iv.buffer, encrypted);
      const response = await fetch(POST_URL, {{ method: "POST", body: payload }});
      const result = await response.json();
      if (!response.ok || !result.id) throw new Error(`Excalidraw upload failed: ${{response.status}}`);
      return `${{EXCALIDRAW_URL}}#json=${{result.id}},${{base64url(key)}}`;
    }}

    const button = document.getElementById("open-web");
    if (button) {{
      button.addEventListener("click", async () => {{
        const note = document.getElementById("note");
        try {{
          button.disabled = true;
          button.textContent = "Generating link...";
          const url = await createUrl(SCENE);
          button.textContent = "Open in Excalidraw";
          button.disabled = false;
          note.textContent = "Web link generated in your browser. Opening Excalidraw now.";
          window.open(url, "_blank", "noreferrer");
        }} catch (error) {{
          button.disabled = false;
          button.textContent = "Open in Excalidraw";
          note.textContent = error.message || String(error);
        }}
      }});
    }}
  </script>
</body>
</html>
"""


def write_preview_html(path: Path, title: str, svg: str, excalidraw_name: str, scene_data: dict, web_url: str | None = None) -> None:
    path.write_text(render_preview_html(title, svg, excalidraw_name, scene_data, web_url), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True, help="Input .excalidraw JSON scene.")
    parser.add_argument("--svg", type=Path, required=True, help="Input SVG preview.")
    parser.add_argument("--output", type=Path, required=True, help="Output preview HTML.")
    parser.add_argument("--title", default="Excalidraw Diagram")
    parser.add_argument("--web-url", help="Optional already-generated Excalidraw Web URL.")
    args = parser.parse_args()

    scene_data = json.loads(args.scene.read_text(encoding="utf-8"))
    svg = args.svg.read_text(encoding="utf-8")
    write_preview_html(args.output, args.title, svg, args.scene.name, scene_data, args.web_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
