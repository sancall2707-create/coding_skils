"""
gen-icons.py
Generate square PWA icons + favicon from an arbitrary source logo image.
Usage: python gen-icons.py <source_image> [<output_dir>]
Defaults: source from cache, output to public/ of the Laravel project.
"""
import sys
import os
from PIL import Image

src_path = sys.argv[1] if len(sys.argv) > 1 else "logo.jpg"
out_base = sys.argv[2] if len(sys.argv) > 2 else "public"

os.makedirs(f"{out_base}/images", exist_ok=True)
os.makedirs(f"{out_base}/icons", exist_ok=True)

img = Image.open(src_path).convert("RGB")
w, h = img.size

# Center-crop to square (no distortion)
side = min(w, h)
left = (w - side) // 2
top = (h - side) // 2
square = img.crop((left, top, left + side, top + side))

# Main logo PNG
square.save(f"{out_base}/images/logo.png", "PNG")

# PWA icons
for size, path in [
    (192, f"{out_base}/icons/icon-192x192.png"),
    (512, f"{out_base}/icons/icon-512x512.png"),
    (64,  f"{out_base}/favicon.png"),
]:
    square.resize((size, size), Image.Resampling.LANCZOS).save(path, "PNG")

# Favicon ICO
square.resize((32, 32), Image.Resampling.LANCZOS).save(f"{out_base}/favicon.ico", "ICO")

print(f"Done: source {w}x{h} → square {side}x{side}, output: {out_base}/")