# Authoring Rules

Use these rules when creating custom Excalidraw scenes quickly.

## Prefer Reusable Inputs

Before writing a custom one-off script:

1. Check whether an existing template script can represent the request.
2. If no template exists, create a compact reusable spec in `<workspace>/excalidraw/specs/` when the subject could recur.
3. Use `scene_primitives.py` for shapes, text, lines, validation, state, and sharing.
4. Save the final scene with `session_state.py save` so follow-up edits can reuse it.

## Avoid Common Coding Errors

- Use keyword arguments for optional `text()` settings, especially `align`.
- Do not pass manual height to `text()`; height is calculated from font size.
- Run `validate_scene.py` before uploading to Excalidraw Web.
- Treat validator failures as design feedback, not merely technical errors.
- If a label fails validation, shorten the visual label and move detail to a note, side panel, or final response.

## Fast Creation Pattern

For one-off custom scenes:

1. Use `/private/tmp` for staging.
2. Import from `scene_primitives.py`.
3. Build editable Excalidraw JSON.
4. Build a matching lightweight SVG preview.
5. Validate the scene.
6. Upload with `share_scene`.
7. Save session state.

## Template Backlog

Create a new template when a pattern appears twice or when one-off code becomes long. Candidate templates:

- `create_flag_diagram.py`: flags and symbolic emblems.
- `create_floorplan.py`: aircraft, building, event, and room floorplans.
- `create_timeline.py`: historical, launch, project, and roadmap timelines.
- `create_comparison_matrix.py`: side-by-side or quadrant comparisons.
- `create_concept_map.py`: central idea plus surrounding concepts.
