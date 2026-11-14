import os
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion, gaussian_filter

input_path = "ASCII ART/better-face_cutout.png"
img = Image.open(input_path).convert("RGBA")
w, h = img.size

arr = np.array(img).astype(np.float64)
rgb = arr[:, :, :3]
alpha = (arr[:, :, 3] > 128)

# 1. Clean background patches (blue desk, brown chair)
is_blue_desk = (rgb[:, :, 2] > rgb[:, :, 0] + 35) & (rgb[:, :, 2] > 70) & (alpha)
y_indices, x_indices = np.indices(alpha.shape)
is_chair_patch = (x_indices > 1240) & (y_indices > 650) & (y_indices < 850) & (rgb[:, :, 0] > 90) & (alpha)

alpha[is_blue_desk] = False
alpha[is_chair_patch] = False

# 2. De-fringe white halo
eroded_alpha = binary_erosion(alpha, iterations=2)
border_band = alpha & ~binary_erosion(eroded_alpha, iterations=3)
brightness = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
is_white_fringe = border_band & (brightness > 115)
rgb[is_white_fringe] = [30.0, 26.0, 28.0]

smooth_alpha = gaussian_filter(eroded_alpha.astype(np.float64), sigma=1.0)
smooth_alpha = np.clip(smooth_alpha, 0.0, 1.0)

# Site background: #1d2021 = (29, 32, 33)
site_bg = np.array([29.0, 32.0, 33.0])
blended_rgb = rgb * smooth_alpha[:, :, np.newaxis] + site_bg * (1.0 - smooth_alpha[:, :, np.newaxis])
blended_rgb = np.clip(blended_rgb, 0.0, 255.0).astype(np.uint8)
alpha_out = (smooth_alpha * 255.0).astype(np.uint8)

# Scale for Hero ASCII art: 64 columns wide
term_w = 64
aspect = h / float(w)
term_h = int(term_w * aspect)
if term_h % 2 != 0:
    term_h += 1

blended_pil = Image.fromarray(blended_rgb, "RGB")
term_img = blended_pil.resize((term_w, term_h), Image.Resampling.LANCZOS)
term_alpha = Image.fromarray(alpha_out).resize((term_w, term_h), Image.Resampling.BILINEAR)

html_rows = []
for y in range(0, term_h, 2):
    row_spans = []
    for x in range(term_w):
        a1 = term_alpha.getpixel((x, y))
        a2 = term_alpha.getpixel((x, y + 1))
        
        r1, g1, b1 = term_img.getpixel((x, y))
        r2, g2, b2 = term_img.getpixel((x, y + 1))
        
        if a1 < 25 and a2 < 25:
            row_spans.append('<span class="ap-bg">&nbsp;</span>')
        elif a1 >= 25 and a2 < 25:
            row_spans.append(f'<span style="color:rgb({r1},{g1},{b1})">▀</span>')
        elif a1 < 25 and a2 >= 25:
            row_spans.append(f'<span style="color:rgb({r2},{g2},{b2})">▄</span>')
        else:
            row_spans.append(f'<span style="color:rgb({r1},{g1},{b1});background:rgb({r2},{g2},{b2})">▀</span>')
    html_rows.append("".join(row_spans))

ascii_html = "".join(f'<div class="ap-row">{r}</div>' for r in html_rows)

with open("ASCII ART/hero_ascii.html", "w", encoding="utf-8") as f:
    f.write(ascii_html)

print("Generated ASCII ART/hero_ascii.html! Rows:", len(html_rows), "Cols:", term_w)
