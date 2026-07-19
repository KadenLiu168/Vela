## Why

The web frontend preloads a 345,588-byte full Inter Variable WOFF2 whose
existing compression makes HTTP gzip or Brotli ineffective. Vela's UI is
English and its configured ETF names are primarily Chinese, which already
use the `system-ui` fallback because Inter has no CJK glyphs. Serving a
reviewed Latin-1-focused subset therefore removes about 250 KB from the
highest-cost single resource while preserving current UI typography and the
existing fallback behavior.

## What Changes

- Replace the full served Inter Variable webfont with a reproducibly generated
  Latin-1-focused variable-font subset no larger than 96 KiB.
- Vendor the exact Inter 4.0 source WOFF2 and OFL license outside the public
  asset directory, record its SHA-256, and pin the FontTools WOFF2 toolchain so
  generation is offline, auditable, and byte-reproducible.
- Keep the existing `300–700` variable-weight contract and the `cv01`, `ss03`, `zero`, and `calt` OpenType behavior.
- Preserve Basic Latin, Latin-1, combining marks, reviewed punctuation and
  symbols, including middle dot, em dash, ellipsis, Command, check, and cross.
- Continue to render Chinese ETF names and other excluded scripts through the existing `system-ui` fallback chain.
- Update the font preload to target only the subset resource.
- Add automated structural and font-metadata checks plus browser/network verification for coverage, fallback, loading, and visual parity.
- Remove the superseded `Display font family token is registered`
  requirement, whose IBM Plex Mono contract conflicts with the later active
  requirements that prohibit IBM Plex Mono and make Inter Variable the sole
  loaded font.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `design-system`: Extend the sole-loaded-font contract with a size-bounded,
  reproducible Inter Variable subset, explicit glyph coverage, required
  OpenType behavior, preload consistency, and fallback requirements; remove
  the already-superseded IBM Plex Mono requirement.

## Impact

- Affected frontend assets and declarations: `apps/web/public/fonts/`, `apps/web/src/styles.css`, and `apps/web/index.html`.
- Affected development inputs and validation: `scripts/fonts/`,
  `scripts/README.md`, the root development dependency group and `uv.lock`,
  `tests/`, and the `design-system` capability.
- Application runtime APIs, frontend data types, and backend behavior are
  unchanged.
- Latin Extended, IPA, Greek, Cyrillic, Vietnamese precomposed characters in
  Latin Extended Additional, and broad symbol repertoires will no longer ship
  in the served font. Characters outside the declared subset use the existing
  platform fallback fonts.
