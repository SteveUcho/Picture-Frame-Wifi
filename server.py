import uvicorn

from fastapi import FastAPI
from fastapi.responses import Response

# from fastapi.responses import StreamingResponse
# import io
import numpy as np
from PIL import Image

import os
import random

app = FastAPI()

frameSize = {
    "rows": 800,
    "cols": 480,
}

SATURATED_PALETTE = [
    [0, 0, 0],
    [161, 164, 165],
    [208, 190, 71],
    [156, 72, 75],
    [61, 59, 94],
    [58, 91, 70],
    [255, 255, 255],
]

DESATURATED_PALETTE = [
    [0, 0, 0],
    [255, 255, 255],
    [255, 255, 0],
    [255, 0, 0],
    [0, 0, 255],
    [0, 255, 0],
    [255, 255, 255],
]

# 6-color palette for GDEP073E01 Spectra E6 display
palette = [
    (0, 0, 0),  # Black
    (255, 255, 255),  # White
    (255, 255, 0),  # Yellow
    (255, 0, 0),  # Red
    (0, 0, 255),  # Blue
    (0, 255, 0),  # Green
]

def rotate_image(image):
    width, height = image.size
    if height > width:
        return image.rotate(90)
    else:
        return image.rotate(180)

def resize_and_truncate(image, target_size=(800, 480)):
    """Resize the image to fit the target size and truncate symmetrically"""
    # Calculate the aspect ratio
    aspect_ratio = image.width / image.height
    target_aspect_ratio = target_size[0] / target_size[1]

    # Resize the image proportionally
    if aspect_ratio > target_aspect_ratio:
        # Resize by height and then truncate the width symmetrically
        resized_image = image.resize(
            (int(target_size[1] * aspect_ratio), target_size[1]), Image.LANCZOS
        )
        left_margin = (resized_image.width - target_size[0]) // 2
        right_margin = (resized_image.width - target_size[0] + 1) // 2
        top_margin = 0
        bottom_margin = 0

    else:
        # Resize by width and then truncate the height symmetrically
        resized_image = image.resize(
            (target_size[0], int(target_size[0] / aspect_ratio)), Image.LANCZOS
        )
        left_margin = 0
        right_margin = 0
        top_margin = (resized_image.height - target_size[1]) // 2
        bottom_margin = (resized_image.height - target_size[1] + 1) // 2

    # Truncate symmetrically from both sides to fit the target size
    truncated_image = resized_image.crop(
        (
            left_margin,
            top_margin,
            resized_image.width - right_margin,
            resized_image.height - bottom_margin,
        )
    )
    return truncated_image


def palette_blend(saturation, dtype="uint8"):
    saturation = float(saturation)
    palette = []
    for i in range(6):
        rs, gs, bs = [c * saturation for c in SATURATED_PALETTE[i]]
        rd, gd, bd = [c * (1.0 - saturation) for c in DESATURATED_PALETTE[i]]
        if dtype == "uint8":
            palette += [int(rs + rd), int(gs + gd), int(bs + bd)]
        if dtype == "uint24":
            palette += [(int(rs + rd) << 16) | (int(gs + gd) << 8) | int(bs + bd)]
    return palette


def set_image(file, saturation=0.5):
    """Copy an image to the display.

    :param image: PIL image to copy, must be 800x480
    :param saturation: Saturation for quantization palette - higher value results in a more saturated image

    """
    image = Image.open(file)
    image = rotate_image(image)
    image = resize_and_truncate(image)

    if not image.size == (image.width, image.height):
        raise ValueError(
            f"Image must be ({frameSize['rows']}x{frameSize['cols']}) pixels!"
        )


    dither = Image.Dither.FLOYDSTEINBERG

    # Image size doesn't matter since it's just the palette we're using
    palette_image = Image.new("P", (1, 1))

    # if image.mode == "P":
    #     # Create a pure colour palette from DESATURATED_PALETTE
    #     palette = np.array(DESATURATED_PALETTE, dtype=np.uint8).flatten().tobytes()
    #     palette_image.putpalette(palette)

    #     # Assume that palette mode images with an unset palette use the
    #     # default colour order and "DESATURATED_PALETTE" pure colours
    #     if not image.palette.colors:
    #         image.putpalette(palette)

    #     # Assume that palette mode images with exactly six colours use
    #     # all the correct colours, but not exactly in the right order.
    #     if len(image.palette.colors) == 6:
    #         dither = Image.Dither.NONE
    # else:

    # All other image should be quantized and dithered
    palette = palette_blend(saturation)
    palette_image.putpalette(palette)

    image = image.convert("RGB").quantize(6, palette=palette_image, dither=dither)

    # Remap our sequential palette colours to display native (missing colour 4)
    remap = np.array([0, 1, 2, 3, 5, 6])
    newBuff = remap[
        np.array(image, dtype=np.uint8).reshape((frameSize["rows"], frameSize["cols"]))
    ]
    #     imageString = newBuff.tolist()
    #     json.dumps(imageString)
    #     return imageString

    # def show(buf, busy_wait=True):
    #     region = buf

    # buf = region.flatten()
    buf = newBuff.flatten()

    buf = ((buf[::2] << 4) & 0xF0) | (buf[1::2] & 0x0F)

    result = buf.astype("uint8").tolist()
    return result

def getRandomImage():
    # Your directory path here
    directory = "/Users/steveucho/Pictures/Photos Library.photoslibrary/resources/derivatives"

    all_entries = os.listdir(directory)
    folders = []

    for entry in all_entries:
        full_path = os.path.join(directory, entry)
        if os.path.isdir(full_path) and len(entry) == 1:
            folders.append(full_path)

    random_folder = random.choice(folders)

    # Get all JPEG/JPG files (non-recursive)
    jpeg_files = [
        f for f in os.listdir(random_folder) if f.lower().endswith((".jpeg", ".jpg"))
    ]

    if not jpeg_files:
        raise FileNotFoundError("No .jpeg or .jpg files found in the directory.")
    
    # Pick a random one
    random_file = random.choice(jpeg_files)
    image_path = os.path.join(random_folder, random_file)
    print(image_path)
    return image_path



@app.get("/")
def read_root():
    random_file = getRandomImage()

    buf = set_image(random_file)
    # imageString = np.array2string(image, precision=2, separator=', ', suppress_small=True)
    data = bytes(buf)
    # return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream")
    return Response(content=data, media_type="application/octet-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
