#!/usr/bin/env python3
"""
assisted_translate.py - translate a text line by line with an Ollama model.

    python3 tools/assisted_translate.py --mode routed|assisted --model NAME \
        --input FILE --output FILE [--source fr] [--target English]

routed    sends only source-language text to the model, after removing copy-paste
          artifacts; English, code, paths and place names pass through.
assisted  does the same and supplies matching GUI labels and glossary terms from
          build/glossary.sqlite. No hand-written term list is used.

Prompt format and sampling follow the SIGate translation tool. Answers are cached in
build/mt_cache/, so an interrupted run resumes.
"""

import argparse
import hashlib
import json
import re
import sqlite3
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATABASE = ROOT / "build" / "glossary.sqlite"
CACHE = ROOT / "build" / "mt_cache"
OLLAMA = "http://localhost:11434/api/chat"
DOMAIN = "geographic information systems and cartography"
OPTIONS = {
    "temperature": 0.7, "top_p": 0.6, "top_k": 20, "repeat_penalty": 1.05,
    "num_ctx": 4096, "seed": 42,
}
MAX_HINTS = 12
MAX_WORDS = 8

ICON_NAMES = (
    "projectionEnabled fileSave dataSourceManager addOgrLayer addRasterLayer "
    "radioButtonOn checkbox toggleEditing calculateField capturePoint saveEdits"
).split()
ICONS = re.compile(r"\|?\s*\b(" + "|".join(ICON_NAMES) + r")\b\s*\|?\s*")
ROLE = re.compile(r":(guilabel|file|kbd|menuselection|sup):`?")
FRENCH = set(
    "le la les des du de un une dans sur pour et vous cliquez sélectionnez assurez ouvrez "
    "est sont que qui avec au aux ce cette en".split()
)
ENGLISH = set(
    "the click select in on for and your set when follow open check to of is are that "
    "with this you it a an".split()
)
CODE = re.compile(r'@\d|^\s*["(\[$].*(=|>|<|\*|\bOR\b|\bin\b)|^\s*\$\w+\s*$|^\s*"[^"]*" ')


def words_of(text):
    return re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)*", text.lower())


def strip_artifacts(line):
    line = ICONS.sub(" ", ROLE.sub("", line)).replace("`", "")
    line = re.sub(r"\s*:\s*:\s*$", " :", line)
    return re.sub(r"\s+", " ", line).strip()


def normalize_label(text):
    text = text.replace("…", "").replace("...", "").replace("’", "'")
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", text).strip(" :.,;").lower()


def load_resources(source, target="en"):
    """(labels, terms): normalized source-language text mapped to target-language text."""
    db = sqlite3.connect(DATABASE)
    votes = defaultdict(Counter)
    if target == "en":
        query = "SELECT translation_normalized, source_text FROM gui_label WHERE language = ?"
        language = source
    else:
        query = "SELECT source_normalized, translation FROM gui_label WHERE language = ?"
        language = target
    for key, text in db.execute(query, (language,)):
        votes[key][text] += 1
    # Most frequent string; ties resolved alphabetically for repeatability.
    labels = {k: sorted(v.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for k, v in votes.items()}
    terms = {}
    for text, translated, source_id in db.execute(
        "SELECT a.text, b.text, e.source_id FROM concept c"
        " JOIN concept_entry ce ON ce.concept_id = c.id"
        " JOIN entry e ON e.id = ce.entry_id"
        " JOIN term a ON a.entry_id = ce.entry_id"
        " JOIN term b ON b.entry_id = ce.entry_id"
        " WHERE c.ambiguous = 0 AND a.language = ? AND b.language = ?"
        " AND a.term_type = 'term' AND b.term_type = 'term'"
        " AND a.status NOT IN ('deprecated', 'superseded')"
        " AND b.status NOT IN ('deprecated', 'superseded')"
        " ORDER BY b.status = 'preferred' DESC, b.id",
        (source, target),
    ):
        key = normalize_label(text)
        # Single words are too ambiguous outside the GIS-specific source.
        if "(" in translated or (" " not in key and source_id != "iso-tc-211-mlgt-geolexica"):
            continue
        terms.setdefault(key, translated)
    return labels, terms


def passes_through(line, labels):
    """True when the line should not reach the model."""
    if not re.search(r"[^\W\d_]", line) or line.startswith("../") or CODE.search(line):
        return True
    words = words_of(line)
    french, english = sum(w in FRENCH for w in words), sum(w in ENGLISH for w in words)
    if english >= 2 and french == 0:
        return True
    is_name = len(words) <= 2 and french == 0 and line.istitle() and not re.search(r"\d", line)
    return is_name and normalize_label(line) not in labels


def find_hints(line, labels, terms):
    tokens = re.findall(r"[^\W_]+(?:['’\-][^\W_]+)*", line)
    used, hints, seen = set(), [], set()
    for size in range(min(MAX_WORDS, len(tokens)), 0, -1):
        for start in range(len(tokens) - size + 1):
            span = set(range(start, start + size))
            if span & used:
                continue
            original = " ".join(tokens[start:start + size])
            key = normalize_label(original)
            if size == 1:
                capitalized = (start > 0 or len(tokens) == 1) and original[:1].isupper()
                if len(original) < 4:
                    continue
                # The label wins a conflict: it is the wording used in GIS software.
                english = (labels.get(key) or terms.get(key)) if key in terms or capitalized else None
            else:
                english = labels.get(key) or terms.get(key)
            if english and english.lower() != original.lower() and key not in seen:
                used |= span
                seen.add(key)
                hints.append((original, english))
    return hints[:MAX_HINTS]


def build_prompt(text, target, hints):
    lines = []
    if hints:
        lines.append("Reference the following translations:")
        lines += [f"{a} translates to {b}" for a, b in hints]
        lines.append("")
    lines.append(f"[Background Information]\nDomain: {DOMAIN}.\n")
    lines.append(
        f"Please translate the following text into {target}, taking the provided "
        "background information into consideration. Only output the translated result, "
        "without any additional explanation.\n"
    )
    lines.append(f"[Source Text]\n{text}")
    return "\n".join(lines)


def ask(model, prompt):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha256(f"{model}\n{prompt}".encode()).hexdigest() + ".txt")
    if path.exists():
        return path.read_text(encoding="utf8")
    body = {
        "model": model, "stream": False, "options": OPTIONS,
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        OLLAMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=900) as response:
        answer = json.load(response)["message"]["content"].strip()
    path.write_text(answer, encoding="utf8")
    return answer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("routed", "assisted"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source", default="fr")
    parser.add_argument("--target", default="English")
    args = parser.parse_args()

    labels, terms = load_resources(args.source)
    output, sent, hinted = [], 0, 0
    for raw in Path(args.input).read_text(encoding="utf8").splitlines():
        line = strip_artifacts(raw)
        if not line or passes_through(line, labels):
            output.append(raw.rstrip() if passes_through(raw.strip() or " ", labels) else line)
            continue
        hints = find_hints(line, labels, terms) if args.mode == "assisted" else []
        sent += 1
        hinted += bool(hints)
        output.append(ask(args.model, build_prompt(line, args.target, hints)))
        Path(args.output).write_text("\n".join(output) + "\n", encoding="utf8")
    Path(args.output).write_text("\n".join(output) + "\n", encoding="utf8")
    print(f"{args.mode} {args.model}: {sent} lines sent, {hinted} with hints")


if __name__ == "__main__":
    main()
