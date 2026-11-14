#!/usr/bin/env python3
"""
High-Fidelity Terminal Art Generator from HQ.jpg
Generates TrueColor ANSI, Monochrome CRT (Amber & Phosphor Green),
High-Resolution Braille matrix, and Unicode block art.
"""

import os
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

INPUT_IMAGE = "ASCII ART/cropped_head_shoulder.jpg"
OUTPUT_DIR = "ASCII ART"

# Ensure cropped image exists from HQ.jpg
if not os.path.exists(INPUT_IMAGE):
    orig = Image.open("HQ.jpg")
    cropped = orig.crop((740, 70, 2120, 1600))
    cropped.save(INPUT_IMAGE, quality=95)

def generate_halfblock_ansi(img, width, color_mode="truecolor"):
    """
    Renders 2 pixels per character cell using Unicode Upper Half Block '▀' (U+2580).
    Top pixel -> foreground ANSI sequence.
    Bottom pixel -> background ANSI sequence.
    """
    aspect = img.height / img.width
    height = int(width * aspect)
    if height % 2 != 0:
        height += 1
        
    resized = img.resize((width, height), Image.Resampling.LANCZOS)
    enhancer = ImageEnhance.Contrast(resized)
    resized = enhancer.enhance(1.2)
    
    lines = []
    for y in range(0, height, 2):
        row = []
        for x in range(width):
            r1, g1, b1 = resized.getpixel((x, y))
            r2, g2, b2 = resized.getpixel((x, y + 1))
            
            if color_mode == "truecolor":
                row.append(f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀")
            elif color_mode == "amber":
                lum1 = int(0.299 * r1 + 0.587 * g1 + 0.114 * b1)
                lum2 = int(0.299 * r2 + 0.587 * g2 + 0.114 * b2)
                # Gruvbox Amber / Orange scale (#fe8019)
                ar1, ag1, ab1 = int(lum1 * 0.99), int(lum1 * 0.50), int(lum1 * 0.10)
                ar2, ag2, ab2 = int(lum2 * 0.99), int(lum2 * 0.50), int(lum2 * 0.10)
                row.append(f"\033[38;2;{ar1};{ag1};{ab1}m\033[48;2;{ar2};{ag2};{ab2}m▀")
            elif color_mode == "green":
                lum1 = int(0.299 * r1 + 0.587 * g1 + 0.114 * b1)
                lum2 = int(0.299 * r2 + 0.587 * g2 + 0.114 * b2)
                # Phosphor Green scale (#b8bb26)
                gr1, gg1, gb1 = int(lum1 * 0.72), int(lum1 * 0.73), int(lum1 * 0.15)
                gr2, gg2, gb2 = int(lum2 * 0.72), int(lum2 * 0.73), int(lum2 * 0.15)
                row.append(f"\033[38;2;gr1;gg1;gb1m\033[48;2;gr2;gg2;gb2m▀".replace("gr1", str(gr1)).replace("gg1", str(gg1)).replace("gb1", str(gb1)).replace("gr2", str(gr2)).replace("gg2", str(gg2)).replace("gb2", str(gb2)))
        row.append("\033[0m")
        lines.append("".join(row))
    return "\n".join(lines)

def generate_braille(img, width=110, invert=False):
    """
    Renders with 2x4 dot matrix per character cell using Unicode Braille Patterns (U+2800..U+28FF).
    Gives ultra-high spatial resolution for crisp eye, pupil, curl, and facial detail.
    """
    gray = img.convert("L")
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(1.6)
    enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=2))
    
    aspect = gray.height / gray.width
    # 2 dots per column, 4 dots per row
    dot_w = width * 2
    dot_h = int(dot_w * aspect)
    # Round dot_h up to multiple of 4
    if dot_h % 4 != 0:
        dot_h += 4 - (dot_h % 4)
        
    resized = enhanced.resize((dot_w, dot_h), Image.Resampling.LANCZOS)
    dithered = resized.convert("1") # Floyd-Steinberg dithering
    
    # Braille dot mapping
    dots_pos = [
        (0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04),
        (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20),
        (0, 3, 0x40), (1, 3, 0x80)
    ]
    
    lines = []
    for y in range(0, dot_h, 4):
        row = []
        for x in range(0, dot_w, 2):
            byte = 0
            for dx, dy, mask in dots_pos:
                if x + dx < dot_w and y + dy < dot_h:
                    pixel = dithered.getpixel((x + dx, y + dy))
                    # If invert is False: dark pixel = dot. If invert is True: light pixel = dot.
                    condition = (pixel == 0) if not invert else (pixel != 0)
                    if condition:
                        byte |= mask
            row.append(chr(0x2800 + byte))
        lines.append("".join(row))
    return "\n".join(lines)

