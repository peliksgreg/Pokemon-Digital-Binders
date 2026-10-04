# Pokémon Digital Binder

A mobile-first digital binder for every Pokémon TCG card by an illustrator.
The default binder is **Shinji Kanda** (the same 55 cards as
[artofpkm.com/illustrators/shinji-kanda/cards](https://www.artofpkm.com/illustrators/shinji-kanda/cards)).

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
[artofpkm.com/illustrators/shinji-kanda/cards](https://www.artofpkm.com/illustrators/shinji-kanda/cards)
card for card: 55 cards (45 TCG, 10 TCG Pocket), in the site's order, with the
site's card images, rarities and set names (Japanese releases, as the site lists them).
In the card details, **Source** links to the card's page on artofpkm.com.

The list is embedded inside `index.html` (the `<script id="card-data">` block),
so the single file works on its own, even opened straight from a phone's Downloads.
If an artofpkm image fails to load, the app tries TCGdex (same Japanese print),
then pokemontcg.io / TCGdex (English print of the same artwork).

Marks saved with the earlier English-print list carry over to the matching card.

To rebuild the list, or build one for another illustrator on artofpkm.com
(the slug is the one in the site's URL):

```sh
python3 tools/build_artofpkm.py shinji-kanda "Shinji Kanda" > cards.js
# optional: add fallback images from the open datasets
curl -sL https://www.artofpkm.com/illustrators/shinji-kanda/cards -o page.html
git clone --depth 1 https://github.com/tcgdex/cards-database.git
git clone --depth 1 https://github.com/PokemonTCG/pokemon-tcg-data.git
python3 tools/add_fallback_images.py cards.js page.html cards-database pokemon-tcg-data > cards.full.js
python3 tools/inline_data.py cards.full.js index.html
```

`tools/build_cards.py` builds a list from the open
[TCGdex](https://github.com/tcgdex/cards-database) and
[PokemonTCG](https://github.com/PokemonTCG/pokemon-tcg-data) datasets instead
(English prints, with pokemontcg.io and TCGdex images).

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
