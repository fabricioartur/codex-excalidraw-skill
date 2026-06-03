# Excalidraw JSON Notes

Use this reference when creating or editing `.excalidraw` files directly.

## Top-Level Shape

An Excalidraw file is JSON with:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": {},
  "files": {}
}
```

Keep `files` when the scene contains images. Do not remove unknown top-level keys from existing files.

## Common Element Fields

Most elements include:

- `id`: stable unique string.
- `type`: `rectangle`, `text`, `arrow`, `line`, `ellipse`, `diamond`, or similar.
- `x`, `y`, `width`, `height`, `angle`.
- `strokeColor`, `backgroundColor`, `fillStyle`, `strokeWidth`, `strokeStyle`, `roughness`, `opacity`.
- `groupIds`, `frameId`, `roundness`, `seed`, `version`, `versionNonce`, `isDeleted`.
- `boundElements`, `updated`, `link`, `locked`.

Text elements also need `text`, `fontSize`, `fontFamily`, `textAlign`, `verticalAlign`, `containerId`, `originalText`, and `lineHeight`.

Arrow elements need `points`, `startBinding`, `endBinding`, `startArrowhead`, and `endArrowhead`.

## Practical Defaults

- Rectangle dimensions: 220 x 88 for architecture nodes.
- Text font: `fontFamily: 1`, `fontSize: 20`, `lineHeight: 1.25`.
- Stroke: `#1e1e1e`, background: `#f8f9fa`.
- Accent fill: `#e7f5ff`, accent stroke: `#1971c2`.
- Arrowhead: `endArrowhead: "arrow"`.

## Validation Checklist

Before delivering a file:

1. Parse it with a JSON parser.
2. Confirm `type` is `excalidraw`.
3. Confirm `elements` is an array.
4. Confirm each element has an `id`, `type`, numeric `x`, and numeric `y`.
5. Confirm referenced edge endpoints or image file IDs still exist.