def generate_blocks_hd(img, width=100):
    """
    Unicode 5-level shaded blocks with contrast curve and sharpening
    """
    gray = img.convert("L")
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(1.4)
    enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1.5, percent=140, threshold=2))
    
    aspect = gray.height / gray.width
    height = int(width * aspect * 0.52)
    resized = enhanced.resize((width, height), Image.Resampling.LANCZOS)
    
    RAMP = " ░▒▓█"
    ramp_len = len(RAMP)
    
    lines = []
    for y in range(height):
        row = []
        for x in range(width):
            val = resized.getpixel((x, y))
            idx = int((val / 256.0) * ramp_len)
            idx = max(0, min(idx, ramp_len - 1))
            row.append(RAMP[idx])
        lines.append("".join(row))
    return "\n".join(lines)

def generate_ascii_rich(img, width=120):
    """
    Rich 70-shade ASCII ramp with high detail
    """
    gray = img.convert("L")
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(1.45)
    enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=2))
    
    aspect = gray.height / gray.width
    height = int(width * aspect * 0.52)
    resized = enhanced.resize((width, height), Image.Resampling.LANCZOS)
    
    RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1]
    ramp_len = len(RAMP)
    
    lines = []
    for y in range(height):
        row = []
        for x in range(width):
            val = resized.getpixel((x, y))
            idx = int((val / 256.0) * ramp_len)
            idx = max(0, min(idx, ramp_len - 1))
            row.append(RAMP[idx])
        lines.append("".join(row))
    return "\n".join(lines)

