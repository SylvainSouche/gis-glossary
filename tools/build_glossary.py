#!/usr/bin/env python3
"""
build_glossary.py - build build/glossary.sqlite from the published term lists.

Loads each source as it stands, then groups entries whose English terms match
exactly. Those groups are candidates: an exact match does not prove the same
sense, so a group is marked ambiguous when one source has several entries in it.
"""

import csv
import io
import lzma
import tarfile
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATABASE = ROOT / "build" / "glossary.sqlite"
SCHEMA = ROOT / "schema" / "glossary.sql"
MLGT = ROOT / "published" / "iso-mlgt" / "mlgt_terms.csv"
IATE = ROOT / "published" / "iate" / "iate_gis_terms.csv"
GUI = ROOT / "published" / "qgis-gui"

TERM_TYPES = {
    "expression": "term", "fullForm": "term", "shortForm": "term",
    "abbreviation": "abbreviation", "phrase": "phrase", "formula": "formula",
}
IATE_STATUS = {
    "preferredTerm-admn-sts": "preferred", "admittedTerm-admn-sts": "admitted",
    "deprecatedTerm-admn-sts": "deprecated", "supersededTerm-admn-sts": "superseded",
    "proposedTerm-admn-sts": "proposed",
}


def normalize(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip().lower()


def normalize_label(text):
    """Forgiving form for matching labels: no accents, case or ellipsis."""
    text = text.replace("\u2026", "").replace("...", "").replace("\u2019", "'")
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", text).strip(" :").lower()


def load_gui_labels(db):
    commit = (GUI / "commit.txt").read_text(encoding="utf8").strip()
    with lzma.open(GUI / "qgis_gui_labels.csv.xz", "rt", encoding="utf8", newline="") as stream:
        db.executemany(
            "INSERT OR IGNORE INTO gui_label (application, version, context, source_text, language,"
            " translation, source_normalized, translation_normalized) VALUES (?,?,?,?,?,?,?,?)",
            (("qgis", commit, r["context"], r["source_text"], r["language"], r["translation"],
              normalize_label(r["source_text"]), normalize_label(r["translation"]))
             for r in csv.DictReader(stream)),
        )


SNORRE = ROOT / "sources" / "open" / "snorre" / "snorre.tar.gz"
SNORRE_COLUMNS = {
    "nb": ("Bokmål", "BokmålSynonym", "BokmålForkortelse"),
    "nn": ("Nynorsk", "NynorskSynonym", "NynorskForkortelse"),
    "en": ("Engelsk", "EngelskSynonym", "EngelskForkortelse"),
    "fr": ("Fransk", "FranskSynonym", "FranskForkortelse"),
    "de": ("Tysk", "TyskSynonym", "TyskForkortelse"),
}


def load_snorre(db):
    """Load the SNORRE word list: main term preferred, synonym admitted, abbreviation."""
    with tarfile.open(SNORRE) as archive:
        stream = io.TextIOWrapper(archive.extractfile("snorre/snorre.txt"), encoding="latin1")
        rows = list(csv.DictReader(stream, delimiter="\t", quoting=csv.QUOTE_NONE))
    db.execute("INSERT INTO source VALUES (?,?,?,?,?)", (
        "snorre", "SNORRE word list, copyright Standard Norge",
        "https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-24/",
        "CC BY 4.0 (Språkbanken sbr-24); credit Standard Norge", "2026-11-09"))
    for row in rows:
        entry = db.execute("INSERT INTO entry (source_id, source_key) VALUES ('snorre', ?)",
                           (row["TermEntryId"],)).lastrowid
        for language, (main, synonym, abbreviation) in SNORRE_COLUMNS.items():
            for column, term_type, status in ((main, "term", "preferred"), (synonym, "term", "admitted"),
                                              (abbreviation, "abbreviation", "unknown")):
                text = (row.get(column) or "").strip()
                if text:
                    db.execute(
                        "INSERT INTO term (entry_id, language, text, normalized, term_type, status)"
                        " VALUES (?,?,?,?,?,?)",
                        (entry, language, text, normalize(text), term_type, status))


LISA = ROOT / "published" / "lisa" / "lisa_terms.csv"


def load_lisa(db):
    """Load the LÍSA Icelandic-English pairs as one entry per headword.

    The pairs are not in the public repository until LÍSA confirms the licence
    (published/lisa/README.md); without the file the build goes on without LÍSA.
    """
    if not LISA.exists():
        print("LÍSA term pairs not found; building without LÍSA (see published/lisa/README.md)")
        return
    db.execute("INSERT INTO source VALUES (?,?,?,?,?)", (
        "lisa-glossary", "Orðalisti LÍSU, Orðanefnd LÍSU",
        "https://landupplysingar.is/index.php/ordalistar/", "No licence stated; terms only", "2026-11-10"))
    entries = {}
    for row in read(LISA):
        if row["entry"] not in entries:
            entries[row["entry"]] = db.execute(
                "INSERT INTO entry (source_id, source_key) VALUES ('lisa-glossary', ?)", (row["entry"],)).lastrowid
            db.execute("INSERT INTO term (entry_id, language, text, normalized, status) VALUES (?,?,?,?,?)",
                       (entries[row["entry"]], "en", row["english"], normalize(row["english"]), "preferred"))
        db.execute("INSERT INTO term (entry_id, language, text, normalized, status) VALUES (?,?,?,?,?)",
                   (entries[row["entry"]], "is", row["term"], normalize(row["term"]), row["status"]))


GEONORGE_CODELISTS = ROOT / "published" / "geonorge-metadata-codelists" / "geonorge_codelists.csv"
GEONORGE_RESOURCES = ROOT / "published" / "geonorge-resources"


def load_geonorge_codelists(db):
    """Load Geonorge metadata code list values: one entry per value, nb and en names."""
    db.execute("INSERT INTO source VALUES (?,?,?,?,?)", (
        "geonorge-metadata-codelists", "Geonorge metadata code lists, Kartverket",
        "https://register.geonorge.no/metadata-kodelister",
        "No licence stated; names and codes only", "2026-11-12"))
    seen = set()
    for row in read(GEONORGE_CODELISTS):
        if not row["nb"] or not row["en"] or row["nb"] == row["en"] or row["id"] in seen:
            continue
        seen.add(row["id"])
        entry = db.execute("INSERT INTO entry (source_id, source_key, subject) VALUES (?,?,?)",
                           ("geonorge-metadata-codelists", row["id"], row["code_list"])).lastrowid
        for language in ("nb", "en"):
            db.execute("INSERT INTO term (entry_id, language, text, normalized, status) VALUES (?,?,?,?,?)",
                       (entry, language, row[language], normalize(row[language]), "preferred"))


def load_geonorge_resources(db):
    """Load Geonorge interface strings as GUI labels, English source and Bokmål translation."""
    commits = dict(line.split("\t")[:2] for line in
                   (GEONORGE_RESOURCES / "commits.txt").read_text(encoding="utf8").splitlines())
    with lzma.open(GEONORGE_RESOURCES / "geonorge_resources.csv.xz", "rt", encoding="utf8", newline="") as f:
        db.executemany(
            "INSERT OR IGNORE INTO gui_label (application, version, context, source_text, language,"
            " translation, source_normalized, translation_normalized) VALUES (?,?,?,?,?,?,?,?)",
            (("geonorge", commits[r["repository"]], f'{r["repository"]}/{r["file"]}#{r["key"]}',
              r["en"], "nb", r["nb"], normalize_label(r["en"]), normalize_label(r["nb"]))
             for r in csv.DictReader(f)))


ARNASTOFNUN = ROOT / "published" / "arnastofnun-dictionaries" / "dictionaries.tsv.xz"
ARNASTOFNUN_SOURCES = {
    "islex": ("arnastofnun-islex", "ISLEX Icelandic-Scandinavian dictionary (2026-02), Árni Magnússon Institute",
              "http://hdl.handle.net/20.500.12537/376"),
    "french": ("arnastofnun-french", "Icelandic-French dictionary (Lexía), Árni Magnússon Institute",
               "http://hdl.handle.net/20.500.12537/377"),
    "polish": ("arnastofnun-polish", "Icelandic-Polish dictionary, Árni Magnússon Institute",
               "http://hdl.handle.net/20.500.12537/378"),
}
NOTE = re.compile(r"[():;=<>]|^(d'|de |du |des |pour |en |sur |dans |o |w |na |z |do |dla )", re.I)


def arnastofnun_term(row):
    """A target text usable as a term: an Equivalent, or a short <text> without notes."""
    text = row["target"].strip()
    if row["form"] == "Equivalent":
        return text if len(text.split()) <= 6 and not re.search(r"[()<>:;=]", text) else None
    return text if text and len(text.split()) <= 4 and not NOTE.search(text) else None


def load_arnastofnun(db):
    """Load dictionary senses: one entry per (dictionary, entry id, sense path).

    Only Sense units are terms; phrases and example sentences stay in the published file for
    translation training. Returns {entry_id: (lemma, Icelandic gloss, senses of that headword)}.
    """
    senses = defaultdict(lambda: {"terms": defaultdict(list), "lemma": "", "gloss": ""})
    with lzma.open(ARNASTOFNUN, "rt", encoding="utf8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"):
            if row["unit_type"] != "Sense":
                continue
            term = arnastofnun_term(row)
            if not term:
                continue
            sense = senses[(row["dictionary"], row["entry"], row["unit"])]
            sense["lemma"], sense["gloss"], sense["pos"] = row["lemma"], row["icelandic"], row["pos"]
            if term not in sense["terms"][row["language"]]:
                sense["terms"][row["language"]].append((term, row["form"]))
    for source_id, name, address in ARNASTOFNUN_SOURCES.values():
        db.execute("INSERT INTO source VALUES (?,?,?,?,?)",
                   (source_id, name, address, "CC BY-SA 4.0; credit the Árni Magnússon Institute", "2026-11-12"))
    per_headword = defaultdict(int)  # senses per (dictionary, lemma): homographs are separate entries
    for (dictionary, _, _), sense in senses.items():
        per_headword[(dictionary, normalize(sense["lemma"]))] += 1
    loaded = {}
    for (dictionary, entry, unit), sense in senses.items():
        source_id = ARNASTOFNUN_SOURCES[dictionary][0]
        entry_id = db.execute("INSERT INTO entry (source_id, source_key, subject) VALUES (?,?,?)",
                              (source_id, f"{entry}/{unit}", sense["pos"])).lastrowid
        db.execute("INSERT INTO term (entry_id, language, text, normalized, status) VALUES (?,?,?,?,?)",
                   (entry_id, "is", sense["lemma"], normalize(sense["lemma"]), "preferred"))
        for language, terms in sense["terms"].items():
            for text, form in terms:
                db.execute("INSERT INTO term (entry_id, language, text, normalized, status) VALUES (?,?,?,?,?)",
                           (entry_id, language, text, normalize(text),
                            "preferred" if form == "Equivalent" else "unknown"))
        loaded[entry_id] = (normalize(sense["lemma"]), normalize(sense["gloss"]),
                            per_headword[(dictionary, normalize(sense["lemma"]))])
    return loaded


EN_IS_GLOSSARY = ROOT / "published" / "arnastofnun-en-is-glossary" / "en_is_glossary.tsv.xz"
MIN_SCORE = 0.05


def load_en_is_glossary(db):
    """Load the English-Icelandic glossary 21.09: one entry per English item.

    Its pairs were accepted when valid in any context, so one English word carries several
    senses (layer: lag, varphæna). Pairs scoring under MIN_SCORE English to Icelandic are left
    out; the best-scored Icelandic term is preferred, the others admitted.
    """
    db.execute("INSERT INTO source VALUES (?,?,?,?,?)", (
        "arnastofnun-en-is-glossary", "English-Icelandic/Icelandic-English glossary 21.09, Árni Magnússon Institute",
        "http://hdl.handle.net/20.500.12537/144", "CC BY 4.0; credit the authors and the Árni Magnússon Institute",
        "2026-11-12"))
    pairs = defaultdict(dict)
    with lzma.open(EN_IS_GLOSSARY, "rt", encoding="utf8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            english, icelandic = row["english"].strip(), row["icelandic"].strip()
            if not re.search(r"[^\W\d_]", english) or not re.search(r"[^\W\d_]", icelandic):
                continue
            score = float(row["score_en_is"] or 0)
            if score < MIN_SCORE:
                continue
            key = normalize(icelandic)
            items = pairs[english.lower()]
            if key not in items or score > items[key][1]:
                items[key] = (icelandic, score, english)
    for english_key, items in pairs.items():
        ranked = sorted(items.values(), key=lambda item: -item[1])
        english = ranked[0][2]
        entry = db.execute("INSERT INTO entry (source_id, source_key) VALUES (?,?)",
                           ("arnastofnun-en-is-glossary", english_key)).lastrowid
        db.execute("INSERT INTO term (entry_id, language, text, normalized, status) VALUES (?,?,?,?,?)",
                   (entry, "en", english, normalize(english), "preferred"))
        for rank, (icelandic, score, _) in enumerate(ranked):
            db.execute("INSERT INTO term (entry_id, language, text, normalized, status, reliability)"
                       " VALUES (?,?,?,?,?,?)",
                       (entry, "is", icelandic, normalize(icelandic), "preferred" if rank == 0 else "admitted",
                        round(score, 3)))


def link_icelandic_pivot(db, loaded):
    """Attach dictionary senses to concepts that hold the same Icelandic term from LÍSA.

    Only LÍSA terms are used as the pivot: the English-Icelandic glossary mixes senses under one
    English word, and its Icelandic would carry them into every Nordic language.

    A headword with one sense links directly. With several senses, only a sense whose Icelandic
    gloss is itself an Icelandic term of the concept links (kort, gloss landakort); otherwise
    nothing links, since homonyms bring in unrelated words (lag: layer, song, manner). A concept
    that still receives several senses of one dictionary is marked ambiguous.
    """
    icelandic = defaultdict(set)
    for concept_id, normalized in db.execute(
            "SELECT ce.concept_id, t.normalized FROM concept_entry ce JOIN term t ON t.entry_id = ce.entry_id"
            " JOIN entry e ON e.id = ce.entry_id WHERE t.language = 'is' AND e.source_id = 'lisa-glossary'"):
        icelandic[normalized].add(concept_id)
    concept_terms = defaultdict(set)
    for normalized, concepts in icelandic.items():
        for concept_id in concepts:
            concept_terms[concept_id].add(normalized)
    by_headword = defaultdict(list)
    for entry_id, (lemma, gloss, count) in loaded.items():
        by_headword[lemma].append((entry_id, gloss, count))
    links, ambiguous = [], set()
    for lemma, entries in by_headword.items():
        for concept_id in icelandic.get(lemma, ()):
            terms = concept_terms[concept_id]
            if all(count == 1 for _, _, count in entries):
                chosen = entries
            else:
                chosen = [e for e in entries if e[2] == 1 or any(g.strip() in terms for g in e[1].split("|"))]
            links += [(concept_id, entry_id) for entry_id, _, _ in chosen]
    db.executemany("INSERT INTO concept_entry (concept_id, entry_id, method) VALUES (?,?,'icelandic-pivot')",
                   links)
    per_source = defaultdict(int)
    sources = dict(db.execute("SELECT id, source_id FROM entry WHERE source_id LIKE 'arnastofnun-%'"))
    for concept_id, entry_id in set(links):
        per_source[(concept_id, sources[entry_id])] += 1
    ambiguous |= {c for (c, _), n in per_source.items() if n > 1}
    db.executemany("UPDATE concept SET ambiguous = 1 WHERE id = ?", [(c,) for c in ambiguous])
    return len(links), len({c for c, _ in links}), len(ambiguous)


def read(path):
    with open(path, encoding="utf8", newline="") as stream:
        return list(csv.DictReader(stream))


def mlgt_status(row):
    if row["entry_status"] == "superseded":
        return "superseded"
    return "preferred" if row["normative_status"] == "preferred" else "unknown"


def load(db, source_id, name, address, licence, retrieved, rows, key, subject, status, reliability):
    db.execute("INSERT INTO source VALUES (?,?,?,?,?)",
               (source_id, name, address, licence, retrieved))
    entries = {}
    for row in rows:
        source_key = row[key]
        if source_key not in entries:
            entries[source_key] = db.execute(
                "INSERT INTO entry (source_id, source_key, subject) VALUES (?,?,?)",
                (source_id, source_key, row[subject]),
            ).lastrowid
        db.execute(
            "INSERT INTO term (entry_id, language, text, normalized, term_type, status, reliability)"
            " VALUES (?,?,?,?,?,?,?)",
            (entries[source_key], row["language"], row["term"], normalize(row["term"]),
             TERM_TYPES.get(row["term_type"], "term"), status(row),
             row[reliability] if reliability else None),
        )


ATTACH_ONLY = {"arnastofnun-en-is-glossary"}


def link_exact_english(db):
    """Group entries sharing a current English term, using union-find."""
    parent = {}

    def find(item):
        parent.setdefault(item, item)
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    labels = {}
    rows = db.execute(
        "SELECT entry_id, normalized, text FROM term WHERE language = 'en' AND term_type = 'term'"
        " AND status NOT IN ('deprecated', 'superseded') ORDER BY id"
    ).fetchall()
    by_term = defaultdict(list)
    for entry_id, normalized, text in rows:
        by_term[normalized].append(entry_id)
        labels.setdefault(entry_id, text)
    for entries in by_term.values():
        for other in entries[1:]:
            parent[find(entries[0])] = find(other)
        find(entries[0])

    groups = defaultdict(list)
    for entry_id in parent:
        groups[find(entry_id)].append(entry_id)
    sources = dict(db.execute("SELECT id, source_id FROM entry"))
    for members in groups.values():
        if all(sources[entry_id] in ATTACH_ONLY for entry_id in members):
            continue  # general vocabulary: joins concepts of other sources, never starts one
        counts = defaultdict(int)
        for entry_id in members:
            counts[sources[entry_id]] += 1
        ambiguous = int(any(count > 1 for count in counts.values()))
        concept = db.execute(
            "INSERT INTO concept (label, ambiguous) VALUES (?,?)",
            (labels[min(members)], ambiguous),
        ).lastrowid
        db.executemany(
            "INSERT INTO concept_entry (concept_id, entry_id, method) VALUES (?,?,'english-exact')",
            [(concept, entry_id) for entry_id in members],
        )


def main():
    DATABASE.parent.mkdir(exist_ok=True)
    DATABASE.unlink(missing_ok=True)
    db = sqlite3.connect(DATABASE)
    db.executescript(SCHEMA.read_text(encoding="utf8"))

    rows = read(MLGT)
    load(db, "iso-tc-211-mlgt-geolexica", rows[0]["source"], rows[0]["source_address"],
         rows[0]["source_licence"], rows[0]["retrieved"], rows,
         "concept_id", "iso_reference", mlgt_status, None)
    rows = read(IATE)
    load(db, "iate", rows[0]["source"], rows[0]["source_address"],
         "Download file: not copyright protected, per IATE legal notice", rows[0]["retrieved"],
         rows, "concept_id", "subject_fields",
         lambda row: IATE_STATUS.get(row["evaluation"], "unknown"), "reliability_code")

    load_snorre(db)
    load_lisa(db)
    load_geonorge_codelists(db)
    load_en_is_glossary(db)
    link_exact_english(db)
    loaded = load_arnastofnun(db)
    print("icelandic pivot: links, concepts, ambiguous", link_icelandic_pivot(db, loaded))
    load_gui_labels(db)
    load_geonorge_resources(db)
    db.commit()

    print("entries", db.execute("SELECT COUNT(*) FROM entry").fetchone()[0])
    print("terms", db.execute("SELECT COUNT(*) FROM term").fetchone()[0])
    print("concepts", db.execute("SELECT COUNT(*) FROM concept").fetchone()[0])
    print("gui labels", db.execute("SELECT COUNT(*) FROM gui_label").fetchone()[0])
    print("ambiguous", db.execute("SELECT COUNT(*) FROM concept WHERE ambiguous = 1").fetchone()[0])
    print("multi-source", db.execute(
        "SELECT COUNT(*) FROM (SELECT ce.concept_id FROM concept_entry ce JOIN entry e ON e.id = ce.entry_id"
        " GROUP BY ce.concept_id HAVING COUNT(DISTINCT e.source_id) > 1)").fetchone()[0])
    for language, count in db.execute(
        "SELECT language, COUNT(DISTINCT concept_id) FROM candidate_term GROUP BY language ORDER BY 2 DESC"
    ):
        print(language, count)


if __name__ == "__main__":
    main()
