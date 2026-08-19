import os
import uvicorn
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Annotated

from dotenv import load_dotenv

from pillow_heif import register_heif_opener

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import  SQLModel, select

from .constants import origins
from .image_processing import process_image, get_image_buffer
from .utils import get_random_image_orientation, parse_sleep_time
from .models import Settings, SessionDep, OrientationType, DeviceIdType, Models, engine, SettingInput

load_dotenv()
register_heif_opener()

photo_dir = os.environ["PHOTO_DIR"]

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# endpoint called by the frame
# returns header bytes followed by image buffer
@app.get("/getFrameBuffer/{device_id}")
def get_frame_buffer(device_id: DeviceIdType, session: SessionDep):
    frame_settings = session.get(Settings, device_id)
    if not frame_settings:
        raise HTTPException(status_code=404, detail="Frame settings not found")
    frame_model = session.get(Models, frame_settings.size)
    if not frame_model:
        raise HTTPException(status_code=404, detail="Frame model not found")

    frame_size = (frame_model.length, frame_model.width)
    sleep_interval = frame_settings.sleepInterval
    orientation = frame_settings.orientation

    image_path = get_random_image_orientation(orientation)
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")

    ny_time = datetime.now(ZoneInfo("America/New_York"))
    formatted_time = ny_time.strftime("%Y-%m-%d %I:%M:%S%p")
    print(formatted_time, "-- Device", device_id, "will display:", image_path)
    # header bytes
    sleep_header = parse_sleep_time(sleep_interval)
    image = process_image(image_path, frame_size)
    complete_buf = sleep_header + get_image_buffer(image, frame_size)

    # imageString = np.array2string(image, precision=2, separator=', ', suppress_small=True)
    data = bytes(complete_buf)
    # return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream")
    return Response(content=data, media_type="application/octet-stream")


@app.get("/admin/getDevices")
def get_devices(session: SessionDep):
    devices = session.exec(select(Settings)).all()
    dev_list = [device.id for device in devices]
    return dev_list


@app.get("/admin/getDeviceSettings/{device_id}")
def get_device_settings(device_id: DeviceIdType, session: SessionDep):
    device_settings = session.get(Settings, device_id)
    if not device_settings:
        raise HTTPException(status_code=404, detail="Device settings not found")
    return device_settings


# requires the form of HH:MM:SS
@app.post("/admin/setDeviceSettings/{device_id}")
def set_device_settings(
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
    image = process_image(image_path, (128, 128))
    image_buffer = get_image_buffer(image, (128, 128))
    return image_buffer

@app.get("/testing/showImg/{orientation}")
def show_image(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation(orientation)
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    image = process_image(image_path, (128, 128))
    image.show()

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
