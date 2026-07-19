## Context

Vela currently self-hosts and preloads one 345,588-byte `InterVariable.woff2`. Because WOFF2 is already compressed, recompressing the response does not materially reduce transfer size. The frontend is English (`<html lang="en">`) but renders dynamic ETF names and messages; Chinese text already falls through Inter to the `system-ui` chain because Inter does not contain CJK glyphs.

The current CSS contract uses only upright Inter Variable at weights `300–700`
and enables `cv01`, `ss03`, `zero`, and `calt`. Runtime source inspection shows
the non-ASCII UI characters `·`, `—`, `…`, `✓`, and `✗`; `⌘` documents the
Command Palette and is retained as part of that UI vocabulary. ETF names cross
the API as unconstrained strings, so unsupported characters must continue to
fall back rather than being rejected or transformed.

The existing font is Inter 4.0 (`Version 4.000;git-a52131595`) with SHA-256
`8af7bd5b545567adffb3dfceb5bedb353a522d7bf1b3a2b8af7b6064156babc0`.
It contains `opsz` (`14–32`) and `wght` (`100–900`) axes and embeds OFL 1.1
license metadata, but the repository does not currently retain a separate
license file or a non-public canonical generation input. Existing Vitest and
build checks do not inspect font structure, coverage, or request behavior.

Feasibility testing with FontTools 4.63.0 disproved the original draft's
80 KiB assumption: `U+0020–024F`, combining marks, broad punctuation/currency
ranges, arrows, and all layout features produced a 187,656-byte WOFF2.
A narrower product-aligned manifest retaining Latin-1, combining marks,
reviewed punctuation/symbols, and the required shaping features produced
approximately 86,220 bytes. The design therefore uses a 96 KiB ceiling rather
than weakening combining-mark rendering or pretending the original budget is
achievable.

## Goals / Non-Goals

**Goals:**

- Reduce the preloaded Inter Variable resource from 345,588 bytes to at most
  98,304 bytes.
- Preserve the current family, `opsz` and `wght` variable axes, outlines and
  metrics for retained glyphs, and enabled OpenType behavior.
- Preserve English, Latin-1, combining marks, reviewed punctuation/currency
  characters, and Vela's current UI symbols.
- Make generation byte-reproducible from committed inputs and a locked
  toolchain.
- Keep excluded scripts on the existing system-font fallback path.

**Non-Goals:**

- Adding a CJK webfont or guaranteeing identical typography for excluded scripts.
- Splitting the font into locale-specific resources or loading fonts dynamically by locale.
- Changing typography tokens, font weights, sizes, spacing, or application copy.
- Removing Inter's optical-size axis or otherwise altering its outlines.
- Deriving a minimal glyph set from current JSX strings.
- Claiming first-paint, LCP, or TTI improvements from font size alone.

## Decisions

### 1. Ship one Latin-focused variable subset

Generate `InterVariable-latin.woff2` and make it the sole served font under
`apps/web/public/fonts/`. The reviewed manifest requests:

- `U+0020–00FF` for ASCII and Latin-1;
- `U+0300–036F` for combining diacritics;
- `U+2013–2014`, `U+2018–201D`, `U+2022`, `U+2026`, `U+20AC`, `U+2122`,
  `U+2190–2199`, `U+2212`, `U+2318`, `U+2713`, and `U+2717` for reviewed
  punctuation, currency, navigation, and UI symbols.

FontTools retains the source-mapped intersection of those ranges. The control
positions inside `U+0020–00FF` are allowed to be unmapped, while every
explicitly required UI symbol must exist in both the source and output cmap.
The manifest intentionally excludes unsupported explicit requests from the
original draft (`U+2215` and `U+FFFD`), which are absent from the source cmap.
The generation script reads the manifest, and an automated check requires the
normalized CSS `unicode-range` to equal it, preventing declaration/binary
drift.

One subset is preferred over core/extended splitting because Vela ships a
single English frontend and has no product requirement for a separately
loadable extended-Latin locale. A second `@font-face` and conditional request
would add configuration and testing without a demonstrated use case.

Alternatives considered:

- **Source-text glyph extraction:** produces the smallest file but is unsafe for dynamic API values, user input, and future copy.
- **Broad `U+0020–024F` coverage with every layout feature:** measured
  187,656 bytes and cannot meet the performance objective.
- **An 80 KiB Latin-1 subset without combining support:** smaller, but makes
  decomposed Latin text depend on cross-font mark placement. The 96 KiB budget
  preserves combining behavior with little performance cost.
- **Core plus Latin Extended files:** creates another request and
  range-boundary complexity for languages Vela does not claim to support.
- **Use an external font CDN:** avoids the repository asset but adds a runtime dependency and weakens deterministic local operation.

### 2. Commit the exact source and pin the complete toolchain

Copy the current full font to the non-public canonical input
`scripts/fonts/inter/InterVariable-source.woff2` together with the upstream
OFL 1.1 text. The generation script verifies the source SHA-256 before doing
any work. After the subset has been generated, remove the former public copy.
This keeps the build input available offline and makes rollback possible
without treating a mutable download URL as an input.

Pin `fonttools[woff]==4.63.0` in the root development dependency group and
commit the resulting `uv.lock`, which also locks the Brotli dependency. The
documented repository-root command is:

`uv run python scripts/fonts/inter/subset_inter_variable.py`

