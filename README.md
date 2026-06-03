# Excalidraw Skill for Codex

This repository contains an original Codex skill created by **Fabricio Artur** for generating editable Excalidraw diagrams directly from natural-language requests.

I built this project to explore how far Codex skills can go beyond static file generation: creating real `.excalidraw` JSON, preview SVG/HTML files, ready-to-open Excalidraw Web links, and reusable local state so follow-up requests can edit the previous scene instead of redrawing everything from scratch.

This is not a copy of an existing skill. It is my own implementation, designed through hands-on iteration, testing, and refinement inside Codex.

## Example Output

This is an example generated with the skill: an editable Excalidraw-style tactical diagram for Brazil's 2026 FIFA World Cup squad.

![Brazil National Team FIFA World Cup 2026 Excalidraw example](examples/brazil-world-cup-2026-official-squad/brazil-world-cup-2026-official-squad-preview.svg)

The diagram is generated as structured Excalidraw data, so it can be opened, edited, and iterated instead of being treated as a static screenshot.

## What It Does

- Creates editable Excalidraw diagrams from natural-language requests.
- Generates chat-friendly SVG previews.
- Generates local preview HTML with an **Open in Excalidraw** button.
- Uploads encrypted scenes to Excalidraw Web by default when a ready web link is needed.
- Supports local-only output with `--no-web-link`.
- Persists the latest diagram locally for incremental edits.
- Includes specialized templates for tactical football rosters and building elevations.

## Structure

- `skill/`: development copy of the skill installed at `~/.codex/skills/excalidraw`.
- `specs/`: reusable JSON inputs for generating diagrams.
- `examples/`: previews, links, and test outputs worth keeping.
- `notes/`: findings, decisions, and Excalidraw references.
- `state/`: local runtime copy of the latest generated/edited diagram for faster incremental changes. This folder is intentionally ignored by git.

## Recommended Workflow

1. Edit and test the skill in `skill/`.
2. Save reusable specs in `specs/` when they speed up future generations.
3. Validate scripts and examples locally.
4. Sync to `~/.codex/skills/excalidraw` when the version is ready.

Sync command:

```bash
rsync -a --delete ./skill/ ~/.codex/skills/excalidraw/
```

## GitHub Publishing Notes

Commit these folders:

- `skill/`
- `specs/`
- `examples/`
- `notes/`
- `README.md`
- `.gitignore`

Do not commit `state/`; it is local runtime state and may contain the most recent user-requested diagram.

## Practical Rule

Use this folder as the versionable working source. The folder `~/.codex/skills/excalidraw` remains the active version loaded by Codex.

For iterations, the skill should save the latest diagram in `state/`. This lets requests like "increase the text size", "change the color", or "add a section" reuse the previous scene instead of redrawing everything.

When a pattern appears for the second time, record it in `notes/template-backlog.md`; before the third time, prefer creating a template.

## Authorship

Created, designed, and iterated by **Fabricio Artur**.

Built as an original Codex skill experiment to make Excalidraw diagram generation faster, more editable, and more useful for real workflows.

Made by Fabricio Artur.
