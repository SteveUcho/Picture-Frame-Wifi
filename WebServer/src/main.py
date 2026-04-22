import os
import random
import uvicorn
import requests
import numpy as np
from typing import Annotated, Literal

from dotenv import load_dotenv

from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS, GPSTAGS
from pillow_heif import register_heif_opener

from fastapi import Depends, FastAPI, HTTPException, Body, Path
from pydantic import BaseModel, Field
from fastapi.responses import Response

from sqlmodel import Field as DbField, Session, SQLModel, create_engine

load_dotenv()
register_heif_opener()

photo_dir = os.environ["PHOTO_DIR"]
sql_url = os.environ["DATABASE_URL"]
user_agent = os.environ["USER_AGENT"]

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
exts = (".jpg", ".jpeg", ".png", ".heic")

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

def get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0
    if ref in ['S', 'W']:
        return -(degrees + minutes + seconds)
    return degrees + minutes + seconds


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


def process_image(image_path, saturation=0.5, target_size=(800, 480)):
    """Copy an image to the display.

    :param image: PIL image to copy, must be 800x480
    :param saturation: Saturation for quantization palette - higher value results in a more saturated image

    """
    image: Image.Image = Image.open(image_path).convert("RGBA")
    image = resize_and_truncate(image)

    if image.size != (image.width, image.height):
        raise ValueError(
            f"Image must be ({frameSize['rows']}x{frameSize['cols']}) pixels!"
        )

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

    exif_data = image.getexif()

    location_text = get_location_text(exif_data)
    name_text = image_path.split("/")[2].split("U")[0]
    date_text = get_date_text(exif_data)
    line_list = [name_text]
    if date_text:
        line_list.append(date_text)
    second_line = " - ".join(line_list)

    text_image = draw_text(location_text, second_line, target_size[0])
    image_anchor = (40, target_size[1] - 60 - 45)
    image.paste(text_image, image_anchor, text_image)

    # All other image should be quantized and dithered
    palette = palette_blend(saturation)
    palette_image.putpalette(palette)

    dither = Image.Dither.FLOYDSTEINBERG
    image_complete = image.convert("RGB").quantize(6, palette=palette_image, dither=dither)

    return image_complete

def get_date_text(exif_data):
    DATE_TAG = next(
        tag for tag, name in TAGS.items() if name == "DateTime"
    )

    datetime = exif_data.get_ifd(DATE_TAG)
    if not datetime:
        return
    date = datetime.split(" ")[0].split(":")
    dateString = "/".join([date[1], date[2], date[0]])

    return dateString

def get_location_text(exif_data):
    GPSINFO_TAG = next(
        tag for tag, name in TAGS.items() if name == "GPSInfo"
    )

    gps_info = {}
    for key in exif_data.get_ifd(GPSINFO_TAG):
        sub_tag_name = GPSTAGS.get(key, key)
        gps_info[sub_tag_name] = exif_data.get_ifd(GPSINFO_TAG)[key]

    if not gps_info:
        return ""

    lat = get_decimal_from_dms(gps_info['GPSLatitude'], gps_info['GPSLatitudeRef'])
    lon = get_decimal_from_dms(gps_info['GPSLongitude'], gps_info['GPSLongitudeRef'])

    payload = {"lat": lat, "lon": lon, "format": "jsonv2"}
    headers = {"User-Agent": user_agent}
    req = requests.request("GET","https://nominatim.openstreetmap.org/reverse", params=payload, headers=headers)
    geo_data = req.json()

    if (req.status_code == requests.codes.ok):
        city = geo_data["address"].get("city")
        if not city:
            city = geo_data["address"].get("village")
        country = geo_data["address"]["country"]
        if (city == "New York"):
            suburb = geo_data["address"]["suburb"]
            return suburb + ", NY"
        elif (country == "United States"):
            state = geo_data["address"]["state"]
            return city + ", " + state
        else:
            return city + ", " + country
    return ""

