#!/usr/bin/env python3
"""Add fallback images to a card list built by tools/build_artofpkm.py.

artofpkm's scans stay first. After them, each card gets the TCGdex image of
the same Japanese (or Pocket) print, then English prints of the same Pokémon
from pokemontcg.io / TCGdex, so a card still shows art if artofpkm's CDN
is unreachable. Ids used by the older English list are added as aliases.

Usage:
  curl -sL https://www.artofpkm.com/illustrators/shinji-kanda/cards -o page.html
  git clone --depth 1 https://github.com/tcgdex/cards-database.git
  git clone --depth 1 https://github.com/PokemonTCG/pokemon-tcg-data.git
  python3 tools/add_fallback_images.py cards.js page.html cards-database pokemon-tcg-data > cards.full.js
  python3 tools/inline_data.py cards.full.js index.html
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_cards import num_key, ptcg_cards, tcgdex_cards  # noqa: E402

# Pocket expansions use set names that never appear in the Japanese TCG.
POCKET_SETS = {
    "Genetic Apex", "Mythical Island", "Space-Time Smackdown", "Triumphant Light",
    "Shining Revelry", "Celestial Guardians", "Extradimensional Crisis", "Eevee Grove",
    "Wisdom of Sea and Sky", "Secluded Springs", "Mega Rising", "Crimson Blaze",
    "Fantastical Parade", "Paldean Wonders", "Pulsing Aura", "Ruler of the Skies",
    "Team Rocket’s Ambition", "Team Rocket's Ambition",
}


def parse_page(text):
    cards = []
    for m in re.finditer(r'<a data-action="click-&gt;lightbox#open"(.*?)</a>', text, re.S):
        a = m.group(1)

        def get(pattern):
            r = re.search(pattern, a, re.S)
            return html.unescape(r.group(1)).strip() if r else ""

        url = get(r'data-lightbox-url="([^"]+)"')
        set_id, card_no = re.search(r"/sets/(\d+)/card/(\d+)", url).groups()
        title = get(r'data-lightbox-title="([^"]+)"')
        name = get(r'card-title[^>]*>([^<]+)<')
        subs = [html.unescape(x).strip() for x in re.findall(r'card-subtitle[^>]*>([^<]*)<', a)]
        set_name = title[len(name) + 2:] if title.startswith(name + ", ") else (subs[1] if len(subs) > 1 else "")
        cards.append({
            "id": f"aop-{set_id}-{card_no}",
            "name": name,
            "ja": get(r'font-ja[^>]*>([^<]*)<'),
            "set": set_name,
            "number": subs[0] if subs else "",
            "game": "Pocket" if set_name in POCKET_SETS else "TCG",
            "images": [get(r'<img[^>]*src="([^"]+)"'), get(r'data-lightbox-src="([^"]+)"')],
            "large": get(r'data-lightbox-src="([^"]+)"'),
        })
    return cards


def norm(s):
    return re.sub(r"\s+", "", s or "")


def load_payload(path):
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text.split("] = ", 1)[1].strip().rstrip(";"))


def main():
    cards_js, page, tcgdex_root, ptcg_root = (Path(a) for a in sys.argv[1:5])
    payload = load_payload(cards_js)
    artist = payload["artist"]
    page_cards = {c["id"].split("-", 1)[1]: c for c in parse_page(page.read_text(encoding="utf-8"))}
    cards = []
    for existing in payload["cards"]:
        key = existing["id"].split("-", 1)[1]           # "592-34" from "apkm-592-34"
        c = dict(page_cards.get(key, {}), **{k: v for k, v in existing.items() if k != "images"})
        c["images"] = existing.get("images", [])
        c.setdefault("ja", "")
        cards.append(c)

    dex_cards = tcgdex_cards(tcgdex_root, artist)
    ptcg = ptcg_cards(ptcg_root, artist, {})

    ja_prints = [c for c in dex_cards if c["region"] == "ja"]
    pocket_prints = [c for c in dex_cards if c["region"] == "intl" and c["pocket"]]
    en_prints = [c for c in dex_cards if c["region"] == "intl" and not c["pocket"]]

    def tcgdex_imgs(c):
        return [c["img"] + "/high.webp", c["img"] + "/high.png"]

    # English images of each Pokémon, the last-resort fallback (same artwork, English text).
    en_imgs = {}
    for p in ptcg:
        en_imgs.setdefault(p["name"], []).extend(p["images"])
    for c in en_prints:
        en_imgs.setdefault(c["name"], []).extend(tcgdex_imgs(c))

    for card in cards:
        num = num_key(card["number"].split("/")[0])
        extra, rarity = [], ""
        if card["game"] == "Pocket":
            match = [c for c in pocket_prints if c["name"] == card["name"] and num_key(c["localId"]) == num]
        else:
            match = [c for c in ja_prints if norm(c["name"]) == norm(card["ja"]) and num_key(c["localId"]) == num]
            extra = en_imgs.get(card["name"], [])
        for c in match:
            extra = tcgdex_imgs(c) + extra
            rarity = rarity or (c["rarity"] if c["rarity"] != "None" else "")
        card["rarity"] = card.get("rarity") or rarity
        card["images"] = list(dict.fromkeys(u for u in card["images"] + extra if u))

    # Aliases: map every id the older English list used to the first Japanese
    # print of the same card, so marks made before this list carry over.
    def first_print(name, pocket, set_hint=None):
        pool = [c for c in cards if c["name"] == name and (c["game"] == "Pocket") == pocket and "Mirror" not in c["set"]]
        if set_hint:
            pool = [c for c in pool if set_hint(c)] or pool
        return pool[-1] if pool else None  # the page lists newest first

    for p in ptcg:
        hint = (lambda c: "30th" in c["set"]) if p["setName"].startswith("30th") else (lambda c: "30th" not in c["set"])
        target = first_print(p["name"], False, hint)
        if target:
            target.setdefault("aliases", []).append(p["id"])
    for c in en_prints:
        hint = (lambda x: "30th" in x["set"]) if c["set"]["id"].startswith("30th") else (lambda x: "30th" not in x["set"])
        target = first_print(c["name"], False, hint)
        if target:
            target.setdefault("aliases", []).append(f"{c['set']['id']}-{c['localId']}")
    for c in pocket_prints:
        target = next((x for x in cards if x["game"] == "Pocket" and x["name"] == c["name"]
                       and num_key(x["number"].split("/")[0]) == num_key(c["localId"])), None)
        if target:
            target.setdefault("aliases", []).append(f"{c['set']['id']}-{c['localId']}")
    for c in cards:
        if "aliases" in c:
            c["aliases"] = sorted(set(c["aliases"]))
        for key in ("large", "ja"):
            c.pop(key, None)

    payload["cards"] = cards
    print("// Generated by tools/build_artofpkm.py + tools/add_fallback_images.py. Do not edit by hand.")
    print("window.BINDER_DATA = window.BINDER_DATA || {};")
    print(f"window.BINDER_DATA[{json.dumps(artist.lower())}] = "
          + json.dumps(payload, ensure_ascii=False, indent=1) + ";")


if __name__ == "__main__":
    main()
