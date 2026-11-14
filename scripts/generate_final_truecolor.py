import os
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
import pymatting

DIR = "ASCII ART"
os.makedirs(DIR, exist_ok=True)

# 1. Load HQ.jpg and crop head and shoulders
orig_img = Image.open("HQ.jpg")
# Crop coordinates: left=740, top=70, right=2120, bottom=1600
cropped = orig_img.crop((740, 70, 2120, 1600))
orig_w, orig_h = cropped.size

# Resolution for matting
w, h = 690, 765
img_pil = cropped.resize((w, h), Image.Resampling.LANCZOS)
scale_x = w / float(orig_w)
scale_y = h / float(orig_h)

# Refined Inner Foreground (Definite subject: face, eyes, nose, mouth, inner hair, chest)
raw_fg_pts = [
    (0, 1530),
    (0, 1200),
    (180, 1050),
    (230, 950),
    (250, 880), # beard
    (230, 800),
    (230, 720),
    (220, 600),
    (220, 500),
    (260, 420),
    (320, 360),
    (390, 310),
    (490, 290),
    (600, 300),
    (700, 295),
    (800, 300),
    (880, 320),
    (950, 360),
    (1000, 420),
    (1040, 500),
    (1060, 600),
    (1060, 700),
    (1040, 800),
    (1000, 900),
    (960, 1000),
    (900, 1100),
    (840, 1180),
    (820, 1260),
    (840, 1320),
    (880, 1380),
    (940, 1440),
    (1020, 1500),
    (1080, 1530),
]

# Refined Outer Envelope (encompassing all hair curls, strands, and shoulders)
raw_outer_pts = [
    (0, 1530),
    (0, 1100),
    (60, 1040),
    (120, 970),
    (170, 900),
    (160, 820),
    (130, 730),
    (80, 650),
    (60, 560),
    (70, 470),
    (110, 390),
    (170, 320),
    (250, 250),
    (340, 200),
    (430, 170),
    (530, 160),
    (630, 155),
    (730, 150),
    (820, 160),
    (910, 190),
    (990, 235),
    (1060, 295),
    (1120, 370),
    (1170, 450),
    (1210, 530),
    (1230, 620),
    (1225, 715),
    (1195, 815),
    (1155, 905),
    (1105, 995),
    (1035, 1085),
    (955, 1165),
    (895, 1220),
    (880, 1265),
    (900, 1315),
    (940, 1370),
    (1000, 1430),
    (1070, 1490),
    (1140, 1530),
]

fg_pts = [(int(x * scale_x), int(y * scale_y)) for (x, y) in raw_fg_pts]
outer_pts = [(int(x * scale_x), int(y * scale_y)) for (x, y) in raw_outer_pts]

image_rgb = np.array(img_pil).astype(np.float64) / 255.0

# Build Trimap
trimap = np.zeros((h, w), dtype=np.float64)

outer_mask = Image.new("L", (w, h), 0)
draw_outer = ImageDraw.Draw(outer_mask)
draw_outer.polygon(outer_pts, fill=128)
outer_arr = np.array(outer_mask).astype(np.float64) / 255.0
trimap[outer_arr > 0.2] = 0.5

fg_mask = Image.new("L", (w, h), 0)
draw_fg = ImageDraw.Draw(fg_mask)
draw_fg.polygon(fg_pts, fill=255)
fg_arr = np.array(fg_mask).astype(np.float64) / 255.0
trimap[fg_arr > 0.8] = 1.0

print("Computing fine curly hair alpha matte with PyMatting LKM...")
alpha = pymatting.estimate_alpha_lkm(image_rgb, trimap, laplacian_kwargs={"radius": 3, "epsilon": 1e-7})
alpha = np.clip(alpha, 0.0, 1.0)

# Soft natural alpha curve
alpha = np.power(alpha, 0.95)

# High-resolution cutouts
alpha_uint8 = (alpha * 255).astype(np.uint8)
img_uint8 = (image_rgb * 255).astype(np.uint8)
rgba = np.dstack([img_uint8, alpha_uint8])

cutout_pil = Image.fromarray(rgba, "RGBA")
cutout_pil.save(os.path.join(DIR, "face_cutout.png"))

# Pre-composite onto site background #1d2021 for natural dark terminal blending
site_bg = np.array([29.0, 32.0, 33.0]) / 255.0
blended_rgb = image_rgb * alpha[:, :, np.newaxis] + site_bg * (1.0 - alpha[:, :, np.newaxis])
blended_pil = Image.fromarray((blended_rgb * 255).astype(np.uint8), "RGB")

# 2. Generate TrueColor Half-Blocks for Terminal (80 cols wide)
term_w = 80
term_h = int(term_w * (h / float(w)))
if term_h % 2 != 0:
    term_h += 1

term_img = blended_pil.resize((term_w, term_h), Image.Resampling.LANCZOS)
# Sharpen facial features slightly for crystal clarity in terminal
enhancer = ImageEnhance.Contrast(term_img)
term_img = enhancer.enhance(1.18)

term_alpha = Image.fromarray(alpha_uint8).resize((term_w, term_h), Image.Resampling.BILINEAR)

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
        
        # If both are below threshold (background)
        if a1 < 25 and a2 < 25:
            row_ansi.append("\033[0m ")
            row_html.append('<span class="bg-pixel">&nbsp;</span>')
        elif a1 >= 25 and a2 < 25:
            # Top half only
            row_ansi.append(f"\033[0m\033[38;2;{r1};{g1};{b1}m▀")
            row_html.append(f'<span style="color:rgb({r1},{g1},{b1})">▀</span>')
        elif a1 < 25 and a2 >= 25:
            # Bottom half only
            row_ansi.append(f"\033[0m\033[38;2;{r2};{g2};{b2}m▄")
            row_html.append(f'<span style="color:rgb({r2},{g2},{b2})">▄</span>')
        else:
            # Both top and bottom are subject
            row_ansi.append(f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀")
            row_html.append(f'<span style="color:rgb({r1},{g1},{b1});background-color:rgb({r2},{g2},{b2})">▀</span>')
            
    row_ansi.append("\033[0m")
    lines.append("".join(row_ansi))
    html_rows.append("".join(row_html))

ansi_text = "\n".join(lines)
with open(os.path.join(DIR, "face_truecolor.ans"), "w", encoding="utf-8") as f:
    f.write(ansi_text)

# 3. Clean Runner Script (view_in_terminal.py)
runner = r'''#!/usr/bin/env python3
"""
Prints Jezali's TrueColor Terminal Face Art (Curls preserved & blended)
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

# 4. Clean HTML Terminal Page (face_terminal.html)
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
            --term-bg: #141617;
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
        <div class="sub">Head, Curls &amp; Shoulder &bull; Alpha Matting Blended to #1d2021 &bull; 24-bit Half-Blocks</div>
    </header>

    <div class="terminal-window">
        <div class="terminal-header">
            <span class="dot-title">TTY: /dev/ttyUSB0 &bull; 80x88px Half-Blocks</span>
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

# 5. Clean up any other files in ASCII ART
keep = {"face_truecolor.ans", "face_terminal.html", "view_in_terminal.py", "face_cutout.png"}
for fname in os.listdir(DIR):
    if fname not in keep:
        p = os.path.join(DIR, fname)
        if os.path.isfile(p):
            os.remove(p)

print("Generated beautiful TrueColor art with natural curl blending!")
print("Remaining files in ASCII ART:", os.listdir(DIR))