def draw_text(first_line, second_line, max_length):
    # create an image
    text_image = Image.new("RGBA", (max_length, 60), (255, 255, 255, 0))

    # get first line font
    fnt1 = ImageFont.truetype("GrenzeFont/static/Grenze-Bold.ttf", 50)
    # get second line font
    fnt2 = ImageFont.truetype("BaskervvilleFont/static/Baskervville-Regular.ttf", 25)

    # start a drawing context
    drawing = ImageDraw.Draw(text_image)

    # draw first line
    drawing.text((0, 0), first_line, font=fnt1, fill=(255, 255, 255, 255), anchor="lt", stroke_width=2, stroke_fill="black")
    # draw second line
    drawing.text((0, 40), second_line, font=fnt2, fill=(255, 255, 255, 255), anchor="lt", stroke_width=2, stroke_fill="black")

    return text_image


def get_image_buffer(image):
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
    return [int(hours), int(minutes), int(seconds)]


def traverse_directory(path):
    results = []
    for root, test, files in os.walk(path):
        for file_name in files:
            if file_name.lower().endswith(exts):
                full_file_path = os.path.join(root, file_name)
                results.append(full_file_path)
    return results


def find_files_with_exts():
    """Recursively finds all JPG, JPEG, PNG, and HEIC files using the glob module."""
    image_candidates = traverse_directory(photo_dir)

    if not len(image_candidates):
        raise FileNotFoundError(
            "No .jpeg, .jpg, .png, or .heic files found in the directory."
        )

    return image_candidates


# returns absolute image path
def get_random_image_orientation(orientation: OrientationType):
    image_candidates = find_files_with_exts()
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


# endpoint called by the frame
# returns header bytes followed by image buffer
@app.get("/getFrameBuffer/{device_id}")
def get_frame_buffer(device_id: DeviceIdType, session: SessionDep):
    frame_settings = session.get(Settings, device_id)
    if not frame_settings:
        raise HTTPException(status_code=404, detail="Frame settings not found")

    sleep_interval = frame_settings.sleepInterval
    orientation = frame_settings.orientation

    image_path = get_random_image_orientation(orientation)
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")

    print("Device", device_id, "will display:", image_path)
    # header bytes
    sleep_header = parse_sleep_time(sleep_interval)
    image = process_image(image_path)
    complete_buf = sleep_header + get_image_buffer(image)

    # imageString = np.array2string(image, precision=2, separator=', ', suppress_small=True)
    data = bytes(complete_buf)
    # return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream")
    return Response(content=data, media_type="application/octet-stream")


# requires the form of HH:MM:SS
@app.post("/setSettings/{device_id}")
def set_db_sleep(
    device_id: DeviceIdType,
    new_settings: Annotated[SettingInput, Body()],
    session: SessionDep,
):
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


@app.post("/init/initializeDB")
def initalize_db(session: SessionDep):
    SQLModel.metadata.create_all(engine)
    setting = Settings(sleepInterval="00:00:45", orientation="horizontal")
    session.add(setting)

    session.commit()
    return "Done"


#
# testing endpoints
#
@app.get("/testing/getSleep/{device_id}")
def get_sleep(device_id: DeviceIdType, session: SessionDep):
    frame_settings = session.get(Settings, device_id)
    sleep_time = parse_sleep_time(frame_settings.sleepInterval)
    return sleep_time


@app.get("/testing/getImagePath/{orientation}")
def get_image(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation(orientation)
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    return image_path


@app.get("/testing/getImageBuffer/{orientation}")
def get_image_list(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation("horizontal")
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    image_buffer = []
    image = process_image(image_path)
    image_buffer = get_image_buffer(image)
    return image_buffer

@app.get("/testing/showImg/{orientation}")
def show_image(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation("horizontal")
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    image = process_image(image_path)
    image.show()
    return

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
