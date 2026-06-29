from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    device_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class LocationCreate(LocationBase):
    user_id: int


class LocationUpdate(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    device_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    user_id: Optional[int] = None


class LocationRead(LocationBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LocationBatchItem(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    device_name: Optional[str] = Field(None, max_length=100)
    speed: Optional[float] = 0.0
    bearing: Optional[float] = 0.0
    accuracy: Optional[float] = 0.0
    altitude: Optional[float] = 0.0
    timestamp: Optional[datetime] = None


class LocationBatchRequest(BaseModel):
    locations: List[LocationBatchItem]
