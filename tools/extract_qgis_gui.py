#!/usr/bin/env python3
"""
extract_qgis_gui.py - publish QGIS interface labels as a compressed CSV.

    python3 tools/extract_qgis_gui.py [COMMIT]

Downloads the translation catalogues of the given qgis/QGIS commit into cache/,
keeps finished label-like strings, and writes published/qgis-gui/. Without a
commit, the commit recorded in published/qgis-gui/commit.txt is reused.
"""

import csv
import html
import lzma
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "published" / "qgis-gui"
COMMIT_FILE = OUT_DIR / "commit.txt"
CACHE = ROOT / "cache" / "qgis-i18n"
RAW = "https://raw.githubusercontent.com/qgis/QGIS/{commit}/i18n/qgis_{language}.ts"
LICENCE_URL = "https://raw.githubusercontent.com/qgis/QGIS/{commit}/COPYING"
USER_AGENT = "gis-glossary/0.1 (terminology research)"
# Target languages with a catalogue; nn, sl and el have none.
LANGUAGES = "fr es de it nb is da pl ro bg sk sv".split()
MAX_LENGTH = 120

ATTRIBUTION = """# QGIS interface labels

- **Source:** QGIS translation catalogues, <https://github.com/qgis/QGIS/tree/{commit}/i18n>
- **Copyright:** QGIS project and its translators
- **Licence:** GNU General Public License, as for the QGIS repository (`COPYING`)
- **Commit:** `{commit}`
- **Changes:** finished translations only, up to {max_length} characters, without
  markup or line breaks; keyboard accelerators removed; converted to CSV and compressed
  with xz. Regenerate with `tools/extract_qgis_gui.py`.
"""


def fetch(url, target):
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=600) as response:
        data = response.read()
    target.write_bytes(data)


def clean(text):
    """Remove accelerators, keeping a literal ampersand written as &&."""
    text = html.unescape(text or "").replace("&&", "\0").replace("&", "").replace("\0", "&")
    return text.strip()


def usable(text):
    return text and len(text) <= MAX_LENGTH and "\n" not in text and "<" not in text


def rows_of(path, language):
    for context in ET.parse(path).getroot().iter("context"):
        name = context.findtext("name") or ""
        for message in context.iter("message"):
            translation = message.find("translation")
            if translation is None or message.get("numerus") == "yes":
                continue
            if translation.get("type") in ("unfinished", "obsolete", "vanished"):
                continue
            source = clean(message.findtext("source"))
            target = clean(translation.text)
            if usable(source) and usable(target):
                yield language, name, source, target


def main():
    if len(sys.argv) > 1:
        commit = sys.argv[1]
    else:
        commit = COMMIT_FILE.read_text(encoding="utf8").strip()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = set()
    for language in LANGUAGES:
        path = CACHE / commit / f"qgis_{language}.ts"
        fetch(RAW.format(commit=commit, language=language), path)
        found = set(rows_of(path, language))
        rows |= found
        print(language, len(found))

    with lzma.open(OUT_DIR / "qgis_gui_labels.csv.xz", "wt", encoding="utf8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["language", "context", "source_text", "translation"])
        writer.writerows(sorted(rows))

    fetch(LICENCE_URL.format(commit=commit), CACHE / commit / "COPYING")
    (OUT_DIR / "COPYING").write_bytes((CACHE / commit / "COPYING").read_bytes())
    COMMIT_FILE.write_text(commit + "\n", encoding="utf8")
    (OUT_DIR / "ATTRIBUTION.md").write_text(
        ATTRIBUTION.format(commit=commit, max_length=MAX_LENGTH), encoding="utf8"
    )
    print("total", len(rows))


if __name__ == "__main__":
    main()
