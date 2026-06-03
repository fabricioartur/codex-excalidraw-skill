# Decisions

- Project folder name: `/Users/fabricioartur/Codex/excalidraw`.
- The active skill remains in `~/.codex/skills/excalidraw`.
- New diagrams should not be saved in the workspace by default; use temporary staging and generate a ready `https://excalidraw.com/#json=...` link during creation. The preview HTML button should point directly to that ready link. Use local-only output only if network access is refused or explicitly undesired.
- Specialized visual diagrams should use templates or custom layouts, not the generic boxes-and-arrows generator.
- Before delivery, run structural validation and readability checks.
- The skill should persist the latest diagram in `/Users/fabricioartur/Codex/excalidraw/state` to support incremental edits without redrawing from scratch.
- Saving local specs is allowed when it speeds up creation, testing, and iteration.
