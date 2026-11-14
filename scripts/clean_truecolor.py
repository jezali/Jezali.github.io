#!/usr/bin/env python3
"""
Generate Transparent-Background TrueColor Terminal Art
"""
import os
from PIL import Image, ImageDraw, ImageEnhance

DIR = "ASCII ART"
os.makedirs(DIR, exist_ok=True)

# 1. Load HQ image and crop strictly head & shoulders
hq_img = Image.open("HQ.jpg")
cropped = hq_img.crop((740, 70, 2120, 1600))
w, h = cropped.size

# High-precision boundary polygon for head, curls, face, neck & shoulder
pts = [
    # Bottom left (chest / shoulder)
    (0, h),
    (0, 1150),
    (80, 1070),
    (140, 1000),
    (170, 940),
    (200, 870), # beard lower left
    # Left hair curls (tight fit, removing all blue desk and wall)
    (185, 800),
    (170, 730),
    (165, 660),
    (125, 590),
    (115, 510),
    (155, 430),
    (220, 360),
    (285, 295),
    (365, 255),
    (450, 230),
    (535, 238),
    (615, 248),
    (705, 242),
    (795, 248),
    (875, 262),
    (955, 292),
    (1035, 342),
    (1100, 400),
    (1155, 480),
    (1190, 560),
    (1210, 645),
    (1205, 735),
    (1175, 835),
    (1135, 925),
    (1085, 1015),
    (1015, 1105),
    (935, 1185),
    (875, 1230),
    # Neck and right shoulder
    (855, 1265),
    (870, 1315),
    (905, 1370),
    (950, 1430),
    (1000, 1490),
    (1040, h),
]

mask = Image.new("L", (w, h), 0)
draw = ImageDraw.Draw(mask)
draw.polygon(pts, fill=255)

# Save high-res cutout with transparent background
cutout_rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
cutout_rgba.paste(cropped.convert("RGBA"), (0, 0), mask)
cutout_rgba.save(os.path.join(DIR, "face_cutout.png"))

# 2. Resize for Terminal (80 columns wide)
target_width = 80
aspect = h / w
target_height = int(target_width * aspect)
if target_height % 2 != 0:
    target_height += 1

# Resize both image and mask
resized_img = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
enhancer = ImageEnhance.Contrast(resized_img)
resized_img = enhancer.enhance(1.2) # crisp contrast

resized_mask = mask.resize((target_width, target_height), Image.Resampling.BILINEAR)

# 3. Generate TrueColor Half-Blocks with Transparent Background
lines = []
html_rows = []

for y in range(0, target_height, 2):
    row_ansi = []
    row_html = []
    
    last_fg = None
    last_bg = None
    
    for x in range(target_width):
        m1 = resized_mask.getpixel((x, y)) > 128
        m2 = resized_mask.getpixel((x, y + 1)) > 128
        
        r1, g1, b1 = resized_img.getpixel((x, y))
        r2, g2, b2 = resized_img.getpixel((x, y + 1))
        
        if not m1 and not m2:
            # Completely background
            row_ansi.append("\033[0m ")
            row_html.append('<span class="bg-pixel">&nbsp;</span>')
            last_fg = None
            last_bg = None
        elif m1 and not m2:
            # Top half only
            row_ansi.append(f"\033[0m\033[38;2;{r1};{g1};{b1}m▀")
            row_html.append(f'<span style="color:rgb({r1},{g1},{b1})">▀</span>')
            last_fg = (r1, g1, b1)
            last_bg = None
        elif not m1 and m2:
            # Bottom half only
            row_ansi.append(f"\033[0m\033[38;2;{r2};{g2};{b2}m▄")
            row_html.append(f'<span style="color:rgb({r2},{g2},{b2})">▄</span>')
            last_fg = (r2, g2, b2)
            last_bg = None
        else:
            # Both top and bottom are subject
            row_ansi.append(f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀")
            row_html.append(f'<span style="color:rgb({r1},{g1},{b1});background-color:rgb({r2},{g2},{b2})">▀</span>')
            last_fg = (r1, g1, b1)
            last_bg = (r2, g2, b2)
            
    row_ansi.append("\033[0m")
    lines.append("".join(row_ansi))
    html_rows.append("".join(row_html))

# Write ANSI file
ansi_content = "\n".join(lines)
with open(os.path.join(DIR, "face_truecolor.ans"), "w", encoding="utf-8") as f:
    f.write(ansi_content)

# 4. Generate clean standalone runner script (view_in_terminal.py)
runner = r'''#!/usr/bin/env python3
"""
Prints Jezali's TrueColor terminal face art with transparent background
"""
import sys
import os

if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    # Enable Virtual Terminal Processing (VT100 / ANSI escape sequences)
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

DIR = os.path.dirname(os.path.abspath(__file__))
ans_path = os.path.join(DIR, "face_truecolor.ans")

if os.path.exists(ans_path):
    print("\033[2J\033[H", end="") # Clear screen and move cursor home
    with open(ans_path, "r", encoding="utf-8") as f:
        print(f.read())
    print("\033[0m")
else:
    print(f"Error: {ans_path} not found.")
'''
with open(os.path.join(DIR, "view_in_terminal.py"), "w", encoding="utf-8") as f:
    f.write(runner)

# 5. Generate beautiful HTML Terminal Viewer
html_body = "<br>".join(html_rows)
html_page = f"""<!DOCTYPE html>
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
            background: repeating-linear-gradient(to bottom, transparent 0px, transparent 2px, rgba(0,0,0,0.15) 2px, rgba(0,0,0,0.15) 4px);
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
        <div class="sub">Head, Hair &amp; Shoulder &bull; Background Pixels Removed &bull; 24-bit Half-Blocks</div>
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
    f.write(html_page)

# 6. Delete all the old / non-truecolor files as requested
keep_files = {
    "face_truecolor.ans",
    "face_terminal.html",
    "face_cutout.png",
    "view_in_terminal.py",
}

deleted = []
for fname in os.listdir(DIR):
    if fname not in keep_files:
        path = os.path.join(DIR, fname)
        if os.path.isfile(path):
            os.remove(path)
            deleted.append(fname)

print("Finished processing!")
print(f"Kept files in '{DIR}/': {list(keep_files)}")
print(f"Deleted {len(deleted)} unwanted files: {deleted}")
