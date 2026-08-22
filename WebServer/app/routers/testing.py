import os
from fastapi import APIRouter, HTTPException

from ..models import Settings, DeviceIdType, OrientationType, SessionDep
from ..image_processing import process_image, get_image_buffer
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


@router.get("/getImageBuffer/{orientation}")
def get_image_list(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation(orientation, photo_dir)
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    image_buffer = []
    image = process_image(image_path, (128, 128))
    image_buffer = get_image_buffer(image, (128, 128))
    return image_buffer

@router.get("/showImg/{orientation}")
def show_image(orientation: OrientationType, session: SessionDep):
    image_path = get_random_image_orientation(orientation, photo_dir)
    if not image_path:
        raise HTTPException(status_code=404, detail="No pictures available to show")
    image = process_image(image_path, (128, 128))
    image.show()