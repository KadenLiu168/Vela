from __future__ import annotations

import re
from hashlib import sha256
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FONTS = ROOT / "apps/web/public/fonts"
SANS = PUBLIC_FONTS / "Geist-Variable.woff2"
MONO = PUBLIC_FONTS / "GeistMono-Variable.woff2"
PROVENANCE = ROOT / "scripts/fonts/geist/PROVENANCE.md"
LICENSE = ROOT / "scripts/fonts/geist/OFL-1.1.txt"
STYLES = ROOT / "apps/web/src/styles.css"
INDEX = ROOT / "apps/web/index.html"

# Pinned by the design-system OpenSpec delta (official Geist v1.7.2 tag).
SANS_SHA256 = "2ffebe993e969069a9789d15164b7715d42491b5835516c5e3b935d5f81b05f1"
MONO_SHA256 = "afaacc4c5fbba89d2ebf7a02dc4070208540874592a5504d57175782fe893101"


def axes(path: Path) -> dict[str, tuple[float, float, float]]:
    font = TTFont(path)
    return {
        axis.axisTag: (axis.minValue, axis.defaultValue, axis.maxValue)
        for axis in font["fvar"].axes
    }


def test_vendored_binaries_match_the_pinned_official_hashes() -> None:
    assert sha256(SANS.read_bytes()).hexdigest() == SANS_SHA256
    assert sha256(MONO.read_bytes()).hexdigest() == MONO_SHA256
    assert "v1.7.2" in PROVENANCE.read_text(encoding="utf-8")


def test_faces_are_upright_variable_woof2_with_weight_only_axes() -> None:
    for path in (SANS, MONO):
        font = TTFont(path)
        assert font.flavor == "woff2"
        font_axes = axes(path)
        assert set(font_axes) == {"wght"}
        weight_min, _default, weight_max = font_axes["wght"]
        assert (weight_min, weight_max) == (100.0, 900.0)
        assert "ital" not in font_axes
        assert "slnt" not in font_axes


def test_families_are_the_official_geist_names() -> None:
    assert TTFont(SANS)["name"].getDebugName(1) == "Geist"
    assert TTFont(MONO)["name"].getDebugName(1) == "Geist Mono"


def test_official_ofl_notice_is_vendored() -> None:
    license_text = LICENSE.read_text(encoding="utf-8")
    assert "SIL OPEN FONT LICENSE Version 1.1" in license_text
    assert "The Geist Project Authors" in license_text


def test_cmap_retains_reviewed_coverage_and_falls_back_for_the_rest() -> None:
    sans_cmap = TTFont(SANS).getBestCmap()
    mono_cmap = TTFont(MONO).getBestCmap()

    # Latin text, digits, punctuation, minus, and arrows that the UI relies
    # on must be covered by the intended family itself.
    required_sans = (
        ord("A"),
        ord("z"),
        0x00E9,  # é
        0x00B7,  # ·
        0x2014,  # em dash
        0x2026,  # ellipsis
        0x2190,  # ←
        0x2192,  # →
    )
    required_mono = (ord("0"), ord("9"), ord("%"), 0x2212, 0x2190, 0x2192)
    for codepoint in required_sans:
        assert codepoint in sans_cmap
    for codepoint in required_mono:
        assert codepoint in mono_cmap

    # Glyphs Geist v1.7.2 does not carry (CJK, ⌘, ✓, ✗) must NOT be in the
    # font: they render through the documented system fallback chains in
    # --font-sans instead of tofu.
    for unsupported in (0x4E2D, 0x2318, 0x2713, 0x2717):  # 中 ⌘ ✓ ✗
        assert unsupported not in sans_cmap
        assert unsupported not in mono_cmap


def test_font_declarations_preloads_and_asset_inventory_are_in_lockstep() -> None:
    styles = STYLES.read_text(encoding="utf-8")
    index = INDEX.read_text(encoding="utf-8")

    faces = re.findall(r"@font-face\s*{[^}]*}", styles)
    assert len(faces) == 2

    expected = {
        '"Geist Sans"': "/fonts/Geist-Variable.woff2",
        '"Geist Mono"': "/fonts/GeistMono-Variable.woff2",
    }
    srcs: dict[str, str] = {}
    for face in faces:
        family_match = re.search(r'font-family:\s*("[^"]+")', face)
        url_match = re.search(r'src:\s*url\("([^"]+)"\)', face)
        assert family_match is not None and url_match is not None
        srcs[family_match.group(1)] = url_match.group(1)
        assert "font-display: swap" in face
        assert "font-weight: 100 900" in face
        assert "unicode-range" not in face
        assert "font-feature-settings" not in face
    assert srcs == expected

    preloads = re.findall(r'<link\s+rel="preload"\s+href="([^"]+)"\s+as="font"', index)
    assert sorted(preloads) == sorted(expected.values())
    for preload in preloads:
        assert preload in srcs.values()

    assert sorted(path.name for path in PUBLIC_FONTS.iterdir() if path.is_file()) == [
        "Geist-Variable.woff2",
        "GeistMono-Variable.woff2",
    ]
