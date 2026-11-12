"""extract_arnastofnun.py - flatten the Árni Magnússon dictionaries (LMF-style XML from CLARIN-IS) to one row per translation.

Output dictionaries.tsv.xz, columns:
  dictionary, entry, unit, unit_type, pos, subject, lemma, icelandic, language, target, form
- entry: the institute's entry id, shared by the three dictionaries (islex_2212 = 2212)
- unit: path of the sense inside the entry (1, 1.2, 2.c1 ...); unit_type: Sense,
  SemanticCollocation, VerbPhrase, SemanticIdiomaticity, SenseExample
- icelandic: the Icelandic text of the unit (sense gloss or phrase), ' | '-joined
- form: Equivalent (writtenForm) or text (a <text> element in the target language)
"""
import collections, csv, lzma, tarfile, xml.etree.ElementTree as ET

LANG = {"dan": "da", "nob": "nb", "nno": "nn", "swe": "sv", "fao": "fo", "fin": "fi",
        "fra": "fr", "pol": "pl", "isl": "is"}
UNITS = {"Sense", "SemanticCollocation", "VerbPhrase", "SemanticIdiomaticity", "SenseExample"}
BASE = "https://repository.clarin.is/repository/xmlui/bitstream/handle/20.500.12537/"
DOWNLOADS = {"islex": "376/ISLEX_2026-02.tar.gz?sequence=1&isAllowed=y",
             "french": "377/franska_2026-02.tar.gz?sequence=5&isAllowed=y",
             "polish": "378/polska_2026-02.tar.gz?sequence=2&isAllowed=y"}
FILES = {name: f"{name}.tar.gz" for name in DOWNLOADS}
import os, urllib.request
for name, path in DOWNLOADS.items():
    if not os.path.exists(FILES[name]):
        request = urllib.request.Request(BASE + path, headers={"User-Agent": "gis-glossary/0.1 (terminology research)"})
        open(FILES[name], "wb").write(urllib.request.urlopen(request, timeout=300).read())
stats = collections.Counter()
subjects = collections.Counter()

def feats(el):
    return {f.get("att"): f.get("val") for f in el.findall("feat")}

def walk(el, path, kind, ctx, out):
    f = feats(el)
    subject = f.get("subjectField") or ctx["subject"]
    if subject and kind == "Sense":
        subjects[subject] += 1
    icelandic = [t.text.strip() for t in el.findall("text") if t.get("language") == "isl" and t.text]
    for eq in el.findall("Equivalent"):
        lang = LANG.get(eq.get("language"), eq.get("language"))
        if eq.get("writtenForm"):
            out.append((ctx["dict"], ctx["entry"], path, kind, ctx["pos"], subject or "", ctx["lemma"],
                        " | ".join(icelandic), lang, eq.get("writtenForm").strip(), "Equivalent"))
    for t in el.findall("text"):
        lang = LANG.get(t.get("language"), t.get("language"))
        if lang != "is" and t.text and t.text.strip():
            out.append((ctx["dict"], ctx["entry"], path, kind, ctx["pos"], subject or "", ctx["lemma"],
                        " | ".join(icelandic), lang, t.text.strip(), "text"))
    n = collections.Counter()
    for child in el:
        if child.tag in UNITS:
            n[child.tag] += 1
            tag = "" if child.tag == "Sense" else {"SemanticCollocation": "c", "VerbPhrase": "v",
                                                   "SemanticIdiomaticity": "i", "SenseExample": "e"}[child.tag]
            walk(child, f"{path}.{tag}{n[child.tag]}" if path else f"{tag}{n[child.tag]}",
                 child.tag, {**ctx, "subject": subject}, out)

with lzma.open("dictionaries.tsv.xz", "wt", encoding="utf8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar="\\")
    w.writerow(["dictionary", "entry", "unit", "unit_type", "pos", "subject", "lemma", "icelandic",
                "language", "target", "form"])
    for name, archive in FILES.items():
        with tarfile.open(archive) as tar:
            member = next(m for m in tar.getmembers() if m.name.endswith(".xml"))
            for _, el in ET.iterparse(tar.extractfile(member)):
                if el.tag != "LexicalEntry":
                    continue
                f0 = feats(el)
                lemma = el.find("Lemma")
                ctx = {"dict": name, "entry": el.get("id").replace("islex_", ""), "pos": f0.get("partOfSpeech", ""),
                       "lemma": feats(lemma).get("writtenForm", "") if lemma is not None else "",
                       "subject": f0.get("subjectField")}
                rows = []
                n = 0
                for child in el:
                    if child.tag in UNITS:
                        n += 1
                        walk(child, str(n), child.tag, ctx, rows)
                for r in rows:
                    w.writerow([x.replace("\t", " ").replace("\n", " ") for x in r])
                    stats[(name, r[3], r[8])] += 1
                stats[(name, "entries", "")] += 1
                el.clear()
for k, v in sorted(stats.items()):
    print("\t".join(k), v)
print("subject fields:", subjects.most_common(80))
