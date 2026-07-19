"""Generate Vela's reproducible Inter Variable Latin-focused webfont."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

MAX_OUTPUT_BYTES = 98_304
SOURCE_SHA256 = "8af7bd5b545567adffb3dfceb5bedb353a522d7bf1b3a2b8af7b6064156babc0"
LAYOUT_FEATURES = ["ccmp", "kern", "mark", "mkmk", "cv01", "ss03", "zero", "calt"]
SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_PATH = SCRIPT_DIR / "InterVariable-source.woff2"
MANIFEST_PATH = SCRIPT_DIR / "unicode_manifest.json"
DEFAULT_OUTPUT_PATH = Path("apps/web/public/fonts/InterVariable-latin.woff2")


def parse_unicode_range(value: str) -> range:
    start, _, end = value.removeprefix("U+").partition("-")
    return range(int(start, 16), int(end or start, 16) + 1)


def load_manifest() -> tuple[list[int], list[int]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    codepoints = [
        codepoint for value in manifest["ranges"] for codepoint in parse_unicode_range(value)
    ]
    required_symbols = [
        int(value.removeprefix("U+"), 16) for value in manifest["required_ui_symbols"]
    ]
    return codepoints, required_symbols


def verify_source(source: Path, required_symbols: list[int]) -> None:
    actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual_hash != SOURCE_SHA256:
        raise ValueError(f"Unexpected Inter source SHA-256: {actual_hash}")

    source_cmap = TTFont(source).getBestCmap()
    missing_symbols = [
        f"U+{codepoint:04X}" for codepoint in required_symbols if codepoint not in source_cmap
    ]
    if missing_symbols:
        raise ValueError(
            f"Inter source is missing required UI symbols: {', '.join(missing_symbols)}"
        )


def generate(output: Path) -> None:
    codepoints, required_symbols = load_manifest()
    verify_source(SOURCE_PATH, required_symbols)

    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = LAYOUT_FEATURES
    options.name_IDs = ["*"]
    options.name_legacy = True

    font = TTFont(SOURCE_PATH)
    font.recalcTimestamp = False
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=codepoints)
    subsetter.subset(font)

    output.parent.mkdir(parents=True, exist_ok=True)
    font.save(output)
    if output.stat().st_size > MAX_OUTPUT_BYTES:
        raise ValueError(f"Subset exceeds {MAX_OUTPUT_BYTES} bytes: {output.stat().st_size}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    generate(args.output)


if __name__ == "__main__":
    main()
