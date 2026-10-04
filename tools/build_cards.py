#!/usr/bin/env python3
"""Build cards.js (the bundled card list) for one illustrator.

Combines two open datasets so the binder doesn't depend on any single API:
  * TCGdex cards-database   https://github.com/tcgdex/cards-database
      international TCG, TCG Pocket and Japanese prints
  * PokemonTCG data         https://github.com/PokemonTCG/pokemon-tcg-data
      English TCG, including cards TCGdex has no illustrator for

Usage:
  git clone --depth 1 https://github.com/tcgdex/cards-database.git
  git clone --depth 1 https://github.com/PokemonTCG/pokemon-tcg-data.git
  python3 tools/build_cards.py cards-database pokemon-tcg-data "Shinji Kanda" > cards.js

Every card gets an ordered list of image URLs; the app tries them in turn,
so a card still shows art when one host lacks the image. Japanese prints of
the same artwork are used as a last image fallback.
"""
import json
import re
import sys
from pathlib import Path


def text_field(src, key):
    m = re.search(r"[\s{,]'?" + re.escape(key) + r"'?\s*:\s*['\"](.*?)['\"]", src)
    return m.group(1) if m else None


def block(src, key):
    m = re.search(r"\b" + key + r"\s*:\s*\{(.*?)\}", src, re.S)
    return m.group(1) if m else ""


def num_key(n):
    """'SWSH185' -> 185, '009' -> 9: lets prints match across datasets."""
    m = re.search(r"\d+", str(n))
    return int(m.group(0)) if m else -1


def read_set(set_file):
    src = set_file.read_text(encoding="utf-8")
    serie_file = set_file.parent.with_suffix(".ts")
    serie_src = serie_file.read_text(encoding="utf-8") if serie_file.exists() else ""
    # "id" is also the Indonesian key inside name blocks, so drop those before reading ids.
    strip_names = lambda t: re.sub(r"\bname\s*:\s*\{.*?\}", "", t, flags=re.S)
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", src.split("releaseDate", 1)[-1][:200]) if "releaseDate" in src else []
    names = block(src, "name")
    return {
        "id": text_field(strip_names(src), "id"),
        "serie": text_field(strip_names(serie_src), "id") or "",
        "en": text_field(names, "en"),
        "ja": text_field(names, "ja"),
        "date": min(dates) if dates else "",
    }


def tcgdex_cards(root, artist):
    out = []
    pattern = re.compile(r"illustrator\s*:\s*['\"]" + re.escape(artist) + r"['\"]", re.I)
    for region, sub in (("intl", "data"), ("ja", "data-asia")):
        for f in sorted((root / sub).rglob("*.ts")):
            src = f.read_text(encoding="utf-8")
            if not pattern.search(src):
                continue
            set_file = f.parent.with_suffix(".ts")
            if not set_file.exists():
                continue
            s = read_set(set_file)
            names = block(src, "name")
            name = text_field(names, "en") if region == "intl" else text_field(names, "ja")
            if not name:  # Asian-region prints other than Japanese (zh, th, id) are skipped
                continue
            dex = re.search(r"dexId\s*:\s*\[([\d,\s]+)\]", src)
            local_id = f.stem
            out.append({
                "region": region,
                "pocket": s["serie"] == "tcgp",
                "set": s,
                "localId": local_id,
                "name": name,
                "dex": [int(x) for x in re.findall(r"\d+", dex.group(1))] if dex else [],
                "rarity": text_field(src, "rarity") or "",
                "img": f"https://assets.tcgdex.net/{'en' if region == 'intl' else 'ja'}/{s['serie']}/{s['id']}/{local_id}",
            })
    return out


def ptcg_cards(root, artist, dex_names):
    """Returns this artist's English cards; fills dex_names {dex: English name} from every card."""
    sets = {s["id"]: s for s in json.loads((root / "sets" / "en.json").read_text(encoding="utf-8"))}
    out = []
    for f in sorted((root / "cards" / "en").glob("*.json")):
        s = sets.get(f.stem)
        if not s:
            continue
        for c in json.loads(f.read_text(encoding="utf-8")):
            dex = c.get("nationalPokedexNumbers") or []
            if len(dex) == 1 and c.get("supertype") == "Pokémon" and " " not in c["name"]:
                dex_names.setdefault(dex[0], c["name"])
            if (c.get("artist") or "").lower() != artist.lower():
                continue
            out.append({
                "id": c["id"], "name": c["name"], "number": c["number"], "rarity": c.get("rarity", ""),
                "setName": s["name"], "date": s["releaseDate"].replace("/", "-"),
                "dex": c.get("nationalPokedexNumbers", []),
                "images": [c["images"].get("large"), c["images"].get("small")],
            })
    return out