def main():
    img_rgb = Image.open(INPUT_IMAGE).convert("RGB")
    
    # 1. TrueColor ANSI (80 cols and 100 cols)
    ans_truecolor = generate_halfblock_ansi(img_rgb, width=80, color_mode="truecolor")
    with open(os.path.join(OUTPUT_DIR, "face_truecolor.ans"), "w", encoding="utf-8") as f:
        f.write(ans_truecolor)
        
    ans_amber = generate_halfblock_ansi(img_rgb, width=80, color_mode="amber")
    with open(os.path.join(OUTPUT_DIR, "face_amber_terminal.ans"), "w", encoding="utf-8") as f:
        f.write(ans_amber)

    ans_green = generate_halfblock_ansi(img_rgb, width=80, color_mode="green")
    with open(os.path.join(OUTPUT_DIR, "face_green_terminal.ans"), "w", encoding="utf-8") as f:
        f.write(ans_green)

    # 2. High-resolution Braille matrices (Normal and Inverted for dark backgrounds)
    braille_normal = generate_braille(img_rgb, width=100, invert=False)
    with open(os.path.join(OUTPUT_DIR, "face_braille_dark_dots.txt"), "w", encoding="utf-8") as f:
        f.write(braille_normal)

    braille_inverted = generate_braille(img_rgb, width=100, invert=True)
    with open(os.path.join(OUTPUT_DIR, "face_braille_light_dots.txt"), "w", encoding="utf-8") as f:
        f.write(braille_inverted)

    # 3. Unicode Shaded Blocks
    blocks_hd = generate_blocks_hd(img_rgb, width=90)
    with open(os.path.join(OUTPUT_DIR, "face_blocks_hd.txt"), "w", encoding="utf-8") as f:
        f.write(blocks_hd)

    # 4. Rich ASCII (110 chars)
    ascii_rich = generate_ascii_rich(img_rgb, width=110)
    with open(os.path.join(OUTPUT_DIR, "face_ascii_hd.txt"), "w", encoding="utf-8") as f:
        f.write(ascii_rich)

    # 5. Terminal CLI Runner script (view_in_terminal.py)
    runner_code = r'''#!/usr/bin/env python3
"""
Interactive Terminal Viewer for Jezali's Face Art
Run: python "ASCII ART/view_in_terminal.py"
"""
import sys
import os

if sys.platform == "win32":
    # Enable ANSI escape sequences on Windows PowerShell / cmd
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

DIR = os.path.dirname(os.path.abspath(__file__))

def show(filename, title):
    path = os.path.join(DIR, filename)
    if os.path.exists(path):
        print("\033[2J\033[H", end="") # clear screen
        print(f"\033[1;33m--- {title} ---\033[0m\n")
        with open(path, "r", encoding="utf-8") as f:
            print(f.read())
        print(f"\n\033[1;30m[End of {filename}]\033[0m")
    else:
        print(f"File not found: {filename}")

def menu():
    while True:
        print("\033[1;36m==========================================")
        print("   JEZALI // TERMINAL FACE ART VIEWER     ")
        print("==========================================\033[0m")
        print("1) TrueColor Photo ANSI (Photorealistic)")
        print("2) Cyberpunk Amber CRT Terminal")
        print("3) Phosphor Green CRT Terminal")
        print("4) Ultra-High-Res Braille Matrix")
        print("5) Unicode Shaded Blocks ( ░▒▓█)")
        print("6) High-Detail ASCII")
        print("q) Quit\n")
        choice = input("Select mode (1-6, q): ").strip().lower()
        if choice == "1":
            show("face_truecolor.ans", "TrueColor 24-bit Photo Half-Blocks")
        elif choice == "2":
            show("face_amber_terminal.ans", "Cyberpunk Amber Terminal (Gruvbox)")
        elif choice == "3":
            show("face_green_terminal.ans", "Phosphor Green Terminal")
        elif choice == "4":
            show("face_braille_dark_dots.txt", "Braille Matrix (2x4 dots/cell)")
        elif choice == "5":
            show("face_blocks_hd.txt", "Unicode Shaded Blocks")
        elif choice == "6":
            show("face_ascii_hd.txt", "High-Detail ASCII")
        elif choice in ("q", "exit"):
            break
        input("\nPress [Enter] to return to menu...")

if __name__ == "__main__":
    menu()
'''
    with open(os.path.join(OUTPUT_DIR, "view_in_terminal.py"), "w", encoding="utf-8") as f:
        f.write(runner_code)

    # 6. HTML Terminal UI Simulation (face_terminal.html)
    # We can embed the TrueColor HTML spans directly for browser viewing!
    html_spans = []
    resized_80 = img_rgb.resize((80, int(80 * (img_rgb.height / img_rgb.width))), Image.Resampling.LANCZOS)
    enh = ImageEnhance.Contrast(resized_80)
    resized_80 = enh.enhance(1.2)
    h80 = resized_80.height
    if h80 % 2 != 0:
        h80 -= 1
        
    for y in range(0, h80, 2):
        row_spans = []
        for x in range(80):
            r1, g1, b1 = resized_80.getpixel((x, y))
            r2, g2, b2 = resized_80.getpixel((x, y + 1))
            row_spans.append(f'<span style="color:rgb({r1},{g1},{b1});background-color:rgb({r2},{g2},{b2})">▀</span>')
        html_spans.append("".join(row_spans))
    truecolor_html = "<br>".join(html_spans)
    
    terminal_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jezali // Terminal Face Render</title>
    <style>
        :root {{
            --bg0: #1d2021;
            --bg1: #282828;
            --fg: #ebdbb2;
            --amber: #fe8019;
            --green: #b8bb26;
            --border: #504945;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg0);
            color: var(--fg);
            font-family: 'IBM Plex Mono', 'Cascadia Code', 'Courier New', monospace;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }}
        header {{
            text-align: center;
            margin-bottom: 1.25rem;
        }}
        h1 {{
            color: var(--amber);
            font-size: 1.2rem;
            letter-spacing: 0.08em;
            margin-bottom: 4px;
        }}
        .sub {{
            font-size: 0.8rem;
            color: #928374;
        }}
        .nav-tabs {{
            display: flex;
            gap: 8px;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            justify-content: center;
        }}
        button {{
            background: var(--bg1);
            color: var(--fg);
            border: 1px solid var(--border);
            padding: 6px 14px;
            font-family: inherit;
            font-size: 0.8rem;
            cursor: pointer;
        }}
        button:hover {{
            border-color: var(--amber);
            color: var(--amber);
        }}
        button.active {{
            background: var(--amber);
            color: var(--bg0);
            font-weight: bold;
        }}
        .terminal-box {{
            position: relative;
            background: #141617;
            border: 2px solid var(--border);
            padding: 1.25rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            max-width: 95vw;
            overflow: auto;
        }}
        .crt-scanlines {{
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(to bottom, transparent 0px, transparent 2px, rgba(0,0,0,0.2) 2px, rgba(0,0,0,0.2) 4px);
            pointer-events: none;
        }}
        .render-area {{
            font-family: inherit;
            font-size: 11px;
            line-height: 1.0;
            letter-spacing: 0;
            white-space: pre;
            display: inline-block;
        }}
        .amber-tint {{
            filter: sepia(1) saturate(5) hue-rotate(345deg);
        }}
        .green-tint {{
            filter: sepia(1) saturate(5) hue-rotate(75deg);
        }}
        .braille-text {{
            font-size: 11px;
            line-height: 1.0;
            letter-spacing: 0.05em;
            color: var(--amber);
        }}
    </style>
