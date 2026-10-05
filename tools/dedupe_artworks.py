#!/usr/bin/env python3
"""Collapse duplicate prints of the same artwork in index.html's card list.

Prints count as the same artwork when they are in the same game (TCG or
Pocket) and have the same card name: mirror foils, deck reprints and later
re-releases. The oldest regular print is kept. The others are listed on it as
"reprints" (shown in the card details), and their ids become aliases so owned
marks carry over to the kept card.

TCG and Pocket cards stay separate, since they are different products.

Usage: python3 tools/dedupe_artworks.py index.html
"""
import json
import re
import sys
from pathlib import Path

BLOCK = re.compile(r'(<script id="card-data">\n.*?\] = )(.*?)(;\n</script>)', re.S)


def label(card, group):
    """'Terastal Festival ex 087/187 (Poké Ball Mirror)' for a mirror, else 'Set 001/100'."""
    if "Mirror" in card["set"] and "·" not in card["set"]:
        base = next((g for g in group if g["number"] == card["number"] and "Mirror" not in g["set"]), None)
        if base:
            return f"{base['set']} {card['number']} ({card['set']})"
    return f"{card['set']} {card['number']}"


def main():
    page_path = Path(sys.argv[1])
    page = page_path.read_text(encoding="utf-8")
    m = BLOCK.search(page)
    if not m:
        sys.exit("No card-data block found in " + str(page_path))
    payload = json.loads(m.group(2))
    cards = payload["cards"]

    groups = {}
    for c in cards:
        groups.setdefault((c["game"], c["name"].strip().lower()), []).append(c)

    kept = []
    for c in cards:  # keep the site's order, using each group's kept card
        group = groups[(c["game"], c["name"].strip().lower())]
        regular = [g for g in group if "Mirror" not in g["set"]] or group
        keep = regular[-1]  # the site lists newest first, so the last is the original
        if c is not keep:
            continue
        others = [g for g in group if g is not keep]
        if others:
            keep["aliases"] = sorted(set(keep.get("aliases", []))
                                     | {o["id"] for o in others}
                                     | {a for o in others for a in o.get("aliases", [])})
            keep["reprints"] = keep.get("reprints", []) + [label(o, group) for o in others]
            keep["images"] = list(dict.fromkeys(keep["images"] + [u for o in others for u in o["images"]]))
        kept.append(keep)

    payload["cards"] = kept
    data = json.dumps(payload, ensure_ascii=False, indent=1).replace("</script", "<\\/script")
    page_path.write_text(page[:m.start(2)] + data + page[m.end(2):], encoding="utf-8")
    print(f"{len(cards)} prints -> {len(kept)} artworks ({len(cards) - len(kept)} duplicates merged)")
    for k in kept:
        if k.get("reprints"):
            print(f"  {k['name']} ({k['set']} {k['number']}) also: {'; '.join(k['reprints'])}")


if __name__ == "__main__":
    main()
