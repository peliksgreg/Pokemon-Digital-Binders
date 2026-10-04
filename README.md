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

The Shinji Kanda list is built into the app (`cards.js`), so it loads instantly
and needs no card API. It has 40 cards: 33 TCG prints (including promos and one
Japan-only card) and 7 TCG Pocket cards. It combines the open
[TCGdex](https://github.com/tcgdex/cards-database) and
[PokemonTCG](https://github.com/PokemonTCG/pokemon-tcg-data) datasets.

Each card has several image sources (pokemontcg.io, TCGdex English, then the
Japanese print of the same artwork). If one host has no picture, the next one is tried.

To rebuild the list, or build one for another illustrator:

```sh
git clone --depth 1 https://github.com/tcgdex/cards-database.git
git clone --depth 1 https://github.com/PokemonTCG/pokemon-tcg-data.git
python3 tools/build_cards.py cards-database pokemon-tcg-data "Shinji Kanda" > cards.js
```

Illustrators without a built-in list are loaded live from the
[TCGdex API](https://tcgdex.dev), with [pokemontcg.io](https://pokemontcg.io) as an
English fallback. Their lists refresh once a week, or on **Settings → Refresh data**.

## Using it on your phone

**Easiest: GitHub Pages (works on iPhone and Android)**
1. On GitHub, go to repo **Settings → Pages**, set *Source* to *Deploy from a branch*, and
   pick this branch and the `/ (root)` folder.
2. Open the published URL on your phone.
3. Add it to your home screen (Safari: Share → *Add to Home Screen*;
   Chrome: ⋮ → *Add to Home screen*). It then opens full screen like an app and works offline.

**Fully local**
- **Android**: copy `index.html` to the phone and open it in Chrome or Firefox
  (e.g. `file:///sdcard/Download/index.html`), or use a local web-server app.
- **iPhone/iPad**: the Files app preview doesn't run JavaScript. Use GitHub Pages,
  or serve the folder from a computer on the same Wi-Fi:
  ```sh
  python3 -m http.server 8000
  ```
  Then open `http://<computer-ip>:8000` on the phone.

The first load needs internet to fetch the card list. After that it's cached.
Owned marks are stored separately for each address (a `file://` copy and the
GitHub Pages copy don't share marks), so use **Backup** to move them between the two.
