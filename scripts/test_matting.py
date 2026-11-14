import numpy as np
from PIL import Image, ImageDraw
import pymatting

# 1. Definite Foreground Polygon (inside the face, beard, chest, and central hair mass)
raw_fg_pts = [
    (50, 1530),
    (50, 1200),
    (200, 1050),
    (240, 950),
    (260, 880), # beard
    (240, 800),
    (240, 720),
    (230, 600),
    (230, 500),
    (270, 420),
    (330, 360),
    (400, 310),
    (500, 290),
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
    (840, 1340),
    (870, 1400),
    (910, 1460),
    (950, 1530),
]

# 2. Outer Boundary Polygon (enveloping all curly hair curls and edges)
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
    (875, 1265),
    (890, 1315),
    (920, 1370),
    (965, 1430),
    (1015, 1490),
    (1055, 1530),
]

# Load HQ.jpg and crop
orig_img = Image.open("HQ.jpg")
cropped = orig_img.crop((740, 70, 2120, 1600))
orig_w, orig_h = cropped.size

# Scale to 552x612 for fast, high-quality matting
w, h = 552, 612
img_pil = cropped.resize((w, h), Image.Resampling.LANCZOS)
scale_x = w / float(orig_w)
scale_y = h / float(orig_h)

fg_pts = [(int(x * scale_x), int(y * scale_y)) for (x, y) in raw_fg_pts]
outer_pts = [(int(x * scale_x), int(y * scale_y)) for (x, y) in raw_outer_pts]

image_rgb = np.array(img_pil).astype(np.float64) / 255.0

# Build Trimap:
trimap = np.zeros((h, w), dtype=np.float64)

# Draw unknown region (0.5) inside outer_pts
outer_mask = Image.new("L", (w, h), 0)
draw_outer = ImageDraw.Draw(outer_mask)
draw_outer.polygon(outer_pts, fill=128)
outer_arr = np.array(outer_mask).astype(np.float64) / 255.0
trimap[outer_arr > 0.2] = 0.5

# Draw foreground region (1.0) inside fg_pts
fg_mask = Image.new("L", (w, h), 0)
draw_fg = ImageDraw.Draw(fg_mask)
draw_fg.polygon(fg_pts, fill=255)
fg_arr = np.array(fg_mask).astype(np.float64) / 255.0
trimap[fg_arr > 0.8] = 1.0

print("Estimating alpha matte with PyMatting (LKM)...")
alpha = pymatting.estimate_alpha_lkm(image_rgb, trimap, laplacian_kwargs={"radius": 3, "epsilon": 1e-7})
alpha = np.clip(alpha, 0.0, 1.0)

# Soft gamma curve on alpha to keep hair strands solid while soft at edges
alpha = np.power(alpha, 0.9)

# Composite onto Gruvbox #1d2021 (rgb(29, 32, 33)) to verify how it blends with the site!
site_bg = np.array([29.0, 32.0, 33.0]) / 255.0
comp_rgb = image_rgb * alpha[:, :, np.newaxis] + site_bg * (1.0 - alpha[:, :, np.newaxis])

# Save transparent PNG
alpha_uint8 = (alpha * 255).astype(np.uint8)
img_uint8 = (image_rgb * 255).astype(np.uint8)
rgba = np.dstack([img_uint8, alpha_uint8])
Image.fromarray(rgba, "RGBA").save("ASCII ART/matting_cutout.png")

# Save composite for preview
comp_uint8 = (comp_rgb * 255).astype(np.uint8)
Image.fromarray(comp_uint8, "RGB").save("ASCII ART/matting_preview.jpg")

print("Done! Saved matting_cutout.png and matting_preview.jpg")
