import os
from fastapi import Depends, Path
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as DbField, Session, create_engine

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
    size: int | None = Field(default=None, title="set current size of frame")


class Settings(SQLModel, table=True):
    id: int = DbField(default=1, primary_key=True)
    sleepInterval: str
    orientation: str = "horizontal"
    size: int

class Models(SQLModel, table=True):
    size: int = DbField(primary_key=True)
    length: int
    width: int