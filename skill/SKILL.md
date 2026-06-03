---
name: excalidraw
description: Create, inspect, and edit Excalidraw diagrams as editable `.excalidraw` JSON files. Use when Codex needs to turn architecture sketches, process flows, user journeys, system diagrams, workshop notes, whiteboard-style visuals, or Mermaid-like node-and-edge specs into an Excalidraw file; modify existing Excalidraw scenes; or prepare diagram files that the user can open and continue editing in Excalidraw.
---

# Excalidraw

## Overview

Create diagrams as real `.excalidraw` JSON, not screenshots, so the user can keep editing them in Excalidraw. Prefer simple editable shapes, text, arrows, frames, and grouped sections over pixel-perfect artwork.

Important boundary: this skill can create editable files and preview pages, but a skill alone cannot create a native inline Excalidraw widget with live editing, checkpoint restoration, or host-provided buttons inside the chat UI. That experience requires an MCP/app/widget integration that exposes operations like `read_me`, `create_view`, checkpoint storage, and widget rendering.

## Core Workflow

1. Clarify the diagram intent only when the request lacks the actors, nodes, or flow.
2. Decide whether this is a new diagram or an edit to the previous diagram:
   - If the user asks to adjust, change, add, remove, make bigger/smaller, recolor, relabel, simplify, improve, or otherwise revise "this", "that", "the diagram", or "the last one", use the incremental edit workflow below.
   - If the user asks for a new subject, create a new diagram.
3. Default to web-link handoff for new diagrams:
   - Use `scripts/create_web_diagram.py` and pass the spec through stdin.
   - Let the script create its own temporary folder under `/private/tmp`.
   - Request network permission during generation so Codex can upload the encrypted scene and return a ready `https://excalidraw.com/#json=...` link.
   - Return the preview image, the local preview page path, and the ready Excalidraw Web URL.
   - The local preview page must include an **Open in Excalidraw** button that points directly to the ready web URL.
   - Use `--no-web-link` only when the user explicitly asks for local-only/offline output or refuses network access.
   - Persist a copy of the latest diagram in the default state directory, or in `CODEX_EXCALIDRAW_STATE_DIR` when configured, with `scripts/session_state.py save` so later edits can reuse it.
4. Choose the fastest path:
   - For simple node-and-edge diagrams, use `scripts/generate_excalidraw.py`.
   - For soccer/football roster or tactical squad diagrams, use `scripts/create_tactical_roster.py`; do not hand-write the scene unless the template cannot represent the request.
   - For landmark/building elevation diagrams, use `scripts/create_building_elevation.py`; do not hand-write a building scene unless the template cannot represent the request.
   - For Mermaid or standard diagram syntax, consult `references/official-excalidraw.md` and prefer the official `@excalidraw/mermaid-to-excalidraw` path when available.
   - For spatial, editorial, tactical, dashboard-like, swimlane, field/court/map, roster, org chart, comparison, or visually composed diagrams, edit/create the JSON directly using `references/format.md`; do not force these into generic boxes and arrows.
5. Save output with the `.excalidraw` extension when a file is needed.
6. Generate a preview when the user expects to see the diagram in chat or browser:
   - Prefer `--preview` with `scripts/generate_excalidraw.py` for generated diagrams.
   - For direct JSON edits, create a separate SVG preview, generate a ready web URL when permitted, and use `scripts/preview_page.py` to create the HTML preview with the **Open in Excalidraw** button.
7. Validate the result with `scripts/validate_scene.py` when an `.excalidraw` file exists. It checks top-level shape, duplicate IDs, invisibly small elements, and text likely to be unreadable.
8. Run the visual quality gate in `references/quality-gate.md` before delivery. Fix readability or layout problems before showing the user.
9. Save latest-state metadata with `scripts/session_state.py save` unless the user explicitly asks for a throwaway diagram.
10. Tell the user what is available: preview image first, then the ready Excalidraw Web link and local preview page with the **Open in Excalidraw** button.

## Incremental Edit Workflow

When the user asks for a change to the previous diagram, do not start from scratch by default.

1. Run:

```bash
python3 ~/.codex/skills/excalidraw/scripts/session_state.py show
```

