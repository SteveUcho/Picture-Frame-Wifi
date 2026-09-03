from sqlmodel import select
from typing import Annotated
from fastapi import APIRouter, Body, HTTPException

from ..models import Settings, DeviceIdType, SettingInput, SessionDep

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)


@router.get("/getDevices")
def get_devices(session: SessionDep):
    devices = session.exec(select(Settings)).all()
    # create list of devices with id and name
    dev_list = [{"id": device.id, "name": device.name, "model": f"{device.size}in ESP32-S3"} for device in devices]
    return dev_list


@router.get("/getDeviceSettings/{device_id}")
def get_device_settings(device_id: DeviceIdType, session: SessionDep):
    device_settings = session.get(Settings, device_id)
    if not device_settings:
        raise HTTPException(status_code=404, detail="Device settings not found")
    return device_settings


# requires the form of HH:MM:SS
@router.post("/setDeviceSettings/{device_id}")
def set_device_settings(
    device_id: DeviceIdType,
    settings_input: Annotated[SettingInput, Body()],
    session: SessionDep,
):
    current_settings = session.get(Settings, device_id)
    if not current_settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    for key, value in settings_input.model_dump(exclude_unset=True).items():
        setattr(current_settings, key, value)

    session.commit()
    return "Done"
