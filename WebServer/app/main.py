import os
import random
import uvicorn
import numpy as np
from typing import Annotated

from PIL import Image
from pillow_heif import register_heif_opener

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import Response

from sqlmodel import Field, Session, SQLModel, create_engine, select

register_heif_opener()

photo_dir = os.environ["PHOTO_DIR"]
sql_url = os.environ["DATABASE_URL"]

engine = create_engine(sql_url)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


class Settings(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sleepInterval: str


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

    buf = newBuff.flatten()

    buf = ((buf[::2] << 4) & 0xF0) | (buf[1::2] & 0x0F)

    result = buf.astype("uint8").tolist()
    return result


def get_sleep_time(session):
    frameSettings = session.get(Settings, 1)
    if not frameSettings:
        raise HTTPException(status_code=404, detail="Frame settings not found")

    hours, minutes, seconds = frameSettings.sleepInterval.split(":")
    print(int(hours), int(minutes), int(seconds))
    return [int(hours), int(minutes), int(seconds)]


# Define the extensions to search for
extensions = (".jpg", ".jpeg", ".png", ".heic")


def traverse_directory(path):
    for root, dirs, files in os.walk(path):
        if len(files):
            file_name = random.choice(files)
            if file_name.lower().endswith(extensions):
                full_file_path = os.path.join(root, file_name)
                return full_file_path
        shuffled_list = dirs[:]  # Create a shallow copy
        random.shuffle(shuffled_list)
        for dir in shuffled_list:
            full_dir_path = os.path.join(root, dir)
            randomFile = traverse_directory(full_dir_path)
            if len(randomFile):
                return randomFile
        return ""


def getRandomImage():
    """Recursively finds all JPG, JPEG, PNG, and HEIC files using the glob module."""
    image_path = traverse_directory(photo_dir)

    if not len(image_path):
        raise FileNotFoundError(
            "No .jpeg, .jpg, .png, or .heic files found in the directory."
        )

    print(image_path)
    return image_path


@app.get("/")
def read_root(session: SessionDep):
    random_image = getRandomImage()

    buf = set_image(random_image)
    sleepHeader = get_sleep_time(session)

    buf = sleepHeader + buf

    # imageString = np.array2string(image, precision=2, separator=', ', suppress_small=True)
    data = bytes(buf)
    # return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream")
    return Response(content=data, media_type="application/octet-stream")


@app.get("/getSleep")
def getSleep(session: SessionDep):
    frameSettings = get_sleep_time(session)
    return frameSettings


@app.get("/getImage")
def getImage(session: SessionDep):
    imagePath = getRandomImage()
    return imagePath


@app.get("/getImageList")
def getImageList(session: SessionDep):
    imagePath = getRandomImage()
    res_list = set_image(imagePath)
    return res_list


@app.post("/initializeDB")
def initalizeDB(session: SessionDep):
    SQLModel.metadata.create_all(engine)
    setting = Settings(sleepInterval="00:00:45")
    session.add(setting)

    session.commit()
    return "Done"


class SettingInput(BaseModel):
    sleepInterval: str


# requires the form of HH:MM:SS
@app.post("/setSleep")
def setDBSleep(settings: SettingInput, session: SessionDep):
    print(settings)
    if len(settings.sleepInterval) != 8 or len(settings.sleepInterval.split(":")) != 3:
        raise HTTPException(status_code=400, detail="Bad input")
    current_settings = session.get(Settings, 1)
    if not current_settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    current_settings.sleepInterval = settings
    session.add(current_settings)
    session.commit()
    return "Done"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
