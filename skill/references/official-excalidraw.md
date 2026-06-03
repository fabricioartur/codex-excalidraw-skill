# Official Excalidraw Notes

Use these notes when a diagram needs to be more robust than hand-written JSON.

## Source Anchors

- Main repository: `https://github.com/excalidraw/excalidraw`
- Developer docs: `https://docs.excalidraw.com/docs/@excalidraw/excalidraw`
- Mermaid converter: `https://github.com/excalidraw/mermaid-to-excalidraw`
- Public JSON storage used by Excalidraw Web links: `https://github.com/excalidraw/excalidraw-store`

## Important Official Concepts

- Excalidraw is an open JSON format. A normal scene has `type`, `version`, `source`, `elements`, `appState`, and `files`.
- Excalidraw Web supports shareable links. The app is local-first and uses end-to-end encryption for shared/collaborative data.
- The npm package exposes programmatic utilities:
  - `serializeAsJSON` for saving scene data.
  - `loadFromBlob` and `loadSceneOrLibraryFromBlob` for importing scene/library data.
  - `restoreAppState`, `restoreElements`, and `restore` for filling missing defaults and repairing imported data.
  - `exportToSvg`, `exportToBlob`, and `exportToCanvas` for official rendering/export paths.
  - `convertToExcalidrawElements` for converting simplified `ExcalidrawElementSkeleton` objects into full elements.
- Export appState supports `exportBackground`, `viewBackgroundColor`, `exportWithDarkMode`, and `exportEmbedScene`.
- `@excalidraw/mermaid-to-excalidraw` can parse Mermaid definitions into Excalidraw `elements` and `files`; use it when the user gives Mermaid or asks for standard flowcharts, sequence diagrams, state diagrams, or ER-style diagrams.

## How This Should Improve the Skill

Prefer a higher-level representation before full manual JSON:

1. Use a purpose-built template when one exists, such as `create_tactical_roster.py`.
2. Use Mermaid conversion for standard Mermaid-like diagrams if a local Node dependency is available or can be installed.
3. Use skeleton-style internal helpers for new generic scripts instead of manually filling every Excalidraw field repeatedly.
4. Use `restore`/`restoreElements` semantics as a validation target: generated elements should include enough structure that Excalidraw can restore defaults safely.
5. Use official export utilities when a real Excalidraw-rendered PNG/SVG is needed; use local SVG previews only as a lightweight fallback.

## Practical Guardrails

- Do not claim local SVG previews are official Excalidraw exports unless they were generated through Excalidraw's export utilities.
- For web links, mention that `--web-link` uploads an encrypted compressed scene and keeps the decryption key in the URL fragment.
- When editing existing files, preserve unknown fields and prefer restore-style repair over rewriting every element.
- For Mermaid input, preserve the Mermaid source in the temp folder or result metadata so the user can regenerate.
