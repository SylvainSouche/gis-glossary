#!/usr/bin/env bash
# Retrieve the restricted sources, then regenerate published/iso-mlgt/.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/tools/fetch_restricted.sh"
python3 "$ROOT/tools/extract_mlgt.py"
