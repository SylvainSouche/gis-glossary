"""Compare the EU-directive parallel test with and without the INSPIRE regulation names.

    python3 compare_parallel.py parallel_with.json parallel_without.json > parallel.md
"""
import json
import sys

with_inspire, without = (json.load(open(p, encoding="utf8")) for p in sys.argv[1:3])
print("EU directives (Water Framework, Floods, Marine Strategy): start of an English paragraph as the "
      "query, the same paragraph in the target language as the answer; R@10. Independent of INSPIRE.\n")
print("| Language | potion | hybrid without INSPIRE names | hybrid with | Change | BGE-M3 | Ratio with |")
print("|---|---:|---:|---:|---:|---:|---:|")
for language in sorted(with_inspire):
    w, o = with_inspire[language], without.get(language, {})
    change = w["hybrid"] - o.get("hybrid", float("nan"))
    print(f"| {language} | {w['potion']:.2f} | {o.get('hybrid', float('nan')):.2f} | {w['hybrid']:.2f} | "
          f"{change:+.2f} | {w['bge-m3']:.2f} | {w['hybrid'] / max(w['bge-m3'], 1e-9):.2f} |")