</head>
<body>
    <header>
        <h1>JEZALI // TERMINAL FACE RENDER</h1>
        <div class="sub">Source: HQ.jpg &bull; Head &amp; Shoulders Crop &bull; TrueColor Half-Blocks &amp; Braille Matrix</div>
    </header>

    <div class="nav-tabs">
        <button class="active" onclick="showMode('truecolor', this)">TrueColor Photo</button>
        <button onclick="showMode('amber', this)">Amber Terminal</button>
        <button onclick="showMode('green', this)">Phosphor Green</button>
        <button onclick="showMode('braille', this)">Braille Matrix</button>
        <button onclick="showMode('blocks', this)">Unicode Blocks</button>
    </div>

    <div class="terminal-box">
        <div class="crt-scanlines"></div>
        <div id="display-area" class="render-area">{truecolor_html}</div>
    </div>

    <script>
        const brailleContent = `{braille_normal.replace("`", "")}`;
        const blocksContent = `{blocks_hd.replace("`", "")}`;
        const truecolorHtml = `{truecolor_html}`;

        function showMode(mode, btn) {{
            document.querySelectorAll('.nav-tabs button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const area = document.getElementById('display-area');
            area.className = 'render-area';

            if (mode === 'truecolor') {{
                area.innerHTML = truecolorHtml;
            }} else if (mode === 'amber') {{
                area.innerHTML = truecolorHtml;
                area.classList.add('amber-tint');
            }} else if (mode === 'green') {{
                area.innerHTML = truecolorHtml;
                area.classList.add('green-tint');
            }} else if (mode === 'braille') {{
                area.innerHTML = brailleContent;
                area.classList.add('braille-text');
            }} else if (mode === 'blocks') {{
                area.innerHTML = blocksContent;
                area.classList.add('braille-text');
            }}
        }}
    </script>
</body>
</html>"""

    with open(os.path.join(OUTPUT_DIR, "face_terminal.html"), "w", encoding="utf-8") as f:
        f.write(terminal_html_content)

    print("Successfully generated all terminal art files in 'ASCII ART/':")
    for f in os.listdir(OUTPUT_DIR):
        sz = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f" - {f} ({sz} bytes)")

if __name__ == "__main__":
    main()
