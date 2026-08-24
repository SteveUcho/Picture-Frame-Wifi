import os
import uvicorn
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from pillow_heif import register_heif_opener

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import  SQLModel

from .constants import origins
from .image_processing import process_image, get_image_buffer
from .utils import get_random_image_orientation, parse_sleep_time
from .models import Settings, SessionDep, DeviceIdType, Models, engine

from .routers import admin, testing

load_dotenv()
register_heif_opener()

photo_dir = os.environ["PHOTO_DIR"]

app = FastAPI()

app.include_router(admin.router)
app.include_router(testing.router)

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

    image_path = get_random_image_orientation(orientation, photo_dir)
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



@app.post("/init/initializeDB")
def initalize_db(session: SessionDep):
    SQLModel.metadata.create_all(engine)
    setting = Settings(sleepInterval="00:00:45", orientation="horizontal", size=8, name="First Device")
    model = Models(size=8, length=800, width=480)
    session.add(setting)
    session.add(model)

    session.commit()
    return "Done"


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
