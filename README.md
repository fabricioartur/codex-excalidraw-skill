# Excalidraw Skill for Codex

This repository contains a Codex skill for creating editable Excalidraw diagrams.

The skill generates real `.excalidraw` JSON, preview SVG/HTML files, and ready-to-open Excalidraw Web links. It also keeps the latest generated diagram in local state so follow-up requests can edit the previous scene instead of redrawing everything from scratch.

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
rsync -a --delete /Users/fabricioartur/Codex/excalidraw/skill/ /Users/fabricioartur/.codex/skills/excalidraw/
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
