from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    title: str = Field(..., max_length=250)
    message: Optional[str] = Field(None, max_length=2000)
    date: Optional[str] = Field(None, max_length=10)  # Format: DD.MM.YYYY
    author: Optional[str] = Field(None, max_length=100)
    user_type: Optional[str] = Field(None, max_length=50)
    user_1c_id: Optional[int] = None


class NotificationCreate(NotificationBase):
    company_id: Optional[int] = None
    security_key: Optional[str] = Field(None, max_length=255)


class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=250)
    message: Optional[str] = Field(None, max_length=2000)
    date: Optional[str] = Field(None, max_length=10)
    author: Optional[str] = Field(None, max_length=100)
    user_type: Optional[str] = Field(None, max_length=50)
    user_1c_id: Optional[int] = None
    company_id: Optional[int] = None
    user_id: Optional[int] = None


class AdminNotificationCreate(BaseModel):
    user_id: int = Field(..., description="DB user ID of the target user")
    title: str = Field(..., max_length=250)
    message: Optional[str] = Field(None, max_length=2000)
    date: Optional[str] = Field(None, max_length=10)
    author: Optional[str] = Field(None, max_length=100)


class AdminNotificationBy1cIdCreate(BaseModel):
    user_1c_id: int = Field(..., description="1C ID of the target user")
    company_id: Optional[int] = Field(None, description="Company ID for narrowing the user search")
    title: str = Field(..., max_length=250)
    message: Optional[str] = Field(None, max_length=2000)
    date: Optional[str] = Field(None, max_length=10)
    author: Optional[str] = Field(None, max_length=100)


class SecurityKeyNotificationCreate(BaseModel):
    security_key: str = Field(..., max_length=255, description="Security key for authorization")
    user_1c_id: int = Field(..., description="1C ID of the target user")
    title: str = Field(..., max_length=250)
    message: Optional[str] = Field(None, max_length=2000)
    date: Optional[str] = Field(None, max_length=10)
    author: Optional[str] = Field(None, max_length=100)


class NotificationStatusResponse(BaseModel):
    id: int
    is_read: bool
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    id: int
    company_id: Optional[int] = None
    user_1c_id: Optional[int] = None
    created_at: datetime
    title: str = Field(..., max_length=250)
    message: Optional[str] = Field(None, max_length=2000)
    status: Optional[NotificationStatusResponse] = None
    author: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationUserStatusBase(BaseModel):
    is_read: bool = False


class NotificationUserStatusCreate(NotificationUserStatusBase):
    notification_id: int
    user_id: int


class NotificationUserStatusUpdate(NotificationUserStatusBase):
    pass


class NotificationUserStatusResponse(NotificationUserStatusBase):
    id: int
    notification_id: int
    user_id: int
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    unread_count: int
    model_config = ConfigDict(from_attributes=True)
