import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .constants import SATURATED_PALETTE, DESATURATED_PALETTE
from .image_utils import get_location_text, get_date_text

def rotate_image(image):
    width, height = image.size
    if height > width:
        return image.rotate(90)
    else:
        return image.rotate(180)


def resize_and_truncate(image, frame_size):
    """Resize the image to fit the target size and truncate symmetrically"""
    # Calculate the aspect ratio
    aspect_ratio = image.width / image.height
    target_aspect_ratio = frame_size[0] / frame_size[1]

    # Resize the image proportionally
    if aspect_ratio > target_aspect_ratio:
        # Resize by height and then truncate the width symmetrically
        resized_image = image.resize(
            (int(frame_size[1] * aspect_ratio), frame_size[1]), Image.LANCZOS
        )
        left_margin = (resized_image.width - frame_size[0]) // 2
        right_margin = (resized_image.width - frame_size[0] + 1) // 2
        top_margin = 0
        bottom_margin = 0

    else:
        # Resize by width and then truncate the height symmetrically
        resized_image = image.resize(
            (frame_size[0], int(frame_size[0] / aspect_ratio)), Image.LANCZOS
        )
        left_margin = 0
        right_margin = 0
        top_margin = (resized_image.height - frame_size[1]) // 2
        bottom_margin = (resized_image.height - frame_size[1] + 1) // 2

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


def process_image(image_path, frame_size):
    """Copy an image to the display.

    :param image_path: Path to the image file
    :param frame_size: Target size of the image (width, height)

    """
    saturation = 0.5
    image: Image.Image = Image.open(image_path).convert("RGBA")
    image = resize_and_truncate(image, frame_size)
    first_line, second_line = get_draw_text(image, image_path)
    image = add_text_to_image(image, frame_size, first_line, second_line)
    image = finalize_image(image, saturation)
    return image

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

def get_draw_text(image, image_path):
    exif_data = image.getexif()
    first_line = get_location_text(exif_data)
    name_text = image_path.split("/")[2].split("U")[0]
    date_text = get_date_text(exif_data)
    line_list = [name_text]
    if date_text:
        line_list.append(date_text)
    second_line = " - ".join(line_list)
    return first_line, second_line


def add_text_to_image(image, frame_size, first_line, second_line):
    text_image = draw_text(first_line, second_line, frame_size[0])
    image_anchor = (80, frame_size[1] - 60 - 45)
    image.paste(text_image, image_anchor, text_image)
    return image

def finalize_image(image, saturation=0.5):
    # Image size doesn't matter since it's just the palette we're using
    palette_image = Image.new("P", (1, 1))

    palette = palette_blend(saturation)
    palette_image.putpalette(palette)

    dither = Image.Dither.FLOYDSTEINBERG
    image_complete = image.convert("RGB").quantize(6, palette=palette_image, dither=dither)
    return image_complete



def draw_text(first_line, second_line, max_length):
    # create an image
    text_image = Image.new("RGBA", (max_length, 100), (255, 255, 255, 0))

    # get first line font
    # fnt1 = ImageFont.truetype("GrenzeFont/static/Grenze-Bold.ttf", 50)
    fnt1 = ImageFont.truetype("fonts/Murecho/Murecho-VariableFont_wght.ttf", 50)
    # get second line font
    # fnt2 = ImageFont.truetype("BaskervvilleFont/static/Baskervville-Regular.ttf", 35)
    fnt2 = ImageFont.truetype("fonts/Murecho/Murecho-VariableFont_wght.ttf", 35)

    # start a drawing context
    drawing = ImageDraw.Draw(text_image)

    # draw first line
    drawing.text((0, 0), first_line, font=fnt1, fill=(255, 255, 255, 255), anchor="lt", stroke_width=2, stroke_fill="black")
    # draw second line
    drawing.text((0, 40), second_line, font=fnt2, fill=(255, 255, 255, 255), anchor="lt", stroke_width=2, stroke_fill="black")

    return text_image


def get_image_buffer(image, frame_size):
    # Remap our sequential palette colours to display native (missing colour 4)
    remap = np.array([0, 1, 2, 3, 5, 6])
    new_buff = remap[
        np.array(image, dtype=np.uint8).reshape((frame_size[0], frame_size[1]))
    ]

    buf = new_buff.flatten()

    buf = ((buf[::2] << 4) & 0xF0) | (buf[1::2] & 0x0F)

    result = buf.astype("uint8").tolist()
    return result
