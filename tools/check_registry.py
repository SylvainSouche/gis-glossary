#!/usr/bin/env python3
"""Validate registry/sources.csv and the published folders: run from anywhere, exits 1 on any problem."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = [r["code"] for r in csv.DictReader(open(ROOT / "registry/languages.csv", encoding="utf8"))]
STATUS = {"todo", "in_progress", "done", "duplicate", "rejected"}
ROLE = {"terminology", "corpus", "training", "method"}
COVERAGE = {"", "yes", "partial", "no"}
DISTRIBUTION = {"", "open", "restricted", "reference"}

rows = list(csv.DictReader(open(ROOT / "registry/sources.csv", encoding="utf8")))
ids = [r["id"] for r in rows]
MANIFEST = {r["id"] for r in csv.DictReader(open(ROOT / "registry/restricted-manifest.tsv", encoding="utf8"), delimiter="\t")}
REFERENCE = (ROOT / "registry/reference-only.md").read_text(encoding="utf8")
errors = []
for r in rows:
    who = r["id"]
    if ids.count(who) > 1:
        errors.append(f"{who}: duplicate id")
    if r["audit_status"] not in STATUS:
        errors.append(f"{who}: bad audit_status {r['audit_status']!r}")
    if r["role"] not in ROLE:
        errors.append(f"{who}: bad role {r['role']!r}")
    if r["duplicate_of"] and r["duplicate_of"] not in ids:
        errors.append(f"{who}: duplicate_of points to unknown {r['duplicate_of']!r}")
    if bool(r["duplicate_of"]) != (r["audit_status"] == "duplicate"):
        errors.append(f"{who}: duplicate_of and audit_status disagree")
    dist = r["distribution"]
    if dist not in DISTRIBUTION:
        errors.append(f"{who}: bad distribution {dist!r}")
    if r["audit_status"] == "done" and not dist:
        errors.append(f"{who}: audited but has no distribution class")
    if dist == "reference" and f"`{who}`" not in REFERENCE:
        errors.append(f"{who}: reference source missing from registry/reference-only.md")
    if (dist == "restricted") != (who in MANIFEST):
        errors.append(f"{who}: distribution and registry/restricted-manifest.tsv disagree")
    for code in LANGS:
        if r[f"lang_{code}"] not in COVERAGE:
            errors.append(f"{who}: bad lang_{code} {r[f'lang_{code}']!r}")

for folder in sorted(p for base in ("sources/open", "published") for p in (ROOT / base).iterdir() if p.is_dir()):
    if not (folder / "ATTRIBUTION.md").exists():
        errors.append(f"{folder.relative_to(ROOT)}: missing ATTRIBUTION.md")

print("\n".join(errors) or f"ok: {len(rows)} rows, {len(LANGS)} languages")
sys.exit(1 if errors else 0)
