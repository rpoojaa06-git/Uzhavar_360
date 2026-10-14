# Uzhavar Demo UI — TN Farmers' Assistant (Sample)

A mobile-first web demo replicating the **Uzhavar** government farmers' assistant app home screen: a blue header and a 3-column grid of **24 service tiles**. Every tile opens a detail page filled with **sample demo data** (info blocks, sample tables, cards, demo forms — no real backend).

Built for demoing a RAG pipeline hand-off: your teammate's pipeline can deep-link straight into any single service, or to the main grid.

## Live deployment

**Production URL:** <https://uzhavar-demo.vercel.app> (hosted on Vercel, auto-deploys on every push to `main` in [github.com/rsakthivel08/Uzhavar_demo](https://github.com/rsakthivel08/Uzhavar_demo)).

## Run it locally

```bash
cd uzhavar-ui
npm install
npm run dev
```

Open **http://localhost:5173** — best viewed in the browser's device toolbar (mobile view) for the app look.

Other scripts: `npm run build` (type-check + production build), `npm run preview` (serve the built `dist/`).

## Deep-link contract (for the RAG pipeline)

Hash routing means every link works on any static host with zero server config.

| URL | Opens |
|---|---|
| `https://uzhavar-demo.vercel.app/#/` | Home grid — all 24 tiles |
| `https://uzhavar-demo.vercel.app/#/market-price` | Market Price detail with sample rates |
| `https://uzhavar-demo.vercel.app/#/service/market-price` | Same as above (alias form) |
| `https://uzhavar-demo.vercel.app/#/links` | Cheat-sheet page listing every deep link with copy buttons |
| any unknown id (e.g. `/#/foo`) | Notice, then auto-redirect to home |

In local dev the same paths work on `http://localhost:5173`.

### All service ids

`tamil-mannvalam` · `subsidy-scheme` · `benefit-registration` · `crop-insurance` · `fertilizer-stock` · `seed-stock` · `machinery-rental` · `market-price` · `weather-advisory` · `officer-contact` · `farm-guide` · `organic-products` · `fpo-products` · `reservoir-levels` · `agri-news` · `feedback` · `pest-disease` · `atma-training` · `e-market` · `sericulture` · `agri-budget` · `kadp` · `palmyra-felling` · `green-mission`

A deep link is simply `https://uzhavar-demo.vercel.app/#/<service-id>`.

Handy shortcut: open **`/#/links`** on the live site to copy any of the 24 URLs in one click.

## Features

- **24 services**, mirroring the reference screenshot's tile order and labels.
- **Sample detail content** per service: info blocks with bullets, sample tables (market price, fertilizer/seed stock, reservoir levels, agri budget), card lists (news, trainings, FPO products), and demo forms (feedback, benefit registration, machinery rental) that show a success toast — nothing is submitted anywhere.
- **Bilingual toggle** — தமிழ் / English button in the header switches every tile label and all detail text; the choice persists in `localStorage`.
- **Search** box on home to filter tiles (handy during demos).
- **`/#/links` page** — every deep link with a one-click copy button, for wiring up the RAG pipeline.

## Adding or renaming a service

Everything is data-driven: edit [src/data/services.ts](src/data/services.ts) — each entry has an `id` (used in the deep link), a bilingual `label`, an icon, an accent color, and its sample content `blocks`. Adding one entry automatically adds the tile, the detail page, and its entry on the `/#/links` page.

## Project structure

```
src/
├─ main.tsx / App.tsx        — entry, HashRouter routes, LangProvider
├─ lang/LangContext.tsx      — தமிழ்/English state + persistence
├─ data/
│  ├─ services.ts            — 24-service registry + all sample content
│  └─ strings.ts             — shared bilingual UI strings
├─ components/
│  ├─ AppHeader.tsx          — blue header, back arrow, language toggle
│  ├─ ServiceGrid.tsx / ServiceTile.tsx
│  └─ ContentBlocks.tsx      — info / table / cards / demo-form renderers
└─ pages/
   ├─ HomePage.tsx           — grid + search
   ├─ ServicePage.tsx        — detail page (unknown id → home)
   └─ LinkIndexPage.tsx      — deep-link cheat sheet
```

## Note

All content is **fabricated sample data for demo purposes only** — it does not represent real government schemes, prices, or contacts.
