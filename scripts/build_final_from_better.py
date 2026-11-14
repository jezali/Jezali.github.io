import os
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion, gaussian_filter

DIR = "ASCII ART"
input_path = os.path.join(DIR, "better-face_cutout.png")

img = Image.open(input_path).convert("RGBA")
w, h = img.size

arr = np.array(img).astype(np.float64)
rgb = arr[:, :, :3]
alpha = (arr[:, :, 3] > 128)

# 1. Clean background patches (blue desk on left, brown chair on right)
is_blue_desk = (rgb[:, :, 2] > rgb[:, :, 0] + 35) & (rgb[:, :, 2] > 70) & (alpha)
y_indices, x_indices = np.indices(alpha.shape)
is_chair_patch = (x_indices > 1240) & (y_indices > 650) & (y_indices < 850) & (rgb[:, :, 0] > 90) & (alpha)

alpha[is_blue_desk] = False
alpha[is_chair_patch] = False

# 2. Erode by 2 iterations to cleanly eliminate white wall halo
eroded_alpha = binary_erosion(alpha, iterations=2)

# De-fringe: clamp any bright edge pixels to dark curl tone
border_band = alpha & ~binary_erosion(eroded_alpha, iterations=3)
brightness = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
is_white_fringe = border_band & (brightness > 115)
rgb[is_white_fringe] = [30.0, 26.0, 28.0]

# 3. Soft Gaussian smoothing on alpha for silky smooth blending with #1d2021
smooth_alpha = gaussian_filter(eroded_alpha.astype(np.float64), sigma=1.0)
smooth_alpha = np.clip(smooth_alpha, 0.0, 1.0)

# Site background: #1d2021 = (29, 32, 33)
site_bg = np.array([29.0, 32.0, 33.0])

# Pre-blend with site background
blended_rgb = rgb * smooth_alpha[:, :, np.newaxis] + site_bg * (1.0 - smooth_alpha[:, :, np.newaxis])
blended_rgb = np.clip(blended_rgb, 0.0, 255.0).astype(np.uint8)

# Save updated face_cutout.png (high-res transparent PNG)
alpha_out = (smooth_alpha * 255.0).astype(np.uint8)
cutout_out = np.dstack([blended_rgb, alpha_out])
Image.fromarray(cutout_out, "RGBA").save(os.path.join(DIR, "face_cutout.png"))

# 4. Generate 24-bit TrueColor ANSI Half-Blocks (80 columns wide)
term_w = 80
aspect = h / float(w)
term_h = int(term_w * aspect)
if term_h % 2 != 0:
    term_h += 1

blended_pil = Image.fromarray(blended_rgb, "RGB")
term_img = blended_pil.resize((term_w, term_h), Image.Resampling.LANCZOS)
term_alpha = Image.fromarray(alpha_out).resize((term_w, term_h), Image.Resampling.BILINEAR)

lines = []
html_rows = []

