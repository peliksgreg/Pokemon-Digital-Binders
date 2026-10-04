# Pokémon Digital Binder

A mobile-first digital binder for every Pokémon TCG card by an illustrator.
The default binder is **Shinji Kanda** (the same set of cards as
[artofpkm.com/illustrators/shinji-kanda](https://www.artofpkm.com/illustrators/shinji-kanda)).

It is a single static page (`index.html`): no build step, no server code, no account.

## Features

- **Tap a card to toggle owned / not owned.** Missing cards are greyed out; owned cards
  show in full colour with a green check. An **Undo** toast appears after every tap.
- **Binder view**: 9-pocket pages you swipe left and right, with a page picker.
  **Grid view**: one scrolling list. The button at the top right switches between them.
- Progress bar (owned / total and %), **All / Have / Need** filters, and search by name or set.
- Tap **ⓘ** (or long-press a card) for a large view with set, number and Prev/Next.
- Your owned list is saved on the device. **Settings → Backup** downloads or copies it,
  and imports it again (an import merges, so nothing you've marked is lost).
- Works offline after the first load: the card list is cached on the device, and when the
  page is served over http(s) a service worker also caches the page and card images.
- Any illustrator works: change it in Settings, or open `index.html?artist=Mitsuhiro%20Arita`.
  Card languages: English, Japanese, French, German, Spanish, Italian.

## Card data

The Shinji Kanda list matches
[artofpkm.com/illustrators/shinji-kanda/cards](https://www.artofpkm.com/illustrators/shinji-kanda/cards):
**55 cards**, the Japanese TCG prints (including mirror variants and deck reprints)
plus the TCG Pocket cards, in the same order as the site.

The list is embedded inside `index.html` (the `<script id="card-data">` block),
so the single file works on its own, even opened straight from a phone's Downloads.
Card images come from artofpkm's scans. If one fails to load, the app tries
TCGdex (Japanese print), then pokemontcg.io / TCGdex (English print of the same artwork).

To rebuild the list (needs access to artofpkm.com and GitHub):

```sh
curl -sL https://www.artofpkm.com/illustrators/shinji-kanda/cards -o page.html
git clone --depth 1 https://github.com/tcgdex/cards-database.git
git clone --depth 1 https://github.com/PokemonTCG/pokemon-tcg-data.git
python3 tools/build_from_artofpkm.py page.html cards-database pokemon-tcg-data "Shinji Kanda" > cards.js
python3 tools/inline_data.py cards.js index.html
```

`tools/build_cards.py` builds an English-print list from the two databases alone,
for illustrators without an artofpkm page. Illustrators without a built-in list are
loaded live from the [TCGdex API](https://tcgdex.dev), with
[pokemontcg.io](https://pokemontcg.io) as an English fallback.

## Using it on your phone

**Easiest: GitHub Pages (works on iPhone and Android)**
1. On GitHub, go to repo **Settings → Pages**, set *Source* to *Deploy from a branch*, and
   pick this branch and the `/ (root)` folder.
2. Open the published URL on your phone.
3. Add it to your home screen (Safari: Share → *Add to Home Screen*;
   Chrome: ⋮ → *Add to Home screen*). It then opens full screen like an app and works offline.

**Fully local**
- **Android**: copy `index.html` to the phone and open it in Chrome or Firefox.
  The file is self-contained, so opening it from Downloads works.
- **iPhone/iPad**: the Files app preview doesn't run JavaScript. Use GitHub Pages,
  or serve the folder from a computer on the same Wi-Fi:
  ```sh
  python3 -m http.server 8000
  ```
  Then open `http://<computer-ip>:8000` on the phone.

The first load needs internet to fetch the card list. After that it's cached.
Owned marks are stored separately for each address (a `file://` copy and the
GitHub Pages copy don't share marks), so use **Backup** to move them between the two.
