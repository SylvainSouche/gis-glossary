"""Compare embedding models on the acceptance test data, outside the GitHub workflow.

    python compare_models.py RECORDS_JSON MODELS_JSON [OUTPUT_MD]

Same tasks and measures as acceptance.py, for models that cannot run on a GitHub runner (a
local fine-tune, distilled static models):
- known-item search, Bokmål and Icelandic: the English title against the title and abstract,
  using the records of an acceptance run (its records.json) so that every model sees the same
  records as that run's potion and hybrid scores;
- Norwegian theme search: the English national theme name against the Geonorge catalogue,
  share of the top 10 tagged with the theme (fetched live, as in acceptance.py);
- INSPIRE concepts (corpus.tsv) and EU directive paragraphs (parallel_eu.tsv.xz): R@10.

MODELS_JSON lists {"id", "model", "kind": "sentence-transformers" | "model2vec"}. Every
sentence-transformers model uses max_seq_length 256, as in acceptance.py.
"""
import collections
import csv
import json
import lzma
import sys
import time
import urllib.request

import numpy as np

HERE = __file__.rsplit("/", 1)[0] or "."
UA = {"User-Agent": "gis-glossary/0.1 (search acceptance test)"}
START = time.time()


def log(*a):
    print(f"[{time.time() - START:6.0f}s]", *a, flush=True)


def get(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.load(r)
        except Exception:
            time.sleep(3 * (attempt + 1))
    return None


def norwegian_standard(text):
    import re
    w = re.findall(r"\w+", text.lower())
    nn = sum(x in {"ikkje", "eit", "dei", "vert", "berre", "korleis", "kva", "noko", "kvar"} for x in w)
    nb = sum(x in {"ikke", "et", "de", "blir", "bare", "hvordan", "hva", "noe"} for x in w)
    return "nn" if nn > nb else "nb"


def load_encoder(spec):
    if spec.get("kind") == "model2vec":
        from model2vec import StaticModel
        model = StaticModel.from_pretrained(spec["model"])
        encode = lambda texts: model.encode(texts, show_progress_bar=False)
    else:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(spec["model"], device=spec.get("device"),
                                    trust_remote_code=spec.get("trust_remote_code", False))
        try:
            model.max_seq_length = 256
        except AttributeError:  # static embedding models have no sequence limit
            pass
        encode = lambda texts: model.encode(texts, batch_size=32, show_progress_bar=False)

    def unit_encode(texts):
        m = np.asarray(encode(list(texts)), dtype=np.float32)
        return m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-9)
    return unit_encode


def recall10(q, d):
    s = q @ d.T
    ranks = (s > s.diagonal()[:, None]).sum(axis=1)
    return float((ranks < 10).mean())


def main():
    records_path, models_path = sys.argv[1], sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else "compare_models.md"
    data = json.load(open(records_path, encoding="utf8"))
    known = {k: v for k, v in data["records"].items() if len(v) >= 5}
    inspire = collections.defaultdict(list)
    with open(f"{HERE}/corpus.tsv", encoding="utf8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            inspire[r["language"]].append((r["query_en"], r["document"]))
    parallel = collections.defaultdict(list)
    with lzma.open(f"{HERE}/parallel_eu.tsv.xz", "rt", encoding="utf8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"):
            parallel[r["language"]].append((r["query_en"], r["document"]))
    english_theme = dict(line.split("\t") for line in open(f"{HERE}/themes_no.tsv", encoding="utf8").read().splitlines()[1:])
    catalogue, offset = [], 0
    while True:
        page = get("https://kartkatalog.geonorge.no/api/search?limit=500&offset=" + str(offset)
                   + "&facets%5B0%5D.name=type&facets%5B0%5D.value=dataset")
        if not page or not page.get("Results"):
            break
        catalogue += [r for r in page["Results"] if r.get("Theme") in english_theme and len(r.get("Abstract") or "") >= 40]
        offset += 500
    tagged = collections.defaultdict(set)
    for i, r in enumerate(catalogue):
        tagged[english_theme[r["Theme"]]].add(i)
    themes = [t for t in tagged if len(tagged[t]) >= 5]
    catalogue_texts = [f"{(r.get('Title') or '').strip()}. {(r.get('Abstract') or '').strip()}" for r in catalogue]
    log("data", {k: len(v) for k, v in known.items()}, "catalogue", len(catalogue), "themes", len(themes))

    results = {}
    for spec in json.load(open(models_path, encoding="utf8")):
        log("model", spec["id"])
        encode = load_encoder(spec)
        res = {}
        for language, items in known.items():
            q = encode([r[0] for r in items])
            d = encode([f"{r[1]}. {r[2]}" if r[1] else r[2] for r in items])
            res[f"known {language}"] = recall10(q, d)
        if themes:
            q, d = encode(themes), encode(catalogue_texts)
            top = np.argsort(-(q @ d.T), axis=1)[:, :10]
            res["themes nb"] = float(np.mean([len(set(top[i]) & tagged[t]) / min(10, len(tagged[t]))
                                              for i, t in enumerate(themes)]))
        for name, corpus in (("INSPIRE", inspire), ("EU", parallel)):
            for language, items in sorted(corpus.items()):
                res[f"{name} {language}"] = recall10(encode([q for q, _ in items]), encode([d for _, d in items]))
        results[spec["id"]] = res
        log(spec["id"], {k: round(v, 2) for k, v in res.items()})
        json.dump(results, open(output.rsplit(".", 1)[0] + ".json", "w", encoding="utf8"), indent=1)

    ids = list(results)
    keys = list(next(iter(results.values())))
    lines = ["| Test | " + " | ".join(ids) + " |", "|---|" + "---:|" * len(ids)]
    for k in keys:
        lines.append(f"| {k} | " + " | ".join(f"{results[i].get(k, float('nan')):.2f}" for i in ids) + " |")
    open(output, "w", encoding="utf8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
