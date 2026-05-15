from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class AppBase(BaseModel):
    name: str
    tag: Optional[str] = None


class AppCreate(AppBase):
    pass


class AppUpdate(BaseModel):
    name: Optional[str] = None


class AppResponse(AppBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VersionBase(BaseModel):
    version: str
    build_number: int
    force_update: bool = False
    update_url: Optional[str] = None
    message: Optional[str] = None
    title: Optional[str] = None


class VersionCreate(VersionBase):
    app_id: int


class VersionUpdate(BaseModel):
    version: Optional[str] = None
    build_number: Optional[int] = None
    force_update: Optional[bool] = None
    update_url: Optional[str] = None
    message: Optional[str] = None
    title: Optional[str] = None


class VersionResponse(VersionBase):
    id: int
    app_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
