import os
from PIL import Image
from rembg import remove, new_session

# Load HQ.jpg
orig = Image.open("HQ.jpg")

# Crop head and shoulders with natural margin around the curls
# x: 680 to 2140, y: 50 to 1640
crop_box = (680, 50, 2140, 1640)
cropped = orig.crop(crop_box)
cropped.save("ASCII ART/hq_cropped_temp.png")

print("Processing background removal with neural AI matting...")
# Use isnet-general-use or u2net
session = new_session("u2net")
result = remove(
    cropped,
    session=session,
    alpha_matting=True,
    alpha_matting_foreground_threshold=240,
    alpha_matting_background_threshold=15,
    alpha_matting_erode_size=10
)

result.save("ASCII ART/ai_cutout.png")
print("Saved ASCII ART/ai_cutout.png successfully!")
