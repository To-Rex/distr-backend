from datetime import date
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    email: str
    role: str
    displayName: str


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    displayName: str
    role: str = "publisher"


class UserUpdate(BaseModel):
    displayName: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: str
    avatar: Optional[str] = None
    createdAt: str


class UserDetail(UserResponse):
    appsCount: int = 0
    totalAppDownloads: int = 0


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str


class ProfileUpdate(BaseModel):
    displayName: Optional[str] = None
