"""Acceptance test: can an English search find records written in other languages?

Methods per language:
- potion: static model only, what the plugin can run;
- potion + concepts: plus glossary concept vectors at weight 0.3;
- hybrid: potion + concepts plus a keyword boost, as in Semantic Plugin Search, where the
  English query is translated term by term through the glossary into the record's language;
- bge-m3: the reference the plugin cannot run.

Verdict (dec-acceptance-two-verdicts): usable when R@10 >= 0.70 and the ratio to BGE-M3 >= 0.85,
otherwise not usable.

Data: Geonorge datasets (English title against Norwegian title and abstract), LMI records in
Icelandic, and INSPIRE feature concepts in the EU languages (corpus.tsv) as a worst case.
Keyword fields of the records are never used, because they define the theme test's answers.

Parallel mode (MODE=parallel): instead of the records above, aligned paragraphs from EU
directives (PARALLEL, built by tools/build_parallel_corpus.py): the start of the English paragraph
is the query, the whole paragraph in the target language is the record. It is independent of
INSPIRE, so running it with lexicons with and without the INSPIRE regulation names measures what
those names bring. LEXICON and OUTPUT choose the lexicon file and the report name.
"""
import collections
import csv
import json
import lzma
import os
import random
import re
import time
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from model2vec import StaticModel
from sentence_transformers import SentenceTransformer

START = time.time()
UA = {"User-Agent": "gis-glossary/0.1 (search acceptance test)"}
WEIGHT = 0.3
TITLE_WEIGHT, BODY_WEIGHT = 0.20, 0.05
FETCH_BUDGET = 600
random.seed(5)
MODE = os.environ.get("MODE", "full")
LEXICON = os.environ.get("LEXICON", "lexicon.tsv.xz")
OUTPUT = os.environ.get("OUTPUT", "acceptance.md")
PARALLEL = os.environ.get("PARALLEL", "parallel_eu.tsv.xz")


def log(*a):
    print(f"[{time.time() - START:6.0f}s]", *a, flush=True)


def get(url, body=None, headers=None, tries=2, timeout=30):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def words(text):
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.findall(r"\w+", text.lower())


def unit(m):
    return m / np.maximum(np.linalg.norm(m, axis=-1, keepdims=True), 1e-9)


def norwegian_standard(text):
    w = words(text)
    nn = sum(x in {"ikkje", "eit", "dei", "vert", "berre", "korleis", "kva", "noko", "kvar"} for x in w)
    nb = sum(x in {"ikke", "et", "de", "blir", "bare", "hvordan", "hva", "noe"} for x in w)
    return "nn" if nn > nb else "nb"


# Records: language -> list of (english query, title, body).
records = collections.defaultdict(list)

icelandic, themes = [], collections.defaultdict(set)
if MODE == "parallel":
    with lzma.open(PARALLEL, "rt", encoding="utf8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"):
            records[r["language"]].append((r["query_en"], "", r["document"]))
    log("parallel paragraphs", {k: len(v) for k, v in records.items()})