2. If `exists` is true and `scene` points to a readable `.excalidraw`, load that file and modify only the requested parts.
3. Preserve element IDs and unrelated layout whenever practical.
4. If the previous diagram was generated from a saved `spec` and the requested change maps cleanly to that spec, edit the spec and regenerate through the same template. Otherwise edit the `.excalidraw` JSON directly.
5. Generate a fresh preview, ready Excalidraw Web URL, and local preview page with the **Open in Excalidraw** button when network permission is available. Use local-only preview only if web upload is refused or explicitly undesired.
6. Validate with `scripts/validate_scene.py`.
7. Save the revised diagram back to session state with `scripts/session_state.py save`.
8. In the response, briefly say it reused the previous diagram and describe only what changed.

If no previous state exists, say that there is no saved previous diagram and create a new one from the user's request.

## Experience Levels

Use the right handoff based on what the environment supports:

- **File handoff**: create `.excalidraw` only. Best when the user just needs an editable file.
- **Web-link handoff**: create temporary files under `/private/tmp`, use the default web upload, return the `https://excalidraw.com/#json=...` URL plus preview image and preview HTML. This is the default because it gives the user a ready one-click Excalidraw Web path.
- **Preview handoff**: create `.excalidraw`, `-preview.svg`, and `-preview.html` without upload by passing `--no-web-link`. Use this when the user wants local-only/offline output or does not grant network permission.
- **Session-state handoff**: after creating or editing, copy the latest scene, preview, and spec into the default state directory with `scripts/session_state.py`. This makes follow-up edits faster and safer.
- **MCP widget handoff**: use a dedicated Excalidraw MCP/app integration if available. This is required for inline editing in chat, preserving manual edits via checkpoint IDs, and one-click open/edit actions backed by the host UI.

Do not describe preview HTML as equivalent to a native MCP widget. Explain that it is a local approximation: the button exists in the preview page, not as a native button embedded in the chat transcript.

## Creating Diagrams

Use the generator for architecture diagrams, process maps, simple flows, stakeholder maps, and other diagrams that can be represented as boxes plus arrows.

Before using the generator, ask: "Would a human expect this as a specific visual composition?" If yes, create a custom Excalidraw scene instead. Examples:

- Football/soccer team lists: draw a pitch, place starters by formation, and put reserves in a side panel.
- Journey maps: use columns or swimlanes, not a single horizontal chain.
- System architecture: use grouped zones and data-flow arrows, not one flat row if the system has layers.
- Research summaries: use sections, callouts, and evidence blocks.

For these cases, make the visual explanation the artifact. The diagram should teach at a glance, not merely list facts.

Read `references/visual-layouts.md` for pattern-specific guidance, `references/quality-gate.md` before delivering any composed visual, `references/official-excalidraw.md` when you need official Excalidraw APIs, import/export behavior, Mermaid conversion, or web-link caveats, and `references/authoring-rules.md` before writing custom scene-generation code.

For football/soccer roster diagrams, prefer ready web-link generation:

```bash
python3 ~/.codex/skills/excalidraw/scripts/create_tactical_roster.py - --name brazil-2026 --web-link
```

Pass the roster spec through stdin. The template enforces exactly 11 starters, short readable field labels, side-panel roster cards, SVG preview generation, and optional Excalidraw Web upload.

For landmark/building elevation diagrams, prefer ready web-link generation:

```bash
python3 ~/.codex/skills/excalidraw/scripts/create_building_elevation.py - --name empire-state --web-link
```

Pass the building spec through stdin or reuse a spec from `<workspace>/excalidraw/specs/`. The template creates a composed elevation, fact panel, callouts, SVG preview, validation, and optional Excalidraw Web upload.

Create a compact spec JSON:

```json
{
  "title": "Checkout Flow",
  "direction": "LR",
  "nodes": [
    {"id": "buyer", "label": "Buyer"},
    {"id": "web", "label": "Storefront"},
    {"id": "pay", "label": "Payment API"}
  ],
  "edges": [
    {"from": "buyer", "to": "web", "label": "Selects item"},
    {"from": "web", "to": "pay", "label": "Authorizes"}
  ]
}
```

Then run:

```bash
python3 ~/.codex/skills/excalidraw/scripts/generate_excalidraw.py spec.json output.excalidraw
```

For a Claude-style handoff with a visible preview and browser page, run:

```bash
python3 ~/.codex/skills/excalidraw/scripts/generate_excalidraw.py spec.json output.excalidraw --preview
```

