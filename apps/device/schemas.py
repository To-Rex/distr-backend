from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    name: str = Field(..., max_length=100)
    device_uuid: str = Field(..., max_length=255)
    platform: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    os_version: Optional[str] = Field(None, max_length=50)
    app_version: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    last_seen: Optional[datetime] = None
    user_id: Optional[int] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    device_uuid: Optional[str] = Field(None, max_length=255)
    platform: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    os_version: Optional[str] = Field(None, max_length=50)
    app_version: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    last_seen: Optional[datetime] = None
    user_id: Optional[int] = None


class DeviceResponse(DeviceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
