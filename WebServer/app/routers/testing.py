import os
from fastapi import APIRouter, HTTPException

from ..models import Settings, DeviceIdType, OrientationType, SessionDep
from ..image_processing import get_buffers, process_image, get_image_buffer
from ..utils import get_random_image_orientation, parse_sleep_time

photo_dir = os.environ["PHOTO_DIR"]

router = APIRouter(
    prefix="/testing",
    tags=["testing"],
    responses={404: {"description": "Not found"}},
)

@router.get("/getSleep/{device_id}")
def get_sleep(device_id: DeviceIdType, session: SessionDep):
    frame_settings = session.get(Settings, device_id)
    sleep_time = parse_sleep_time(frame_settings.sleepInterval)
    return sleep_time


@router.get("/getImagePath/{orientation}")
def get_image(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation(orientation, photo_dir)
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    return image_path


@router.get("/v1/getImageBuffer/{orientation}")
def get_image_list(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation(orientation, photo_dir)
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    image = process_image(image_path, (1200, 1600))
    image_buffer = get_image_buffer(image, (1200, 1600))
    return {
        "path": image_path,
        "size": (1200, 1600),
        "length": len(image_buffer)
    }

@router.get("/v2/getImageBuffer/{orientation}")
def get_png_image_list(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation(orientation, photo_dir)
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    image = process_image(image_path, (1200, 1600))
    image_buffers = get_buffers(image, 2, "tall")
    return {
        "path": image_path,
        "size": (1200, 1600),
        "lengths": [len(buffer) for buffer in image_buffers]
    }

@router.get("/showImg/{orientation}")
def show_image(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation(orientation, photo_dir)
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    image = process_image(image_path, (1200, 1600))
    image.show()