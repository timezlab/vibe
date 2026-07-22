# Brand assets

Canonical VIBE brand marks and the social images built from them. Edit
source files here, not copies elsewhere in the repo.

## Structure

```
brand/
├── marks/    canonical brand marks (source of truth)
├── social/   generated marketing/social images, built FROM marks/
└── generate_assets.py   pipeline that builds both folders
```

| File | What it is |
|---|---|
| `marks/logo.svg` | Icon-only mark (isometric brackets + cube). Hand-authored source. |
| `marks/favicon.svg` | `logo.svg` on a rounded dark chip with a subtle gray border — for browser tabs/app icons. Hand-authored, derived from `logo.svg`. |
| `marks/wordmark.svg` | Standalone "VIBE" wordmark. Generated. |
| `marks/logo-wordmark-horizontal.svg` | Logo + wordmark, horizontal lockup. Generated. |
| `marks/logo-wordmark-vertical.svg` | Logo + wordmark, vertical lockup. Generated. |
| `social/banner.svg` / `.png` | GitHub repo banner, 1280×640. Generated. |
| `social/og-image.svg` / `.png` | Open Graph share image, 1200×630. Generated. |
| `generate_assets.py` | Generator for everything above. |

`social/` is a pure build artifact — never hand-edit those files; run the
generator instead.

## Fonts

| Font | Weight | Used for |
|---|---|---|
| [Exo 2](https://fontsource.org/fonts/exo-2) | 700 Italic | "VIBE" wordmark, "Vibe-Coding Era" tagline — the brand display face |
| [Space Grotesk](https://fontsource.org/fonts/space-grotesk) | 700 | Small acronym caption ("Vibe Integrated Build Environment") |
| [Plus Jakarta Sans](https://fontsource.org/fonts/plus-jakarta-sans) | 700 | "The IDE of the" tagline + badge pill labels on banner/OG image |

Downloaded from Fontsource on first run and cached at `~/.cache/vibe_fonts`.

## Colors

### Core palette — logo, wordmark, lockups

Gradients (`leftGrad`, `rightGrad` vertical; `vibeGrad` horizontal, used for
wordmark text fill):

| Gradient | Stops |
|---|---|
| `leftGrad` | `#F472B6` → `#C084FC` |
| `rightGrad` | `#38BDF8` → `#C084FC` |
| `vibeGrad` | `#F472B6` → `#C084FC` → `#38BDF8` |

Cube facets (top / left-shade / right-shade per cube):

| Cube | Top | Left | Right |
|---|---|---|---|
| Bottom (purple) | `#C084FC` | `#A855F7` | `#9333EA` |
| Top-left (pink) | `#F472B6` | `#EC4899` | `#DB2777` |
| Top-right (blue) | `#38BDF8` | `#0EA5E9` | `#0284C7` |

### Extended palette — banner / OG image only

Used for the dark background, glass-card mockup, and badges in
`social/banner.*` and `social/og-image.*` — not part of the logo itself.

| Role | Color(s) |
|---|---|
| Background gradient | `#05070D` → `#0B1220` → `#070A12` |
| Pink/blue ambient glow | `#EC4899` @ 14% · `#38BDF8` @ 10% · `#A855F7` @ 5% |
| Card border gradient | `#8B4670` → `#382C53` → `#236F95` |
| Heading text gradient | `#FFFFFF` → `#CBD5E1` |
| Grid lines | `#334155` @ 14% |
| Badge pills (accent / dimmed) | pink `#F472B6`/`#764069` · purple `#C084FC`/`#5F4888` · blue `#38BDF8`/`#216287` |
| Terminal mockup chrome | bg `#0A0E18` · titlebar `#111827` · borders `#22304A` · traffic lights `#FF5F56`/`#FFBD2E`/`#27C93F` |
| Terminal mockup text | `#E2E8F0` primary · `#94A3B8` secondary · `#7C8DA6`/`#64748B`/`#5B6B84` muted |
| Agent pane accents | `#38BDF8` · `#F472B6` · `#C084FC` · `#34D399` |

## Regenerating

```
python3 brand/generate_assets.py
```

Rebuilds `marks/wordmark.svg` and both lockups, then rebuilds
`social/banner.{svg,png}` and `social/og-image.{svg,png}` from the freshly
built horizontal lockup, so text/logo alignment always matches. Requires
`cairosvg` and `fonttools`.

`marks/logo.svg` and `marks/favicon.svg` are not written by the script —
`logo.svg`'s markup is duplicated inline as `LOGO_INNER` in
`generate_assets.py` so the lockups and social images can embed it, and
`favicon.svg` embeds the same icon markup again on a rounded chip with a
gray border.
If you hand-edit `logo.svg`, update `LOGO_INNER` and `favicon.svg` to
match.
