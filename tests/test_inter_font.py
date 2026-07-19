from __future__ import annotations

import json
import re
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FONTS = ROOT / "apps/web/public/fonts"
SUBSET = PUBLIC_FONTS / "InterVariable-latin.woff2"
SOURCE = ROOT / "scripts/fonts/inter/InterVariable-source.woff2"
LICENSE = ROOT / "scripts/fonts/inter/OFL-1.1.txt"
MANIFEST = ROOT / "scripts/fonts/inter/unicode_manifest.json"
SCRIPT = ROOT / "scripts/fonts/inter/subset_inter_variable.py"
STYLES = ROOT / "apps/web/src/styles.css"
INDEX = ROOT / "apps/web/index.html"
MAX_FONT_BYTES = 98_304
SOURCE_SHA256 = "8af7bd5b545567adffb3dfceb5bedb353a522d7bf1b3a2b8af7b6064156babc0"


def axes(path: Path) -> dict[str, tuple[float, float, float]]:
    font = TTFont(path)
    return {
        axis.axisTag: (axis.minValue, axis.defaultValue, axis.maxValue)
        for axis in font["fvar"].axes
    }


def test_served_subset_is_a_small_upright_variable_font_usable_at_v3_weights() -> None:
    font = TTFont(SUBSET)

    assert font.flavor == "woff2"
    assert SUBSET.stat().st_size <= MAX_FONT_BYTES
    assert axes(SUBSET)["opsz"] == axes(SOURCE)["opsz"]
    assert axes(SUBSET)["wght"] == axes(SOURCE)["wght"]
    assert "ital" not in axes(SUBSET)
    assert "slnt" not in axes(SUBSET)

    styles = STYLES.read_text(encoding="utf-8")
    assert "font-weight: 300 700" in styles
    assert all(300 <= weight <= 700 for weight in (300, 400, 510, 590))


def test_subset_cmap_retains_reviewed_coverage_and_excludes_undeclared_repertoires() -> None:
    cmap = TTFont(SUBSET).getBestCmap()

    required_codepoints = (
        ord("A"),
        ord("z"),
        ord("0"),
        0x00E9,
        0x0301,
        0x00B7,
        0x2014,
        0x2026,
        0x2318,
        0x2713,
        0x2717,
    )
    for codepoint in required_codepoints:
        assert codepoint in cmap

    for codepoint in (0x03A9, 0x0416, 0x0104, 0x0259, 0x1EA1):
        assert codepoint not in cmap


def layout_features(path: Path) -> set[str]:
    font = TTFont(path)
    return {
        record.FeatureTag
        for table_name in ("GSUB", "GPOS")
        if table_name in font
        for record in font[table_name].table.FeatureList.FeatureRecord
    }


def test_subset_preserves_required_layout_features() -> None:
    required_features = {"ccmp", "kern", "mark", "mkmk", "cv01", "ss03", "zero", "calt"}
    assert required_features <= layout_features(SUBSET)


def generate_subset(output: Path) -> None:
    subprocess.run([sys.executable, str(SCRIPT), str(output)], cwd=ROOT, check=True)


def test_subset_generation_is_reproducible_from_the_vendored_source(tmp_path: Path) -> None:
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    license_text = LICENSE.read_text(encoding="utf-8")
    assert "SIL OPEN FONT LICENSE Version 1.1" in license_text
    assert "by changing or porting the Font Software to a new environment" in license_text

    first = tmp_path / "first.woff2"
    second = tmp_path / "second.woff2"
    generate_subset(first)
    generate_subset(second)

    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes() == SUBSET.read_bytes()


def test_font_declaration_preload_asset_and_manifest_are_in_lockstep() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_range = ",".join(manifest["ranges"])
    styles = STYLES.read_text(encoding="utf-8")
    index = INDEX.read_text(encoding="utf-8")

    match = re.search(r"unicode-range:\s*([^;]+);", styles)
    assert match is not None
    assert re.sub(r"\s+", "", match.group(1)).upper() == expected_range
    assert 'src: url("/fonts/InterVariable-latin.woff2")' in styles
    assert 'href="/fonts/InterVariable-latin.woff2"' in index
    assert sorted(path.name for path in PUBLIC_FONTS.iterdir() if path.is_file()) == [
        "InterVariable-latin.woff2"
    ]
