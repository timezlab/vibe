#!/usr/bin/env python3
"""
VIBE Favicon Generator — rasterizes brand/marks/favicon.svg into the PNG
sizes and multi-resolution .ico that browsers/OSes expect.

Source (hand-authored):
    brand/marks/favicon.svg

Outputs (brand/favicon/ — build artifacts, regenerate, never hand-edit):
    favicon-16x16.png
    favicon-32x32.png
    favicon-48x48.png
    favicon-64x64.png
    favicon-128x128.png
    favicon-180x180.png   Apple touch icon size
    favicon-192x192.png   Android/PWA icon size
    favicon-512x512.png   Android/PWA large icon size
    favicon.ico           16/32/48 embedded in one .ico

Each PNG is rasterized directly from the SVG at its target size (not
downsampled from a larger bitmap), so every size stays crisp. The .ico
embeds the exact 16/32/48 renders rather than resizing a single image.

Usage:
    python3 brand/generate_favicons.py
"""

import os
import cairosvg
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..")) if os.path.basename(SCRIPT_DIR) in ["brand", "public", "scripts"] else SCRIPT_DIR
SVG_PATH = os.path.join(REPO_DIR, "brand", "marks", "favicon.svg")
OUT_DIR = os.path.join(REPO_DIR, "brand", "favicon")

PNG_SIZES = [16, 32, 48, 64, 128, 180, 192, 512]
ICO_SIZES = [16, 32, 48]

def render_png(size):
    path = os.path.join(OUT_DIR, f"favicon-{size}x{size}.png")
    cairosvg.svg2png(url=SVG_PATH, write_to=path, output_width=size, output_height=size)
    print(f"✔ Saved {path}")
    return path

def build_ico(png_paths):
    ico_path = os.path.join(OUT_DIR, "favicon.ico")
    images = {size: Image.open(png_paths[size]) for size in ICO_SIZES}
    base_size = max(ICO_SIZES)
    base = images[base_size]
    others = [images[size] for size in ICO_SIZES if size != base_size]
    base.save(
        ico_path,
        format="ICO",
        sizes=[(size, size) for size in ICO_SIZES],
        append_images=others,
    )
    print(f"✔ Saved {ico_path} ({'/'.join(str(s) for s in ICO_SIZES)})")

def main():
    print("VIBE Favicon Generator")
    os.makedirs(OUT_DIR, exist_ok=True)

    png_paths = {size: render_png(size) for size in PNG_SIZES}
    build_ico(png_paths)

    print("\n🎉 All favicons generated!")

if __name__ == "__main__":
    main()
