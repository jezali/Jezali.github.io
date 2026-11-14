#!/usr/bin/env python3
"""
Convert face avatar image to high-fidelity ASCII art
Generates multiple resolutions and themes into 'ASCII ART/' directory.
"""

import os
from PIL import Image, ImageEnhance

INPUT_IMAGE = "avatar.png"
OUTPUT_DIR = "ASCII ART"

# Character density ramps
RAMP_CLASSIC = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1] # dark to light
RAMP_SHARP = "@%#*+=-:. "
RAMP_DARK_MODE = " .:-=+*#%@"
RAMP_BLOCKS = " ░▒▓█"

def image_to_ascii(image_path, width, ramp, contrast=1.35, brightness=1.0):
    img = Image.open(image_path).convert("L")
    
    # Monospace font aspect ratio correction (width:height ~ 1:0.52)
    aspect_ratio = img.height / img.width
    height = int(width * aspect_ratio * 0.52)
    resized = img.resize((width, height), Image.Resampling.LANCZOS)
    
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(resized)
        resized = enhancer.enhance(contrast)
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(resized)
        resized = enhancer.enhance(brightness)
        
    ramp_len = len(ramp)
    lines = []
    for y in range(height):
        row = []
        for x in range(width):
            pixel = resized.getpixel((x, y))
            idx = int((pixel / 256.0) * ramp_len)
            idx = max(0, min(idx, ramp_len - 1))
            row.append(ramp[idx])
        lines.append("".join(row))
    return "\n".join(lines)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Standard face ASCII art (75 chars wide)
    face_standard = image_to_ascii(INPUT_IMAGE, width=75, ramp=RAMP_SHARP, contrast=1.35)
    with open(os.path.join(OUTPUT_DIR, "face.txt"), "w", encoding="utf-8") as f:
        f.write(face_standard)
        
    # 2. Dark mode optimized (for black/dark terminal backgrounds)
    face_dark = image_to_ascii(INPUT_IMAGE, width=75, ramp=RAMP_DARK_MODE, contrast=1.35)
    with open(os.path.join(OUTPUT_DIR, "face_dark_mode.txt"), "w", encoding="utf-8") as f:
        f.write(face_dark)

    # 3. High detail version (110 chars wide)
    face_detailed = image_to_ascii(INPUT_IMAGE, width=110, ramp=RAMP_CLASSIC, contrast=1.4)
    with open(os.path.join(OUTPUT_DIR, "face_detailed.txt"), "w", encoding="utf-8") as f:
        f.write(face_detailed)

    # 4. Compact version (48 chars wide, for terminal banners or small windows)
    face_compact = image_to_ascii(INPUT_IMAGE, width=48, ramp=RAMP_SHARP, contrast=1.3)
    with open(os.path.join(OUTPUT_DIR, "face_compact.txt"), "w", encoding="utf-8") as f:
        f.write(face_compact)

    # 5. Shaded block version
    face_blocks = image_to_ascii(INPUT_IMAGE, width=64, ramp=RAMP_BLOCKS, contrast=1.35)
    with open(os.path.join(OUTPUT_DIR, "face_blocks.txt"), "w", encoding="utf-8") as f:
        f.write(face_blocks)

    # 6. Beautiful Cyberpunk/Gruvbox HTML Viewer
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jezali - Face ASCII Art</title>
    <style>
        :root {{
            --bg: #1d2021;
            --fg: #ebdbb2;
            --accent: #fe8019;
            --green: #b8bb26;
            --border: #504945;
        }}
        body {{
            background-color: var(--bg);
            color: var(--fg);
            font-family: 'IBM Plex Mono', 'Cascadia Code', 'Courier New', monospace;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        h1 {{
            color: var(--accent);
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
            letter-spacing: 0.05em;
        }}
        .sub {{
            color: #928374;
            font-size: 0.85rem;
            margin-bottom: 1.5rem;
        }}
        .controls {{
            margin-bottom: 1.5rem;
            display: flex;
            gap: 10px;
        }}
        button {{
            background: #282828;
            color: var(--fg);
            border: 1px solid var(--border);
            padding: 6px 14px;
            font-family: inherit;
            font-size: 0.85rem;
            cursor: pointer;
        }}
        button:hover {{
            border-color: var(--accent);
            color: var(--accent);
        }}
        button.active {{
            background: var(--accent);
            color: var(--bg);
            font-weight: bold;
        }}
        pre {{
            font-family: inherit;
            line-height: 1.0;
            letter-spacing: 0.06em;
            font-size: 10px;
            background: #282828;
            padding: 1.5rem;
            border: 1px solid var(--border);
            white-space: pre;
            overflow-x: auto;
            max-width: 95vw;
        }}
        .amber {{ color: #fe8019; }}
        .green {{ color: #b8bb26; }}
        .white {{ color: #ebdbb2; }}
    </style>
</head>
<body>
    <h1>JEZALI // FACE ASCII ART</h1>
    <div class="sub">Generated from avatar.png &bull; Monospace Render</div>
    
    <div class="controls">
        <button onclick="setTheme('amber')" class="active">Amber Terminal</button>
        <button onclick="setTheme('green')">Phosphor Green</button>
        <button onclick="setTheme('white')">Gruvbox Light</button>
    </div>

    <pre id="ascii-display" class="amber">{face_dark}</pre>

    <script>
        function setTheme(theme) {{
            document.querySelectorAll('button').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            const pre = document.getElementById('ascii-display');
            pre.className = theme;
        }}
    </script>
</body>
</html>"""

    with open(os.path.join(OUTPUT_DIR, "face_viewer.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated 5 ASCII variations + HTML viewer in '{OUTPUT_DIR}/':")
    for f in os.listdir(OUTPUT_DIR):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f" - {f} ({size} bytes)")

if __name__ == "__main__":
    main()