for y in range(0, term_h, 2):
    row_ansi = []
    row_html = []
    
    for x in range(term_w):
        a1 = term_alpha.getpixel((x, y))
        a2 = term_alpha.getpixel((x, y + 1))
        
        r1, g1, b1 = term_img.getpixel((x, y))
        r2, g2, b2 = term_img.getpixel((x, y + 1))
        
        # Threshold: if both are background (< 20 alpha)
        if a1 < 20 and a2 < 20:
            row_ansi.append("\033[0m ")
            row_html.append('<span class="bg-pixel">&nbsp;</span>')
        elif a1 >= 20 and a2 < 20:
            row_ansi.append(f"\033[0m\033[38;2;{r1};{g1};{b1}m▀")
            row_html.append(f'<span style="color:rgb({r1},{g1},{b1})">▀</span>')
        elif a1 < 20 and a2 >= 20:
            row_ansi.append(f"\033[0m\033[38;2;{r2};{g2};{b2}m▄")
            row_html.append(f'<span style="color:rgb({r2},{g2},{b2})">▄</span>')
        else:
            row_ansi.append(f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀")
            row_html.append(f'<span style="color:rgb({r1},{g1},{b1});background-color:rgb({r2},{g2},{b2})">▀</span>')
            
    row_ansi.append("\033[0m")
    lines.append("".join(row_ansi))
    html_rows.append("".join(row_html))

ansi_text = "\n".join(lines)
with open(os.path.join(DIR, "face_truecolor.ans"), "w", encoding="utf-8") as f:
    f.write(ansi_text)

# 5. Save HTML Terminal Viewer
html_body = "<br>".join(html_rows)
html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jezali // TrueColor Terminal Portrait</title>
    <style>
        :root {{
            --bg: #1d2021;
            --term-bg: #1d2021;
            --accent: #fe8019;
            --fg: #ebdbb2;
            --border: #504945;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg);
            color: var(--fg);
            font-family: 'IBM Plex Mono', 'Cascadia Code', 'Courier New', monospace;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }}
        header {{
            text-align: center;
            margin-bottom: 1.5rem;
        }}
        h1 {{
            color: var(--accent);
            font-size: 1.3rem;
            letter-spacing: 0.08em;
            margin-bottom: 4px;
        }}
        .sub {{
            color: #928374;
            font-size: 0.85rem;
        }}
        .terminal-window {{
            position: relative;
            background: var(--term-bg);
            border: 2px solid var(--border);
            padding: 1.5rem 2rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.7);
            max-width: 95vw;
            overflow: auto;
        }}
        .terminal-header {{
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: #928374;
            padding-bottom: 10px;
            margin-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }}
        .dot-title {{
            color: var(--accent);
        }}
        .crt-scanlines {{
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(to bottom, transparent 0px, transparent 2px, rgba(0,0,0,0.12) 2px, rgba(0,0,0,0.12) 4px);
            pointer-events: none;
        }}
        .art-container {{
            font-size: 11px;
            line-height: 1.0;
            letter-spacing: 0;
            white-space: pre;
            display: inline-block;
            user-select: all;
        }}
        .bg-pixel {{
            background: transparent;
            color: transparent;
        }}
    </style>
</head>
<body>
    <header>
        <h1>JEZALI // TRUECOLOR TERMINAL PORTRAIT</h1>
        <div class="sub">Source: better-face_cutout.png &bull; De-fringed &amp; Blended to #1d2021 &bull; 80x78 Half-Blocks</div>
    </header>

    <div class="terminal-window">
        <div class="terminal-header">
            <span class="dot-title">TTY: /dev/ttyUSB0 &bull; 24-bit TrueColor Half-Blocks</span>
            <span>jezali@nightcity:~</span>
        </div>
        <div class="crt-scanlines"></div>
        <div class="art-container">{html_body}</div>
    </div>
</body>
</html>
"""
with open(os.path.join(DIR, "face_terminal.html"), "w", encoding="utf-8") as f:
    f.write(html_doc)

# 6. Save view_in_terminal.py
runner = r'''#!/usr/bin/env python3
"""
Prints Jezali's TrueColor Terminal Face Art (De-fringed & blended to site background)
Run: python "ASCII ART/view_in_terminal.py"
"""
import sys
import os

if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

DIR = os.path.dirname(os.path.abspath(__file__))
ans_file = os.path.join(DIR, "face_truecolor.ans")

if os.path.exists(ans_file):
    print("\033[2J\033[H", end="")
    with open(ans_file, "r", encoding="utf-8") as f:
        print(f.read())
    print("\033[0m")
else:
    print(f"File not found: {ans_file}")
'''
with open(os.path.join(DIR, "view_in_terminal.py"), "w", encoding="utf-8") as f:
    f.write(runner)

# 7. Clean up temporary test files
keep = {"face_truecolor.ans", "face_terminal.html", "view_in_terminal.py", "face_cutout.png", "better-face_cutout.png"}
for fname in os.listdir(DIR):
    if fname not in keep:
        p = os.path.join(DIR, fname)
        if os.path.isfile(p):
            os.remove(p)

print("Generated all TrueColor assets from better-face_cutout.png!")
print("Remaining files in ASCII ART:", os.listdir(DIR))