For the default web-link handoff, pass the spec through stdin:

```bash
python3 ~/.codex/skills/excalidraw/scripts/create_web_diagram.py - --name checkout-flow
```

The command prints JSON containing `url`, `preview_svg`, `preview_html`, `excalidraw`, `spec`, `element_count`, and `temporary_dir`. In the default mode, `url` is a ready `https://excalidraw.com/#json=...` link and `preview_html` contains an **Open in Excalidraw** button pointing to it. Use this command for normal user requests so Codex does not need to create temp files manually.

After generation, persist the latest diagram for follow-up edits:

```bash
python3 ~/.codex/skills/excalidraw/scripts/session_state.py save \
  --scene /path/to/output.excalidraw \
  --preview /path/to/output-preview.svg \
  --html /path/to/output-preview.html \
  --url "https://excalidraw.com/#json=..." \
  --request "original user request" \
  --template "template-or-custom"
```

For local-only/offline output, skip the upload:

```bash
python3 ~/.codex/skills/excalidraw/scripts/create_web_diagram.py spec.json --name checkout-flow --no-web-link
```

If the user does not want files saved in their workspace, do not use `apply_patch` or manual file creation for `/private/tmp`. Use `create_web_diagram.py`, which handles staging safely.

This creates:

- `output.excalidraw`: the editable Excalidraw scene.
- `output-preview.svg`: a lightweight preview that can be embedded in chat.
- `output-preview.html`: a local preview card with buttons to download the `.excalidraw` file and open Excalidraw Web.
- By default, the preview HTML button points to the ready `https://excalidraw.com/#json=...` link, so the diagram opens already loaded in Excalidraw Web.
- With `--no-web-link`, the preview HTML falls back to a local-only button that can attempt browser-side upload on click.

Note: the default web-link flow uploads an encrypted, compressed copy of the diagram to Excalidraw's public JSON storage. The decryption key stays in the URL fragment. If network permission is refused, keep the no-upload preview fallback.

## MCP-Style Behavior

If the user asks for Claude-like Excalidraw behavior, explain the required moving parts:

1. A tool such as `read_me` to expose the supported Excalidraw JSON schema.
2. A tool such as `create_view` to validate elements and render a host-native widget.
3. A checkpoint store to persist the scene after every create/edit operation.
4. A way to read back manual widget edits before applying chat-requested changes.
5. A hosted or encoded scene URL for opening Excalidraw Web with the diagram preloaded.

In Codex without that MCP/widget integration, produce the best available fallback: `.excalidraw` plus preview SVG/HTML, and keep the spec JSON so future edits can be regenerated.

Supported spec fields:

- `title`: optional title shown at the top of the canvas.
- `direction`: `LR` for left-to-right or `TB` for top-to-bottom. Default is `LR`.
- `nodes`: required list of objects with `id` and `label`.
- `edges`: optional list of objects with `from`, `to`, and optional `label`.
- `groups`: optional list of objects with `label` and `nodes` to draw a light frame around related nodes.

## Editing Existing Files

When editing a supplied `.excalidraw` file:

1. Parse the JSON and preserve unknown fields.
2. Modify only the relevant elements.
3. Preserve `files` entries and image references.
4. Keep element IDs stable unless replacing an element.
5. Increment `version` or `versionNonce` for edited elements when practical.
6. Prefer restore-style repair semantics: missing defaults, stale bindings, and text dimensions should be repaired instead of blindly preserved when they break rendering.
7. Re-parse the saved JSON before handing it back.

Read `references/format.md` when direct JSON edits are needed.

## Style Guidance

- Use clear labels, short lines, and generous spacing.
- Prefer rectangles for components, diamonds only for decisions, and arrows for direction.
- Use restrained colors: dark strokes, light fills, and one accent color for emphasis.
- Avoid embedding long paragraphs in shapes; create note text near the diagram instead.
- Do not export an image unless the user specifically asks for a PNG/SVG/PDF.
- Never put long names plus metadata inside small shapes. Put short labels in the shape and move detail to a side panel, legend, or note.
- Optimize for readability at chat-preview scale, not just at full zoom in Excalidraw.
- For custom scripts, import `scene_primitives.py` and use keyword arguments for optional text settings to avoid positional-argument mistakes.
