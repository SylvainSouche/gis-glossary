#!/usr/bin/env bash
# Collect the documents that may be used here but not redistributed.
#
#   tools/fetch_restricted.sh [--force]
#
# Reads registry/restricted-manifest.tsv and downloads each entry from its original
# source into sources/restricted/, which git ignores. Existing files are kept
# unless --force is given; git sources are always updated.
#
# Exits 1 if a download fails or a file differs from its recorded checksum.

set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/registry/restricted-manifest.tsv"
DEST="$ROOT/sources/restricted"
UA="gis-glossary/0.1 (terminology research)"
FORCE=0
FAILED=0

[ "${1:-}" = "--force" ] && FORCE=1
mkdir -p "$DEST"

fail() {
    echo "FAILED  $1: $2" >&2
    FAILED=1
}

verify() { # id path expected-sha256
    [ "$3" = "-" ] && return
    local actual
    actual="$(shasum -a 256 "$2" | cut -d' ' -f1)"
    if [ "$actual" = "$3" ]; then
        echo "ok      $1"
    else
        fail "$1" "checksum differs; source may have changed (got $actual)"
    fi
}

fetch_file() { # id url target sha
    local path="$DEST/$3"
    if [ -f "$path" ] && [ "$FORCE" -eq 0 ]; then
        verify "$1" "$path" "$4"
        return
    fi
    echo "fetch   $1"
    if curl -fsSL -A "$UA" --retry 2 -m 600 -o "$path.part" "$2"; then
        mv "$path.part" "$path"
        verify "$1" "$path" "$4"
    else
        rm -f "$path.part"
        fail "$1" "download failed: $2"
    fi
}

fetch_git() { # id url target
    local path="$DEST/$3"
    echo "git     $1"
    if [ -d "$path/.git" ]; then
        git -C "$path" -c core.hooksPath=/dev/null pull -q --ff-only ||
            fail "$1" "update failed"
    else
        git -c core.hooksPath=/dev/null clone -q --depth 1 "$2" "$path" ||
            fail "$1" "clone failed: $2"
    fi
}

while IFS=$'\t' read -r id method url target sha _; do
    case "$id" in id | "" | \#*) continue ;; esac
    case "$method" in
        file) fetch_file "$id" "$url" "$target" "$sha" ;;
        git) fetch_git "$id" "$url" "$target" ;;
        *) fail "$id" "unknown method $method" ;;
    esac
done <"$MANIFEST"

exit "$FAILED"