The script uses the reviewed manifest and preserves only the features Vela
needs: `cv01`, `ss03`, `zero`, `calt`, plus `ccmp`, `kern`, `mark`, and `mkmk`
for composition, kerning, and combining-mark placement. Keeping every source
layout feature was measured to dominate the subset size without a product
requirement. The subset operation does not instantiate or narrow either
variable axis. CSS continues to expose `font-weight: 300 700`, while the
binary retains the source `opsz` and `wght` axes.

The script accepts an optional output path so tests can generate into pytest
temporary directories without overwriting the committed public asset.

Two independent generations from the same committed inputs must have
identical SHA-256 values. The committed output is then compared with a fresh
temporary generation by the font contract test; a mismatch fails validation.

Alternatives considered:

- **Download the source during generation:** saves repository space but makes
  regeneration depend on network availability and release-asset retention.
- **Keep every OpenType layout feature:** retains unused alternates and was a
  major contributor to the failed size budget.
- **Freeze weights to static fonts:** requires multiple files and removes the
  continuously variable `510` and `590` design-token weights.

### 3. Use an explicit filename and matching preload

Update the `@font-face` source and the `<link rel="preload">` to `/fonts/InterVariable-latin.woff2`, and delete the old full resource. A new filename avoids stale browser caches serving the old binary. Only this subset is preloaded; unsupported scripts must not cause another project-hosted font request.

`font-display: swap`, the existing fallback chains, family name, style, and weight range remain unchanged.

### 4. Validate the binary contract, not only source references

Automated checks will assert:

- the canonical source version, SHA-256, and OFL license input;
- byte-identical regeneration with the locked toolchain and manifest;
- WOFF2 format and an on-disk size of at most 98,304 bytes;
- required cmap coverage, including Vela's six non-ASCII UI characters;
- exclusion of representative Greek, Cyrillic, Latin Extended, IPA, and
  Vietnamese precomposed code points;
- preservation of the `opsz` and `wght` axes, absence of italic/slant axes,
  and availability of `cv01`, `ss03`, `zero`, `calt`, `ccmp`, `kern`, `mark`,
  and `mkmk`;
- exact agreement among the generated filename, CSS source, CSS `unicode-range`, and HTML preload;
- absence of the old full font from `apps/web/public/fonts/` and
  `apps/web/dist/fonts/`.

A browser smoke test under throttled networking will confirm one successful
font request, Inter rendering for retained Latin text, system fallback for a
Chinese ETF name, and no text wrapping, clipping, or symbol regression against
a pre-change baseline. Performance evidence records the font response payload,
request duration, and before/after byte delta; it does not infer application
timing guarantees.

### 5. Remove the superseded IBM Plex Mono requirement

The current `design-system` main spec still contains the historical
`Display font family token is registered` requirement, which mandates an IBM
Plex Mono `@font-face` and preload. Later requirements in the same capability
explicitly require `--font-display` to resolve to Inter Variable, prohibit IBM
Plex Mono resources, and make Inter Variable the sole loaded font. The current
implementation follows those later requirements.

This Change removes only that superseded requirement. It does not change any
token or application code and must not reintroduce IBM Plex Mono. Cleaning the
contradiction here is directly necessary for the post-archive font contract to
be satisfiable; broader historical spec cleanup remains out of scope.

## Risks / Trade-offs

- **[Unsupported Latin language falls back within a word]** → Vela claims only
  English UI coverage; preserve Latin-1 and combining marks, test mixed
  fallback, and propose a locale-specific coverage change if product language
  support expands.
- **[A required OpenType behavior disappears during closure]** → Preserve and
  test the four enabled features plus composition, kerning, and mark-positioning
  dependencies.
- **[A UI symbol changes to a platform glyph]** → Include the known symbol code points explicitly and add them to cmap and browser checks.
- **[Fallback metrics differ for excluded scripts]** → Accept platform-dependent rendering as the existing fallback policy; verify that mixed strings remain legible and do not overflow key ETF-name surfaces.
- **[Generated bytes drift]** → Pin the full toolchain, verify the canonical
  source hash, and compare a fresh generation with the committed output.
- **[The 96 KiB budget is missed]** → Fail the contract test; do not silently
  weaken coverage, required features, or variable axes.
- **[Historical spec cleanup expands scope]** → Remove only the one IBM Plex
  Mono requirement that directly contradicts the active sole-Inter contract;
  do not refactor unrelated design-system requirements.

## Migration Plan

1. Capture the pre-change browser/network baseline.
2. Copy the canonical full source outside the public tree, add its OFL
   license, pin the toolchain, and add the reviewed manifest and generation
   command.
3. Add failing binary, reproducibility, declaration, and asset contract tests.
4. Generate `InterVariable-latin.woff2` and confirm its metadata, coverage,
   determinism, and size before changing consumers.
5. Point `@font-face` and preload at the new resource, remove the former
   public full font, and use the matching
   `unicode-range`.
6. Build the frontend and confirm only the subset is copied to
   `apps/web/dist/fonts/`.
7. Run automated checks and browser/network smoke tests under normal and
   throttled conditions.

Rollback consists of copying the vendored canonical source back to
`apps/web/public/fonts/InterVariable.woff2`, reverting the `@font-face` and
preload URLs, and removing the subset-only manifest and validation constraints.

## Open Questions

None. If Vela later adds a supported non-English locale, its required script coverage should be proposed separately rather than silently expanding this preload.
