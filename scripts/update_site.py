import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

with open("ASCII ART/hero_ascii.html", "r", encoding="utf-8") as f:
    ascii_rows = f.read()

# Replace <img id="hero-avatar" ...> with <div id="hero-avatar" class="hero-ascii">...</div>
old_img_pattern = r'<img id="hero-avatar"[^>]*>'
new_avatar_div = f'<div id="hero-avatar" class="hero-ascii" title="Jezali TrueColor Terminal Portrait (7 clicks for Akira cut)">{ascii_rows}</div>'

html = re.sub(old_img_pattern, new_avatar_div, html)

# Also update Contact section to include Email as PIN 1
old_contact = r'''                    <div class="contact-connector">
                        <div class="connector-label">// HEADER J1 PINOUT \(CLICK VALUE TO COPY\)</div>

                        <!-- Pin 1: Telegram -->
                        <div class="pinout-row">
                            <span class="pin-id">PIN 1 \[TG\]</span>
                            <a class="pin-val" href="https://t.me/unsaltedchickenbreast" target="_blank" rel="noopener noreferrer">@unsaltedchickenbreast</a>
                            <button class="copy-trigger" data-copy="@unsaltedchickenbreast" data-confirm="confirm-tg" title="Copy Telegram handle">\[copy\]</button>
                            <span id="confirm-tg" class="copied-badge">copied</span>
                        </div>

                        <!-- Pin 2: GitHub -->
                        <div class="pinout-row">
                            <span class="pin-id">PIN 2 \[GH\]</span>
                            <a class="pin-val" href="https://github.com/Jezali" target="_blank" rel="noopener noreferrer">github.com/Jezali</a>
                            <button class="copy-trigger" data-copy="https://github.com/Jezali" data-confirm="confirm-gh" title="Copy GitHub URL">\[copy\]</button>
                            <span id="confirm-gh" class="copied-badge">copied</span>
                        </div>
                    </div>'''

new_contact = '''                    <div class="contact-connector">
                        <div class="connector-label">// HEADER J1 PINOUT (CLICK VALUE TO COPY)</div>

                        <!-- Pin 1: Email -->
                        <div class="pinout-row">
                            <span class="pin-id">PIN 1 [EM]</span>
                            <a class="pin-val" href="mailto:jezali.jakaloo@protonmail.com">jezali.jakaloo@protonmail.com</a>
                            <button class="copy-trigger" data-copy="jezali.jakaloo@protonmail.com" data-confirm="confirm-em" title="Copy email address">[copy]</button>
                            <span id="confirm-em" class="copied-badge">copied</span>
                        </div>

                        <!-- Pin 2: Telegram -->
                        <div class="pinout-row">
                            <span class="pin-id">PIN 2 [TG]</span>
                            <a class="pin-val" href="https://t.me/unsaltedchickenbreast" target="_blank" rel="noopener noreferrer">@unsaltedchickenbreast</a>
                            <button class="copy-trigger" data-copy="@unsaltedchickenbreast" data-confirm="confirm-tg" title="Copy Telegram handle">[copy]</button>
                            <span id="confirm-tg" class="copied-badge">copied</span>
                        </div>

                        <!-- Pin 3: GitHub -->
                        <div class="pinout-row">
                            <span class="pin-id">PIN 3 [GH]</span>
                            <a class="pin-val" href="https://github.com/Jezali" target="_blank" rel="noopener noreferrer">github.com/Jezali</a>
                            <button class="copy-trigger" data-copy="https://github.com/Jezali" data-confirm="confirm-gh" title="Copy GitHub URL">[copy]</button>
                            <span id="confirm-gh" class="copied-badge">copied</span>
                        </div>
                    </div>'''

html = re.sub(old_contact, new_contact, html)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Updated index.html successfully with ASCII art and email!")
