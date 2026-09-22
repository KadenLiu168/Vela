# Geist font provenance

Vela serves two variable WOFF2 resources from the official Geist v1.7.2
distribution:

| Runtime file | Source URL (tag `v1.7.2`) | SHA-256 |
| --- | --- | --- |
| `apps/web/public/fonts/Geist-Variable.woff2` | `https://raw.githubusercontent.com/vercel/geist-font/v1.7.2/fonts/Geist/webfonts/Geist%5Bwght%5D.woff2` (release-zip member `geist-font/Geist/webfonts/Geist[wght].woff2`) | `2ffebe993e969069a9789d15164b7715d42491b5835516c5e3b935d5f81b05f1` |
| `apps/web/public/fonts/GeistMono-Variable.woff2` | `https://raw.githubusercontent.com/vercel/geist-font/v1.7.2/fonts/GeistMono/webfonts/GeistMono%5Bwght%5D.woff2` (release-zip member `geist-font/GeistMono/webfonts/GeistMono[wght].woff2`) | `afaacc4c5fbba89d2ebf7a02dc4070208540874592a5504d57175782fe893101` |

- Release tag: https://github.com/vercel/geist-font/releases/tag/v1.7.2
- License: SIL Open Font License 1.1 (`OFL-1.1.txt` in this directory, copied
  from the tag's root `OFL.txt`).
- Verified metadata (FontTools): WOFF2 flavor, family name 1 = `Geist` /
  `Geist Mono`, single upright `wght` axis covering 100–900, no `ital`/`slnt`
  axes. The CSS declares the product-facing families `Geist Sans` and
  `Geist Mono`.

## Note on the release zip

The `geist-font-v1.7.2.zip` release asset was repackaged after the tag was cut:
its `Geist[wght].woff2` / `GeistMono[wght].woff2` members hash to
`a369fcf5…` / `fba8f577…` and do not match the pinned hashes above. The pinned
hashes correspond to the v1.7.2 **git tag** sources served by
`raw.githubusercontent.com` (the npm package `geist@1.7.2` ships the
repackaged variants). Vela pins the tag files listed in the table; re-verifying
a future upgrade requires its own reviewed contract change.

Verified on 2026-09-21 by downloading the tag URLs and comparing SHA-256 with
the `design-system` delta spec.
