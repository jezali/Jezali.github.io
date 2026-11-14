from PIL import Image, ImageDraw

# Generate 64x64 pixel art 👾 favicon
size = 64
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 11x8 space invader matrix
matrix = [
    "  #     #  ",
    "   #   #   ",
    "  #######  ",
    " ## ### ## ",
    "###########",
    "# ####### #",
    "# #     # #",
    "   ## ##   ",
]

scale = 5
offset_x = (size - (11 * scale)) // 2
offset_y = (size - (8 * scale)) // 2

# Gruvbox purple/magenta #d3869b or aqua #8ec07c
color = (211, 134, 155, 255) # #d3869b

for y, row in enumerate(matrix):
    for x, ch in enumerate(row):
        if ch == '#':
            x0 = offset_x + x * scale
            y0 = offset_y + y * scale
            draw.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=color)

img.save("favicon.png")
print("Saved favicon.png with 👾 pixel art!")

# Also generate favicon.svg
svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <text y=".9em" font-size="90">👾</text>
</svg>"""
with open("favicon.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print("Saved favicon.svg!")
