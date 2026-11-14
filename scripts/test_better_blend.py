import os
import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import gaussian_filter

DIR = "ASCII ART"
input_path = os.path.join(DIR, "better-face_cutout.png")

img = Image.open(input_path).convert("RGBA")
w, h = img.size

arr = np.array(img).astype(np.float64)
rgb = arr[:, :, :3]
alpha = arr[:, :, 3] / 255.0

# 1. Soft anti-aliasing / natural edge feathering on the alpha channel
# A gentle 1.2px sigma gaussian blur on the binary alpha removes all harsh jagged pixel edges
# while preserving the exact shape of the curls.
soft_alpha = gaussian_filter(alpha, sigma=1.2)
# Re-scale slightly so inner hair stays 100% solid
soft_alpha = np.clip((soft_alpha - 0.05) / 0.90, 0.0, 1.0)

# 2. Site background color: #1d2021 = (29, 32, 33)
site_bg = np.array([29.0, 32.0, 33.0])

# Pre-blend with site background where alpha transitions into background
blended_rgb = rgb * soft_alpha[:, :, np.newaxis] + site_bg * (1.0 - soft_alpha[:, :, np.newaxis])
blended_rgb = np.clip(blended_rgb, 0.0, 255.0).astype(np.uint8)

# Save test preview composite on #1d2021 background
Image.fromarray(blended_rgb, "RGB").save("ASCII ART/better_preview_blended.jpg", quality=95)

# Save updated face_cutout.png (with smooth alpha channel)
alpha_out = (soft_alpha * 255.0).astype(np.uint8)
cutout_out = np.dstack([blended_rgb, alpha_out])
Image.fromarray(cutout_out, "RGBA").save(os.path.join(DIR, "face_cutout.png"))

print("Generated better_preview_blended.jpg and face_cutout.png")