else:
    # Norwegian records, fetched in parallel within a time budget.
    offset, uuids = 0, []
    while len(uuids) < 1600:
        page = get(f"https://kartkatalog.geonorge.no/api/search?limit=400&offset={offset}"
                   "&facets%5B0%5D.name=type&facets%5B0%5D.value=dataset", tries=3, timeout=60)
        if not page or not page.get("Results"):
            break
        uuids += [r["Uuid"] for r in page["Results"]]
        offset += 400
    random.shuffle(uuids)
    log("Geonorge uuids", len(uuids))
    outcome = collections.Counter()


    def fetch(uuid):
        if time.time() - START > FETCH_BUDGET:
            return "skipped", None
        d = get(f"https://kartkatalog.geonorge.no/api/getdata/{uuid}")
        return ("failed", None) if d is None else ("fetched", d)


    with ThreadPoolExecutor(8) as pool:
        for state, d in pool.map(fetch, uuids):
            outcome[state] += 1
            if d is None:
                continue
            title, abstract = (d.get("Title") or "").strip(), (d.get("Abstract") or "").strip()
            english = (d.get("EnglishTitle") or "").strip()
            if not english or english.lower() == title.lower():
                outcome["no English title"] += 1
                continue
            if len(abstract) < 40 or (d.get("EnglishAbstract") or "").strip()[:60] == abstract[:60]:
                outcome["no Norwegian abstract"] += 1
                continue
            records[norwegian_standard(abstract)].append((english, title, abstract))
    log("Geonorge", dict(outcome), {k: len(v) for k, v in records.items()})

    # Icelandic records.
    lmi = get("https://gatt.lmi.is/geonetwork/srv/api/search/records/_search?bucket=s101",
              {"size": 1000, "query": {"term": {"mainLanguage": "ice"}},
               "_source": ["resourceTitleObject", "resourceAbstractObject", "allKeywords"]},
              {"Accept": "application/json", "Content-Type": "application/json"}, tries=3, timeout=60)
    icelandic, themes = [], collections.defaultdict(set)
    for hit in (lmi or {}).get("hits", {}).get("hits", []):
        s = hit["_source"]
        t, a = s.get("resourceTitleObject") or {}, s.get("resourceAbstractObject") or {}
        title = (t.get("langice") or t.get("default") or "").strip()
        i = len(icelandic)
        icelandic.append((t.get("langeng"), title, (a.get("langice") or a.get("default") or "").strip()))
        for name, thesaurus in (s.get("allKeywords") or {}).items():
            if "inspireeceuropaeutheme" in name:
                for k in thesaurus.get("keywords", []):
                    if k.get("langeng"):
                        themes[k["langeng"]].add(i)
    records["is"] = [r for r in icelandic if r[0] and r[0].strip().lower() != r[1].lower()]
    log("LMI records", len(icelandic), "with English title", len(records["is"]),
        "themes", {k: len(v) for k, v in themes.items()})

    with open("corpus.tsv", encoding="utf8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            records[r["language"]].append((r["query_en"], "", r["document"]))

    with open("records.json", "w", encoding="utf8") as f:
        json.dump({"records": {k: v for k, v in records.items() if k in ("nb", "nn", "is")},
                   "icelandic": icelandic, "themes": {k: sorted(v) for k, v in themes.items()}},
                  f, ensure_ascii=False)


def text_of(record):
    return f"{record[1]}. {record[2]}" if record[1] else record[2]


# Glossary.
with lzma.open(LEXICON, "rt", encoding="utf8", newline="") as f:
    lexicon = [r for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
               if r.get("term") and r.get("language")]
# Keyword translation uses every concept; vector composition keeps to unambiguous ones.
lookup = collections.defaultdict(lambda: collections.defaultdict(set))
lookup_vector = collections.defaultdict(lambda: collections.defaultdict(set))
members = collections.defaultdict(set)
translations = collections.defaultdict(lambda: collections.defaultdict(set))
for r in lexicon:
    form = " ".join(words(r["term"]))
    if not form:
        continue
    lookup[r["language"]][form].add(r["key"])
    if r["ambiguous"] == "0":
        lookup_vector[r["language"]][form].add(r["key"])
    members[r["key"]].add(r["term"])
    translations[r["key"]][r["language"]].add(form)


def singular(word):
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def spans(text, language, longest=6, tokens=None, tables=None):
    """Longest glossary matches in text: list of (concept keys, matched words).

    English lookups also try the singular of the last word.
    """
    tokens, out, i = tokens if tokens is not None else words(text), [], 0
    table = (tables or lookup).get(language, {})
    while i < len(tokens):
        for size in range(min(longest, len(tokens) - i), 0, -1):
            chunk = tokens[i:i + size]
            hit = table.get(" ".join(chunk))
            if not hit and language == "en":
                hit = table.get(" ".join(chunk[:-1] + [singular(chunk[-1])]))
            if hit:
                out.append((hit, chunk))
                i += size
                break
        else:
            out.append((set(), tokens[i:i + 1]))
            i += 1
    return out


def found(text, language):
    return set().union(set(), *(keys for keys, _ in spans(text, language, tables=lookup_vector)))


texts = [(q, "en") for v in records.values() for q, _, _ in v] + [(t, "en") for t in themes]
texts += [(text_of(r), lang) for lang, v in records.items() for r in v]
texts += [(text_of(r), "is") for r in icelandic]
used = set().union(*(found(t, lang) for t, lang in texts))
log("concepts used", len(used))

# Keyword part.
STOP = set("the and for from with into onto that this these those are was were has have of in on "
           "to by at or as an a its data dataset map maps".split())


def stem(word):
    """A forgiving prefix for inflected and compound languages."""
    return word if len(word) <= 4 else word[:max(4, len(word) - 2)]


class KeywordIndex:
    def __init__(self, items):
        self.fields = []
        for weight, field in ((TITLE_WEIGHT, 1), (BODY_WEIGHT, 2)):
            postings = collections.defaultdict(set)
            for i, record in enumerate(items):
                for w in words(record[field]):
                    postings[w].add(i)
            self.fields.append((weight, postings, sorted(postings)))
        self.size, self.cache = len(items), {}

    def docs(self, field, word):
        key = (field, word)
        if key not in self.cache:
            _, postings, vocabulary = self.fields[field]
            s = stem(word)
            hits = set()
            for w in vocabulary:
                if w.startswith(s) or (len(s) >= 6 and s in w):
                    hits |= postings[w]
            self.cache[key] = hits
        return self.cache[key]

    def phrase(self, field, form):
        sets = [self.docs(field, w) for w in form.split() if w not in STOP]
        return set.intersection(*sets) if sets else set()

    def boosts(self, query, language):
        """Each query unit (a glossary concept, or a plain English word) shares the boost."""
        units = []

        def add(found_spans):
            for keys, matched in found_spans:
                forms = {f for k in keys for f in translations[k].get(language, ())}
                if forms:
                    units.append(forms | {" ".join(matched)})
                elif len(matched) > 1:
                    add(spans("", "en", len(matched) - 1, matched))
                else:
                    units.extend([{w} for w in matched if w not in STOP and len(w) >= 3])

        add(spans(query, "en"))
        boost = np.zeros(self.size, dtype=np.float32)
        for forms in units:
            for field, (weight, _, _) in enumerate(self.fields):
                hits = set().union(set(), *(self.phrase(field, f) for f in forms))
                if hits:
                    boost[list(hits)] += weight / len(units)
        return boost


# Models.
potion = StaticModel.from_pretrained("minishlab/potion-multilingual-128M")
bge = SentenceTransformer("BAAI/bge-m3", device="cpu")
bge.max_seq_length = 256
log("models loaded")
P = lambda x: unit(potion.encode(x, show_progress_bar=False))
B = lambda x: bge.encode(x, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
train = random.sample(sorted({r["term"] for r in lexicon if r["ambiguous"] == "0"}), 12000)
tb, tp = B(train), P(train)
W = np.linalg.solve(tb.T @ tb + np.eye(tb.shape[1]), tb.T @ tp)
needed = sorted({t for k in used for t in members[k]})
log("needed terms", len(needed))
vec = dict(zip(needed, B(needed) @ W)) if needed else {}
concept = {k: unit(np.mean([vec[t] for t in members[k]], axis=0)) for k in used}


def ensure(keys):
    """Compute concept vectors not built yet, in one batch."""
    missing = sorted(k for k in keys if k not in concept)
    terms = sorted({t for k in missing for t in members[k]} - set(vec))
    if terms:
        vec.update(zip(terms, B(terms) @ W))
    for k in missing:
        concept[k] = unit(np.mean([vec[t] for t in members[k]], axis=0))


def embed(items, language, method):
    if method == "bge-m3":
        return B(items)
    base = P(items)
    if method == "potion":
        return base
    ensure(set().union(*(found(t, language) for t in items)))
    out = []
    for t, b in zip(items, base):
        keys = found(t, language)
        out.append(unit(b + WEIGHT * unit(np.mean([concept[k] for k in keys], axis=0))) if keys else b)
    return np.array(out)


METHODS = ["potion", "potion + concepts", "hybrid", "bge-m3"]


def scores(queries, items, language):
    """Similarity matrices (queries x records) for every method."""
    docs = [text_of(r) for r in items]
    out = {m: embed(queries, "en", m) @ embed(docs, language, m).T
           for m in ("potion", "potion + concepts", "bge-m3")}
    index = KeywordIndex(items)
    out["hybrid"] = out["potion + concepts"] + np.stack([index.boosts(q, language) for q in queries])
    return out


def verdict(r10, ratio):
    return "usable" if r10 >= 0.70 and ratio >= 0.85 else "not usable"


SOURCE = {"nb": "Geonorge", "nn": "Geonorge", "is": "LMI, English title"} if MODE == "full" else {}
DEFAULT_SOURCE = "INSPIRE concepts" if MODE == "full" else "EU directives"
results = {}
lines = ["| Language | Data | n | potion | + concepts | hybrid | BGE-M3 | Ratio | Verdict |",
         "|---|---|---:|---:|---:|---:|---:|---:|---|"]
for language in sorted(records):
    items = records[language]
    if len(items) < 5:
        continue
    s = scores([q for q, _, _ in items], items, language)
    r10 = {}
    for m, matrix in s.items():
        ranks = (matrix > matrix.diagonal()[:, None]).sum(axis=1)
        r10[m] = (ranks < 10).mean()
    best = max(r10["potion + concepts"], r10["hybrid"])
    ratio = best / max(r10["bge-m3"], 1e-9)
    results[language] = {m: float(v) for m, v in r10.items()}
    lines.append(f"| {language} | {SOURCE.get(language, DEFAULT_SOURCE)} | {len(items)} | "
                 f"{r10['potion']:.2f} | {r10['potion + concepts']:.2f} | {r10['hybrid']:.2f} | "
                 f"{r10['bge-m3']:.2f} | {ratio:.2f} | {verdict(best, ratio)} |")
    log(lines[-1])

theme_names = [t for t, ix in themes.items() if len(ix) >= 2]
if theme_names and icelandic:
    lines += ["", "Icelandic theme search: share of the top 10 that are tagged with the theme.", "",
              "| Method | Precision@10 |", "|---|---:|"]
    s = scores(theme_names, icelandic, "is")
    for m in METHODS:
        top = np.argsort(-s[m], axis=1)[:, :10]
        p = np.mean([len(set(top[i]) & themes[t]) / min(10, len(themes[t]))
                     for i, t in enumerate(theme_names)])
        lines.append(f"| {m} | {p:.2f} |")
    lines.append(f"\nThemes: {', '.join(f'{t} ({len(themes[t])})' for t in theme_names)}")
if MODE == "full":
    # Norwegian theme search: English national theme name against all Geonorge datasets; the
    # answer key is the theme each publisher set (Geonorge metadata code list, nb and en names).
    english_theme = dict(line.split("\t") for line in open("themes_no.tsv", encoding="utf8").read().splitlines()[1:])
    catalogue, offset = [], 0
    while True:
        page = get(f"https://kartkatalog.geonorge.no/api/search?limit=500&offset={offset}"
                   "&facets%5B0%5D.name=type&facets%5B0%5D.value=dataset", tries=3, timeout=90)
        if not page or not page.get("Results"):
            break
        catalogue += [r for r in page["Results"] if r.get("Theme") in english_theme and len(r.get("Abstract") or "") >= 40]
        offset += 500
    items = [("", (r.get("Title") or "").strip(), (r.get("Abstract") or "").strip()) for r in catalogue]
    tagged = collections.defaultdict(set)
    for i, r in enumerate(catalogue):
        tagged[english_theme[r["Theme"]]].add(i)
    standard = collections.Counter(norwegian_standard(b) for _, _, b in items)
    log("Geonorge catalogue for themes", len(items), dict(standard))
    names = [t for t in tagged if len(tagged[t]) >= 5]
    if names:
        lines += ["", f"Norwegian theme search: English national theme name against {len(items)} Geonorge "
                  f"datasets ({dict(standard)}); share of the top 10 tagged with the theme.", "",
                  "| Method | Precision@10 | Ratio to BGE-M3 |", "|---|---:|---:|"]
        s_no = scores(names, items, "nb")
        precision = {}
        for m in METHODS:
            top = np.argsort(-s_no[m], axis=1)[:, :10]
            precision[m] = [len(set(top[i]) & tagged[t]) / min(10, len(tagged[t])) for i, t in enumerate(names)]
        for m in METHODS:
            mean = np.mean(precision[m])
            lines.append(f"| {m} | {mean:.2f} | {mean / max(np.mean(precision['bge-m3']), 1e-9):.2f} |")
        lines += ["", "| Theme | Datasets | potion | + concepts | hybrid | BGE-M3 |", "|---|---:|---:|---:|---:|---:|"]
        for i, t in enumerate(names):
            lines.append(f"| {t} | {len(tagged[t])} | " + " | ".join(f"{precision[m][i]:.1f}" for m in METHODS) + " |")
        log("Norwegian theme search done")
open(OUTPUT, "w", encoding="utf8").write("\n".join(lines) + "\n")
with open(OUTPUT.rsplit(".", 1)[0] + ".json", "w", encoding="utf8") as f:
    json.dump(results, f, indent=1)
print("\n".join(lines))