def main():
    tcgdex_root, ptcg_root, artist = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    dex_cards = tcgdex_cards(tcgdex_root, artist)
    dex_names = {}
    ptcg = ptcg_cards(ptcg_root, artist, dex_names)

    # Japanese prints, used as image fallbacks for the same Pokémon's English card.
    ja_by_dex = {}
    for c in dex_cards:
        if c["region"] == "ja":
            for d in c["dex"]:
                ja_by_dex.setdefault(d, []).append(c)

    def ja_images(dex):
        imgs = []
        for d in dex:
            for j in ja_by_dex.get(d, []):
                imgs += [j["img"] + "/high.webp", j["img"] + "/high.png"]
        return imgs

    cards = {}
    ptcg_by_key = {(p["setName"].lower(), num_key(p["number"])): p for p in ptcg}
    # Fallback match for sets the two datasets name or number differently:
    # same release date and same Pokémon means the same print.
    ptcg_by_date = {}
    for p in ptcg:
        for d in p["dex"]:
            ptcg_by_date.setdefault((p["date"], d), []).append(p)
    used_ptcg = set()

    for c in dex_cards:
        if c["region"] != "intl":
            continue
        s = c["set"]
        key = ((s["en"] or "").lower(), num_key(c["localId"]))
        p = ptcg_by_key.get(key)
        if not p and not c["pocket"]:
            same = [q for d in c["dex"] for q in ptcg_by_date.get((s["date"], d), []) if q["id"] not in used_ptcg]
            p = same[0] if len(same) == 1 else None
        if p:
            used_ptcg.add(p["id"])
        imgs = (p["images"] if p else []) + [c["img"] + "/high.webp", c["img"] + "/high.png"]
        tcgdex_id = f"{s['id']}-{c['localId']}"
        cid = p["id"] if p else tcgdex_id
        cards[cid] = {
            "id": cid,
            # Older app versions stored TCGdex ids; the app migrates owned marks from these.
            "aliases": [tcgdex_id] if tcgdex_id != cid else [], "name": c["name"], "set": s["en"] or s["id"],
            "number": p["number"] if p else c["localId"],
            "rarity": (p and p["rarity"]) or (c["rarity"] if c["rarity"] != "None" else ""),
            "game": "Pocket" if c["pocket"] else "TCG",
            "date": s["date"] or (p and p["date"]) or "",
            "images": imgs + ([] if c["pocket"] else ja_images(c["dex"])),
        }

    # English cards TCGdex has no illustrator for.
    for p in ptcg:
        if p["id"] in used_ptcg:
            continue
        cards[p["id"]] = {
            "id": p["id"], "name": p["name"], "set": p["setName"], "number": p["number"],
            "rarity": p["rarity"], "game": "TCG", "date": p["date"],
            "images": p["images"] + ja_images(p["dex"]),
        }

    # Japanese-exclusive artworks: a Pokémon with no English print by this artist.
    en_dex = set()
    for c in dex_cards:
        if c["region"] == "intl":
            en_dex.update(c["dex"])
    for p in ptcg:
        en_dex.update(p["dex"])
    for c in dex_cards:
        if c["region"] == "ja" and c["dex"] and not set(c["dex"]) & en_dex:
            s = c["set"]
            cid = f"ja-{s['id']}-{c['localId']}"
            cards[cid] = {
                "id": cid, "name": dex_names.get(c["dex"][0], c["name"]), "set": f"{s['ja'] or s['id']} (Japan)", "number": c["localId"],
                "rarity": c["rarity"], "game": "TCG (Japan)", "date": s["date"],
                "images": [c["img"] + "/high.webp", c["img"] + "/high.png"],
            }

    order = {"TCG": 0, "TCG (Japan)": 0, "Pocket": 1}
    result = sorted(cards.values(), key=lambda c: (order[c["game"]], c["date"], c["set"], num_key(c["number"])))
    for c in result:
        c["images"] = list(dict.fromkeys(u for u in c["images"] if u))  # dedupe, keep order
        c.pop("date")
        if not c.get("aliases"):
            c.pop("aliases", None)

    payload = {"artist": artist, "cards": result}
    print("// Generated by tools/build_cards.py. Do not edit by hand.")
    print("window.BINDER_DATA = window.BINDER_DATA || {};")
    print(f"window.BINDER_DATA[{json.dumps(artist.lower())}] = "
          + json.dumps(payload, ensure_ascii=False, indent=1) + ";")


if __name__ == "__main__":
    main()
