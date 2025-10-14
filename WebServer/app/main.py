import os
import random
import uvicorn
import numpy as np
from pathlib import Path as OsPath
from typing import Annotated, Literal

from dotenv import load_dotenv

from PIL import Image
from pillow_heif import register_heif_opener

from fastapi import Depends, FastAPI, HTTPException, Body, Path
from pydantic import BaseModel, Field
from fastapi.responses import Response

from sqlmodel import Field as DbField, Session, SQLModel, create_engine

load_dotenv()
register_heif_opener()

photo_dir = os.environ["PHOTO_DIR"]
sql_url = os.environ["DATABASE_URL"]

engine = create_engine(sql_url)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

DeviceIdType = Annotated[int, Path(title="The ID of the item to get")]
OrientationType = Literal["horizontal", "vertical"]


class SettingInput(BaseModel):
    sleepInterval: str | None = Field(
        default=None,
        title="sleepInterval in HH:MM:SS",
        min_length=8,
        max_length=8,
        pattern=r"^\d{2}:\d{2}:\d{2}$",
    )
    orientation: OrientationType | None = Field(
        default=None, title="set current orientation of frame"
    )


class Settings(SQLModel, table=True):
    id: int | None = DbField(default=None, primary_key=True)
    sleepInterval: str
    orientation: str = "horizontal"


app = FastAPI()

# Define the extensions to search for
exts = {".jpg", ".jpeg", ".png", ".heic"}
root = OsPath(photo_dir)
image_candidates = [p for p in root.rglob("*") if p.suffix.lower() in exts]

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


def get_image_buffer(image, saturation=0.5):
    """Copy an image to the display.

    :param image: PIL image to copy, must be 800x480
    :param saturation: Saturation for quantization palette - higher value results in a more saturated image

    """
    image = resize_and_truncate(image)

    if image.size != (image.width, image.height):
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
    new_buff = remap[
        np.array(image, dtype=np.uint8).reshape((frameSize["rows"], frameSize["cols"]))
    ]

    buf = new_buff.flatten()

    buf = ((buf[::2] << 4) & 0xF0) | (buf[1::2] & 0x0F)

    result = buf.astype("uint8").tolist()
    return result


def parse_sleep_time(sleep_time: str):
    hours, minutes, seconds = sleep_time.split(":")
    print(int(hours), int(minutes), int(seconds))
    return [int(hours), int(minutes), int(seconds)]


def traverse_directory(path):
    for root, dirs, files in os.walk(path):
        if len(files):
            file_name = random.choice(files)
            if file_name.lower().endswith(exts):
                full_file_path = os.path.join(root, file_name)
                return full_file_path
        shuffled_list = dirs[:]  # Create a shallow copy
        random.shuffle(shuffled_list)
        for dir in shuffled_list:
            full_dir_path = os.path.join(root, dir)
            random_file = traverse_directory(full_dir_path)
            if len(random_file):
                return random_file
        return ""


def get_random_image_traverse():
    """Recursively finds all JPG, JPEG, PNG, and HEIC files using the glob module."""
    image_path = traverse_directory(photo_dir)

    if not len(image_path):
        raise FileNotFoundError(
            "No .jpeg, .jpg, .png, or .heic files found in the directory."
        )

    print(image_path)
    return image_path


def get_random_image_orientation(orientation: OrientationType):
    if not len(image_candidates):
        return None
    correct_orientation = False
    while not correct_orientation:
        chosen_image = random.choice(image_candidates)
        with Image.open(chosen_image) as image:
            correct_orientation = check_orientation(image, orientation)
            if correct_orientation:
                return chosen_image
    return None


def check_orientation(image, orientation: OrientationType):
    width, height = image.size
    if orientation == "horizontal":
        return width > height
    elif orientation == "vertical":
        return height > width


# returns header bytes followed by image buffer
@app.get("/getFrameBuffer/{device_id}")
def get_frame_buffer(device_id: DeviceIdType, session: SessionDep):
    frame_settings = session.get(Settings, device_id)
    if not frame_settings:
        raise HTTPException(status_code=404, detail="Frame settings not found")

    sleep_interval = frame_settings.sleepInterval
    orientation = frame_settings.orientation

    sleep_header = parse_sleep_time(sleep_interval)

    chosen_image = get_random_image_orientation(orientation)
    if not chosen_image:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    complete_buf = sleep_header + get_image_buffer(chosen_image)

    # imageString = np.array2string(image, precision=2, separator=', ', suppress_small=True)
    data = bytes(complete_buf)
    # return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream")
    return Response(content=data, media_type="application/octet-stream")


@app.get("/getSleep/{device_id}")
def get_sleep(device_id: DeviceIdType, session: SessionDep):
    frame_settings = session.get(Settings, device_id)
    sleep_time = parse_sleep_time(frame_settings.sleepInterval)
    return sleep_time


@app.get("/getImagePath/{orientation}")
def get_image(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation(orientation)
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    return image_path


@app.get("/getImageList/{orientation}")
def get_image_list(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation("horizontal")
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    res_list = []
    with Image.open(image_path) as image:
        res_list = get_image_buffer(image)
    return res_list


# requires the form of HH:MM:SS
@app.post("/setSettings/{device_id}")
def set_db_sleep(
    device_id: DeviceIdType,
    new_settings: Annotated[SettingInput, Body()],
    session: SessionDep,
):
    print(new_settings)
    current_settings = session.get(Settings, device_id)
    if not current_settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    if new_settings.sleepInterval:
        current_settings.sleepInterval = new_settings.sleepInterval
    if new_settings.orientation:
        current_settings.orientation = new_settings.orientation

    session.add(current_settings)
    session.commit()
    return "Done"


@app.post("/initializeDB")
def initalize_db(session: SessionDep):
    SQLModel.metadata.create_all(engine)
    setting = Settings(sleepInterval="00:00:45")
    session.add(setting)

    session.commit()
    return "Done"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
