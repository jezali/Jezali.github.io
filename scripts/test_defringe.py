import os
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion, gaussian_filter

DIR = "ASCII ART"
input_path = os.path.join(DIR, "better-face_cutout.png")

img = Image.open(input_path).convert("RGBA")
arr = np.array(img).astype(np.float64)
rgb = arr[:, :, :3]
alpha = (arr[:, :, 3] > 128).astype(bool)

# 1. Erode binary mask by 2 iterations to cleanly strip the white wall fringe
eroded_alpha = binary_erosion(alpha, iterations=2)

# 2. De-fringe: anywhere on the outer border where brightness is high, pull inward color
# Find border band
border_band = alpha & ~binary_erosion(eroded_alpha, iterations=3)

# For pixels in border band that have high brightness (white wall bleed), clamp them to dark hair tone
brightness = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
is_white_fringe = border_band & (brightness > 120)

# Replace white fringe pixels with dark curl tone
rgb[is_white_fringe] = [35.0, 30.0, 32.0]

# 3. Soft Gaussian smoothing on eroded alpha for silky smooth blending with #1d2021
smooth_alpha = gaussian_filter(eroded_alpha.astype(np.float64), sigma=1.0)
smooth_alpha = np.clip(smooth_alpha, 0.0, 1.0)

# Site background: #1d2021
site_bg = np.array([29.0, 32.0, 33.0])

# Blend with site background
blended_rgb = rgb * smooth_alpha[:, :, np.newaxis] + site_bg * (1.0 - smooth_alpha[:, :, np.newaxis])
blended_rgb = np.clip(blended_rgb, 0.0, 255.0).astype(np.uint8)

# Save test preview
Image.fromarray(blended_rgb, "RGB").save("ASCII ART/test_defringed.jpg", quality=95)
print("Saved test_defringed.jpg")
