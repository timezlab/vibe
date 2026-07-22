#!/usr/bin/env python3
"""
VIBE Brand Asset Generator — single pipeline for every generated asset.

Outputs (brand/marks/ — canonical brand marks):
    wordmark.svg                  standalone VIBE wordmark (Exo2 Bold Italic)
    logo-wordmark-horizontal.svg  logo + wordmark, horizontal lockup
    logo-wordmark-vertical.svg    logo + wordmark, vertical lockup

Outputs (brand/social/ — social/marketing images, built FROM the marks above):
    banner.svg / banner.png       GitHub banner, 1280x640
    og-image.svg / og-image.png   Open Graph image, 1200x630

The banner and OG image embed the freshly built horizontal lockup verbatim,
so logo/text alignment always matches the canonical mark.

Usage:
    python3 brand/generate_assets.py
"""

import os
import time
import urllib.request
import cairosvg
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..")) if os.path.basename(SCRIPT_DIR) in ["brand", "public", "scripts"] else SCRIPT_DIR
MARKS_DIR = os.path.join(REPO_DIR, "brand", "marks")
SOCIAL_DIR = os.path.join(REPO_DIR, "brand", "social")
CACHE_DIR = os.path.expanduser("~/.cache/vibe_fonts")

os.makedirs(MARKS_DIR, exist_ok=True)
os.makedirs(SOCIAL_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

FONTS = {
    "Exo2_BoldItalic": "https://cdn.jsdelivr.net/fontsource/fonts/exo-2@latest/latin-700-italic.ttf",
    "SpaceGrotesk": "https://cdn.jsdelivr.net/fontsource/fonts/space-grotesk@latest/latin-700-normal.ttf",
    "PlusJakartaSans": "https://cdn.jsdelivr.net/fontsource/fonts/plus-jakarta-sans@latest/latin-700-normal.ttf"
}

def download_fonts():
    paths = {}
    for name, url in FONTS.items():
        dest = os.path.join(CACHE_DIR, f"{name}.ttf")
        if not os.path.exists(dest):
            print(f"Downloading font {name}...")
            for attempt in range(3):
                try:
                    urllib.request.urlretrieve(url, dest)
                    break
                except Exception as e:
                    if attempt == 2:
                        print(f"Error downloading {name}: {e}")
                    time.sleep(1)
        paths[name] = dest
    return paths

def get_exact_text_path_and_bounds(font_path, text, font_size=50):
    font = TTFont(font_path)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font['hmtx']
    units_per_em = font['head'].unitsPerEm
    scale = font_size / units_per_em
    x_cursor = 0
    paths = []

    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    for char in text:
        codepoint = ord(char)
        if codepoint not in cmap: continue
        glyph_name = cmap[codepoint]
        glyph = glyph_set[glyph_name]

        bpen = BoundsPen(glyph_set)
        glyph.draw(bpen)
        if bpen.bounds:
            g_min_x, g_min_y, g_max_x, g_max_y = bpen.bounds
            min_x = min(min_x, (g_min_x + x_cursor) * scale)
            min_y = min(min_y, g_min_y * scale)
            max_x = max(max_x, (g_max_x + x_cursor) * scale)
            max_y = max(max_y, g_max_y * scale)

        pen = SVGPathPen(glyph_set)
        tpen = TransformPen(pen, (scale, 0, 0, -scale, x_cursor * scale, 0))
        glyph.draw(tpen)
        d = pen.getCommands()
        if d: paths.append(d)

        x_cursor += hmtx[glyph_name][0]

    return {
        "path_d": " ".join(paths),
        "svg_min_x": min_x,
        "svg_min_y": -max_y,
        "svg_max_x": max_x,
        "svg_max_y": -min_y,
        "real_width": max_x - min_x,
        "real_height": -min_y - (-max_y)
    }

# ---------------------------------------------------------------------------
# Brand marks (wordmark + logo lockups)
# ---------------------------------------------------------------------------

MARK_DEFS = '''    <defs>
        <linearGradient id="leftGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#F472B6" />
            <stop offset="100%" stop-color="#C084FC" />
        </linearGradient>
        <linearGradient id="rightGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#38BDF8" />
            <stop offset="100%" stop-color="#C084FC" />
        </linearGradient>
        <linearGradient id="vibeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#F472B6" />
            <stop offset="50%" stop-color="#C084FC" />
            <stop offset="100%" stop-color="#38BDF8" />
        </linearGradient>
    </defs>'''

# Logo drawing coordinates live in a 200x200 design space; ink spans
# x 20..180 / y 30..170 (w 160, h 140).
LOGO_INNER = '''        <!-- Left Isometric Bracket -->
        <g>
            <path d="M 45,30 L 20,44.43 L 20,155.57 L 45,170" fill="none" stroke="url(#leftGrad)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity="0.3"></path>
            <path d="M 45,30 L 20,44.43 L 20,155.57 L 45,170" fill="none" stroke="url(#leftGrad)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></path>
        </g>
        <!-- Right Isometric Bracket -->
        <g>
            <path d="M 155,30 L 180,44.43 L 180,155.57 L 155,170" fill="none" stroke="url(#rightGrad)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity="0.3"></path>
            <path d="M 155,30 L 180,44.43 L 180,155.57 L 155,170" fill="none" stroke="url(#rightGrad)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></path>
        </g>
        <!-- Bottom -->
        <g transform="translate(100, 127.7)">
            <polygon points="0,-28 24.25,-14 0,0 -24.25,-14" fill="#C084FC"></polygon>
            <polygon points="-24.25,-14 0,0 0,28 -24.25,14" fill="#A855F7"></polygon>
            <polygon points="24.25,-14 0,0 0,28 24.25,14" fill="#9333EA"></polygon>
        </g>
        <!-- Top Left -->
        <g transform="translate(68, 72.3)">
            <polygon points="0,-28 24.25,-14 0,0 -24.25,-14" fill="#F472B6"></polygon>
            <polygon points="-24.25,-14 0,0 0,28 -24.25,14" fill="#EC4899"></polygon>
            <polygon points="24.25,-14 0,0 0,28 24.25,14" fill="#DB2777"></polygon>
        </g>
        <!-- Top Right -->
        <g transform="translate(132, 72.3)">
            <polygon points="0,-28 24.25,-14 0,0 -24.25,-14" fill="#38BDF8"></polygon>
            <polygon points="-24.25,-14 0,0 0,28 -24.25,14" fill="#0EA5E9"></polygon>
            <polygon points="24.25,-14 0,0 0,28 24.25,14" fill="#0284C7"></polygon>
        </g>'''

def build_wordmark_svg(font_info, pad_x=12, pad_y=12):
    w = font_info["real_width"] + pad_x * 2
    h = font_info["real_height"] + pad_y * 2
    tx = pad_x - font_info["svg_min_x"]
    ty = pad_y - font_info["svg_min_y"]

    svg = f'''<svg width="{w:.2f}" height="{h:.2f}" viewBox="0 0 {w:.2f} {h:.2f}" xmlns="http://www.w3.org/2000/svg">
{MARK_DEFS}
    <g transform="translate({tx:.2f}, {ty:.2f})">
        <path d="{font_info['path_d']}" fill="url(#vibeGrad)" />
    </g>
</svg>'''
    return svg

def build_horizontal_combo_svg(font_info, logo_size=75, gap=18, pad_x=12, pad_y=12):
    """Returns (svg, ink_bounds) — ink_bounds is the visual extent of the
    content inside the viewBox, used to place the lockup inside banners."""
    scale = logo_size / 200.0
    logo_w = 160.0 * scale
    logo_h = 140.0 * scale

    text_w = font_info["real_width"]
    text_h = font_info["real_height"]

    total_w = logo_w + gap + text_w + pad_x * 2
    total_h = max(logo_h, text_h) + pad_y * 2

    logo_x = pad_x - (20.0 * scale)
    logo_y = pad_y + (total_h - pad_y * 2 - logo_h) / 2.0 - (30.0 * scale)

    text_target_top_y = pad_y + (total_h - pad_y * 2 - text_h) / 2.0
    tx = pad_x + logo_w + gap - font_info["svg_min_x"]
    ty = text_target_top_y - font_info["svg_min_y"]

    svg = f'''<svg width="{total_w:.2f}" height="{total_h:.2f}" viewBox="0 0 {total_w:.2f} {total_h:.2f}" xmlns="http://www.w3.org/2000/svg">
{MARK_DEFS}
    <!-- Logo -->
    <g transform="translate({logo_x:.2f}, {logo_y:.2f}) scale({scale})">
{LOGO_INNER}
    </g>
    <!-- Wordmark -->
    <g transform="translate({tx:.2f}, {ty:.2f})">
        <path d="{font_info['path_d']}" fill="url(#vibeGrad)" />
    </g>
</svg>'''
    ink_bounds = {
        "x0": pad_x,
        "y0": pad_y,
        "x1": total_w - pad_x,
        "y1": pad_y + max(logo_h, text_h),
    }
    return svg, ink_bounds

def build_vertical_combo_svg(font_info, logo_size=85, gap=18, pad_x=15, pad_y=15):
    scale = logo_size / 200.0
    logo_w = 160.0 * scale
    logo_h = 140.0 * scale

    text_w = font_info["real_width"]
    real_text_h = font_info["real_height"]

    total_w = max(logo_w, text_w) + pad_x * 2
    total_h = logo_h + gap + real_text_h + pad_y * 2

    logo_x = pad_x + (total_w - pad_x * 2 - logo_w) / 2.0 - (20.0 * scale)
    logo_y = pad_y - (30.0 * scale)

    text_target_left_x = pad_x + (total_w - pad_x * 2 - text_w) / 2.0
    text_target_top_y = pad_y + logo_h + gap
    tx = text_target_left_x - font_info["svg_min_x"]
    ty = text_target_top_y - font_info["svg_min_y"]

    svg = f'''<svg width="{total_w:.2f}" height="{total_h:.2f}" viewBox="0 0 {total_w:.2f} {total_h:.2f}" xmlns="http://www.w3.org/2000/svg">
{MARK_DEFS}
    <!-- Logo -->
    <g transform="translate({logo_x:.2f}, {logo_y:.2f}) scale({scale})">
{LOGO_INNER}
    </g>
    <!-- Wordmark -->
    <g transform="translate({tx:.2f}, {ty:.2f})">
        <path d="{font_info['path_d']}" fill="url(#vibeGrad)" />
    </g>
</svg>'''
    return svg

def svg_inner(svg):
    """Inner markup of a mark SVG with its <defs> stripped — banner/OG defs
    define the same gradient ids."""
    return svg.split("</defs>", 1)[1].rsplit("</svg>", 1)[0]

# ---------------------------------------------------------------------------
# Banner + OG image (built from the horizontal lockup)
# ---------------------------------------------------------------------------

BANNER_DEFS = '''    <defs>
        <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#05070D" />
            <stop offset="50%" stop-color="#0B1220" />
            <stop offset="100%" stop-color="#070A12" />
        </linearGradient>
        <radialGradient id="pinkGlow" cx="12%" cy="18%" r="45%">
            <stop offset="0%" stop-color="#EC4899" stop-opacity="0.14" />
            <stop offset="100%" stop-color="#000000" stop-opacity="0" />
        </radialGradient>
        <radialGradient id="blueGlow" cx="88%" cy="82%" r="55%">
            <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.10" />
            <stop offset="55%" stop-color="#A855F7" stop-opacity="0.05" />
            <stop offset="100%" stop-color="#000000" stop-opacity="0" />
        </radialGradient>
        <linearGradient id="vibeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#F472B6" />
            <stop offset="50%" stop-color="#C084FC" />
            <stop offset="100%" stop-color="#38BDF8" />
        </linearGradient>
        <linearGradient id="textGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#FFFFFF" />
            <stop offset="100%" stop-color="#CBD5E1" />
        </linearGradient>
        <linearGradient id="leftGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#F472B6" />
            <stop offset="100%" stop-color="#C084FC" />
        </linearGradient>
        <linearGradient id="rightGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#38BDF8" />
            <stop offset="100%" stop-color="#C084FC" />
        </linearGradient>
        <linearGradient id="borderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#8B4670" />
            <stop offset="50%" stop-color="#382C53" />
            <stop offset="100%" stop-color="#236F95" />
        </linearGradient>
        <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#334155" stroke-width="1" opacity="0.14"/>
        </pattern>
        <filter id="glassShadow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#000000" flood-opacity="0.55"/>
        </filter>
    </defs>'''

BADGES = [
    ("Canonical Harness", "#F472B6", "#764069"),
    ("Multi-Agent Workspace", "#C084FC", "#5F4888"),
    ("Governed Memory", "#38BDF8", "#216287"),
]

def build_badge(text_path, accent, accent_dim, x):
    """Pill badge sized to its label, with a colored dot instead of emoji
    (emoji glyphs are missing in cairosvg's fallback fonts). accent_dim is
    the accent pre-blended against the pill background — no alpha used."""
    pad_text, pad_right = 30, 18
    pill_w = pad_text + text_path["real_width"] + pad_right
    pill_h = 38
    tx = pad_text - text_path["svg_min_x"]
    ty = pill_h / 2 - (text_path["svg_min_y"] + text_path["svg_max_y"]) / 2
    svg = f'''        <g transform="translate({x:.2f}, 0)">
            <rect width="{pill_w:.2f}" height="{pill_h}" rx="{pill_h/2}" fill="#0F172A" stroke="{accent_dim}" stroke-width="1.2" />
            <circle cx="17" cy="{pill_h/2}" r="4" fill="{accent}" />
            <g transform="translate({tx:.2f}, {ty:.2f})">
                <path d="{text_path['path_d']}" fill="#DDE6F2" />
            </g>
        </g>'''
    return svg, pill_w

def build_badge_row(font_paths, gap=14):
    """Returns (svg_rows, total_width) for the badge pills, laid out at x=0."""
    badge_paths = [get_exact_text_path_and_bounds(font_paths["PlusJakartaSans"], t, font_size=13) for t, _, _ in BADGES]
    svgs = []
    bx = 0.0
    for (text, accent, accent_dim), tpath in zip(BADGES, badge_paths):
        svg, pill_w = build_badge(tpath, accent, accent_dim, bx)
        svgs.append(svg)
        bx += pill_w + gap
    return "\n".join(svgs), bx - gap

def build_agent_pane(x, y, w, h, name, accent, task, pct, pane_id):
    bar_w = (w - 32) * pct
    return f'''        <g transform="translate({x:.0f}, {y:.0f})">
            <rect width="{w:.0f}" height="{h}" rx="10" fill="#0C1424" stroke="#22304A" stroke-width="1" />
            <circle cx="17" cy="21" r="4" fill="{accent}" />
            <text x="29" y="25" font-family="monospace" font-size="12" font-weight="600" fill="#E2E8F0">{name}</text>
            <text x="{w-16:.0f}" y="25" text-anchor="end" font-family="monospace" font-size="10" fill="#64748B">{int(pct*100)}%</text>
            <text x="16" y="50" font-family="monospace" font-size="11" fill="#94A3B8">{task}</text>
            <rect x="16" y="63" width="{w-32:.0f}" height="6" rx="3" fill="#1B2537" />
            <rect x="16" y="63" width="{bar_w:.0f}" height="6" rx="3" fill="{accent}" />
            <text x="16" y="87" font-family="monospace" font-size="10" fill="#5B6B84">worktree · {pane_id}</text>
        </g>'''

def build_terminal(x, y):
    """Mock 'vibe' app window: init log + 2x2 multi-agent pane grid + status bar."""
    w, h = 490, 480
    pad = 24
    inner_w = w - 2 * pad
    pane_gap = 12
    pane_w = (inner_w - pane_gap) / 2
    pane_h = 100

    panes = [
        ("agent-1", "#38BDF8", "refactoring core engine…", 0.72, "pane-1"),
        ("agent-2", "#F472B6", "writing unit tests…", 0.45, "pane-2"),
        ("agent-3", "#C084FC", "syncing skill adapters…", 0.88, "pane-3"),
        ("agent-4", "#34D399", "reviewing memory notes…", 0.31, "pane-4"),
    ]
    grid_y = 206
    pane_svg = "\n".join(
        build_agent_pane(
            pad + (i % 2) * (pane_w + pane_gap),
            grid_y + (i // 2) * (pane_h + pane_gap),
            pane_w, pane_h, *p
        )
        for i, p in enumerate(panes)
    )

    return f'''    <g transform="translate({x}, {y})" filter="url(#glassShadow)">
        <rect width="{w}" height="{h}" rx="16" fill="#0A0E18" />

        <!-- Title bar (border is drawn last, on top, so this can run to the edge) -->
        <path d="M 0 16 Q 0 0 16 0 L {w-16} 0 Q {w} 0 {w} 16 L {w} 44 L 0 44 Z" fill="#111827" />
        <line x1="0" y1="44" x2="{w}" y2="44" stroke="#22304A" stroke-width="1" />
        <circle cx="24" cy="22" r="5.5" fill="#FF5F56" />
        <circle cx="43" cy="22" r="5.5" fill="#FFBD2E" />
        <circle cx="62" cy="22" r="5.5" fill="#27C93F" />
        <text x="{w/2}" y="26" text-anchor="middle" fill="#7C8DA6" font-family="monospace" font-size="13">vibe — multi-agent workspace</text>

        <!-- Init log -->
        <g transform="translate({pad}, 74)" font-family="monospace" font-size="13">
            <text y="0"><tspan fill="#5B6B84">$</tspan> <tspan fill="#38BDF8">vibe init</tspan></text>
            <text y="26" fill="#94A3B8"><tspan fill="#34D399">✔</tspan> 4 CLI agent harnesses detected</text>
            <text y="52" fill="#94A3B8"><tspan fill="#34D399">✔</tspan> 14 canonical skills synced</text>
            <text y="78" fill="#94A3B8"><tspan fill="#34D399">✔</tspan> git worktrees ready · pane-1..4</text>
        </g>

        <!-- Workspace section -->
        <g transform="translate({pad}, 190)" font-family="monospace">
            <text y="0" font-size="10" fill="#5B6B84" letter-spacing="2">WORKSPACE · 4 PANES</text>
            <line x1="142" y1="-4" x2="{inner_w}" y2="-4" stroke="#1B2537" stroke-width="1" />
        </g>
{pane_svg}

        <!-- Status bar -->
        <line x1="0" y1="{h-38}" x2="{w}" y2="{h-38}" stroke="#22304A" stroke-width="1" />
        <g font-family="monospace" font-size="11">
            <circle cx="{pad+4}" cy="{h-19}" r="3.5" fill="#34D399" />
            <text x="{pad+16}" y="{h-15}" fill="#94A3B8">4 agents active</text>
            <text x="{w-pad}" y="{h-15}" text-anchor="end" fill="#5B6B84">skills: canonical · memory: governed</text>
        </g>

        <!-- Card border drawn last so nothing paints over it -->
        <rect width="{w}" height="{h}" rx="16" fill="none" stroke="url(#borderGrad)" stroke-width="1.5" />
    </g>'''

def build_banner(font_paths, combo_svg, ink):
    w, h = 1280, 640
    left_x = 90

    wordmark_inner = svg_inner(combo_svg)
    wm_scale = 1.85
    wm_w = (ink["x1"] - ink["x0"]) * wm_scale
    wm_h = (ink["y1"] - ink["y0"]) * wm_scale

    acronym = get_exact_text_path_and_bounds(font_paths["SpaceGrotesk"], "Vibe Integrated Build Environment", font_size=21)
    line1 = get_exact_text_path_and_bounds(font_paths["PlusJakartaSans"], "The IDE of the", font_size=50)
    line2 = get_exact_text_path_and_bounds(font_paths["Exo2_BoldItalic"], "Vibe-Coding Era", font_size=58)
    badge_row, _ = build_badge_row(font_paths)

    # Vertical rhythm: stack heights + gaps, then center the block in the canvas.
    gap_wm_acr, gap_acr_l1, gap_l1_l2, gap_l2_badges = 30, 50, 22, 56
    badge_h = 38
    block_h = (wm_h + gap_wm_acr + acronym["real_height"] + gap_acr_l1
               + line1["real_height"] + gap_l1_l2 + line2["real_height"]
               + gap_l2_badges + badge_h)
    top = (h - block_h) / 2

    wm_tx = left_x - ink["x0"] * wm_scale
    wm_ty = top - ink["y0"] * wm_scale

    acr_top = top + wm_h + gap_wm_acr
    acr_x = left_x - acronym["svg_min_x"]
    acr_y = acr_top - acronym["svg_min_y"]

    line1_top = acr_top + acronym["real_height"] + gap_acr_l1
    line1_x = left_x - line1["svg_min_x"]
    line1_y = line1_top - line1["svg_min_y"]

    line2_top = line1_top + line1["real_height"] + gap_l1_l2
    line2_x = left_x - line2["svg_min_x"]
    line2_y = line2_top - line2["svg_min_y"]

    badges_y = line2_top + line2["real_height"] + gap_l2_badges

    term_w, term_h = 490, 480
    terminal = build_terminal(w - 90 - term_w, (h - term_h) / 2)

    return f'''<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
{BANNER_DEFS}
    <rect width="{w}" height="{h}" fill="url(#bgGradient)" />
    <rect width="{w}" height="{h}" fill="url(#grid)" />
    <rect width="{w}" height="{h}" fill="url(#pinkGlow)" />
    <rect width="{w}" height="{h}" fill="url(#blueGlow)" />

    <rect x="0" y="0" width="{w}" height="3" fill="url(#vibeGrad)" />
    <rect x="0" y="{h-3}" width="{w}" height="3" fill="url(#vibeGrad)" />

    <!-- Canonical horizontal lockup (same build as logo-wordmark-horizontal.svg) -->
    <g transform="translate({wm_tx:.2f}, {wm_ty:.2f}) scale({wm_scale})">
{wordmark_inner}
    </g>

    <g transform="translate({acr_x:.2f}, {acr_y:.2f})">
        <path d="{acronym['path_d']}" fill="#8FA3C0" />
    </g>

    <g transform="translate({line1_x:.2f}, {line1_y:.2f})">
        <path d="{line1['path_d']}" fill="url(#textGrad)" />
    </g>

    <g transform="translate({line2_x:.2f}, {line2_y:.2f})">
        <path d="{line2['path_d']}" fill="url(#vibeGrad)" />
    </g>

    <g transform="translate({left_x}, {badges_y:.2f})">
{badge_row}
    </g>

{terminal}
</svg>'''

def build_og_image(font_paths, combo_svg, ink):
    w, h = 1200, 630

    wordmark_inner = svg_inner(combo_svg)
    wm_scale = 2.5
    wm_w = (ink["x1"] - ink["x0"]) * wm_scale
    wm_h = (ink["y1"] - ink["y0"]) * wm_scale

    acronym = get_exact_text_path_and_bounds(font_paths["SpaceGrotesk"], "Vibe Integrated Build Environment", font_size=22)
    tag1 = get_exact_text_path_and_bounds(font_paths["PlusJakartaSans"], "The IDE of the", font_size=46)
    tag2 = get_exact_text_path_and_bounds(font_paths["Exo2_BoldItalic"], "Vibe-Coding Era", font_size=52)
    badge_row, badges_total_w = build_badge_row(font_paths)

    # Tagline is one line: "The IDE of the" + "Vibe-Coding Era", baselines aligned.
    tag_gap = 18
    tag_total_w = tag1["real_width"] + tag_gap + tag2["real_width"]
    tag_min_y = min(tag1["svg_min_y"], tag2["svg_min_y"])
    tag_max_y = max(tag1["svg_max_y"], tag2["svg_max_y"])
    tag_h = tag_max_y - tag_min_y
    badge_h = 38

    # Vertical rhythm: stack heights + gaps, then center the block in the canvas.
    gap_wm_acr, gap_acr_tag, gap_tag_badges = 32, 52, 56
    block_h = wm_h + gap_wm_acr + acronym["real_height"] + gap_acr_tag + tag_h + gap_tag_badges + badge_h
    top = (h - block_h) / 2

    wm_tx = (w - wm_w) / 2 - ink["x0"] * wm_scale
    wm_ty = top - ink["y0"] * wm_scale

    acr_top = top + wm_h + gap_wm_acr
    acr_x = (w - acronym["real_width"]) / 2 - acronym["svg_min_x"]
    acr_y = acr_top - acronym["svg_min_y"]

    tag_top = acr_top + acronym["real_height"] + gap_acr_tag
    tag_baseline = tag_top - tag_min_y
    tag_start_x = (w - tag_total_w) / 2
    tag1_x = tag_start_x - tag1["svg_min_x"]
    tag2_x = tag_start_x + tag1["real_width"] + tag_gap - tag2["svg_min_x"]

    badges_y = tag_top + tag_h + gap_tag_badges
    badges_x = (w - badges_total_w) / 2

    return f'''<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
{BANNER_DEFS}
    <rect width="{w}" height="{h}" fill="url(#bgGradient)" />
    <rect width="{w}" height="{h}" fill="url(#grid)" />
    <rect width="{w}" height="{h}" fill="url(#pinkGlow)" />
    <rect width="{w}" height="{h}" fill="url(#blueGlow)" />

    <rect x="0" y="0" width="{w}" height="3" fill="url(#vibeGrad)" />
    <rect x="0" y="{h-3}" width="{w}" height="3" fill="url(#vibeGrad)" />

    <!-- Canonical horizontal lockup (same build as logo-wordmark-horizontal.svg) -->
    <g transform="translate({wm_tx:.2f}, {wm_ty:.2f}) scale({wm_scale})">
{wordmark_inner}
    </g>

    <g transform="translate({acr_x:.2f}, {acr_y:.2f})">
        <path d="{acronym['path_d']}" fill="#8FA3C0" />
    </g>

    <g transform="translate({tag1_x:.2f}, {tag_baseline:.2f})">
        <path d="{tag1['path_d']}" fill="url(#textGrad)" />
    </g>
    <g transform="translate({tag2_x:.2f}, {tag_baseline:.2f})">
        <path d="{tag2['path_d']}" fill="url(#vibeGrad)" />
    </g>

    <g transform="translate({badges_x:.2f}, {badges_y:.2f})">
{badge_row}
    </g>
</svg>'''

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def write_svg(path, svg):
    with open(path, "w") as f:
        f.write(svg)
    print(f"✔ Saved {path}")

def main():
    print("VIBE Brand Asset Generator")
    font_paths = download_fonts()

    # 1. Brand marks (brand/marks/)
    vibe_info = get_exact_text_path_and_bounds(font_paths["Exo2_BoldItalic"], "VIBE", font_size=46)

    wm_svg = build_wordmark_svg(vibe_info)
    combo_h_svg, combo_h_ink = build_horizontal_combo_svg(vibe_info)
    combo_v_svg = build_vertical_combo_svg(vibe_info)

    write_svg(os.path.join(MARKS_DIR, "wordmark.svg"), wm_svg)
    write_svg(os.path.join(MARKS_DIR, "logo-wordmark-horizontal.svg"), combo_h_svg)
    write_svg(os.path.join(MARKS_DIR, "logo-wordmark-vertical.svg"), combo_v_svg)

    # 2. Banner (brand/social/), embedding the horizontal lockup built above
    banner_svg = build_banner(font_paths, combo_h_svg, combo_h_ink)
    write_svg(os.path.join(SOCIAL_DIR, "banner.svg"), banner_svg)
    cairosvg.svg2png(bytestring=banner_svg.encode('utf-8'), write_to=os.path.join(SOCIAL_DIR, "banner.png"))
    print(f"✔ Saved {os.path.join(SOCIAL_DIR, 'banner.png')} (1280x640)")

    # 3. OG image (brand/social/)
    og_svg = build_og_image(font_paths, combo_h_svg, combo_h_ink)
    write_svg(os.path.join(SOCIAL_DIR, "og-image.svg"), og_svg)
    cairosvg.svg2png(bytestring=og_svg.encode('utf-8'), write_to=os.path.join(SOCIAL_DIR, "og-image.png"))
    print(f"✔ Saved {os.path.join(SOCIAL_DIR, 'og-image.png')} (1200x630)")

    print("\n🎉 All VIBE brand assets generated!")

if __name__ == "__main__":
    main()
