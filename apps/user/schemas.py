from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from apps.company.schemas import CompanyResponse
from apps.user.models import UserStatus, UserType  # Import your Enum classes


class UserBase(BaseModel):
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    photo: Optional[str] = None
    user_type: Optional[UserType] = None
    user_status: Optional[UserStatus] = None
    company_id: Optional[int] = None
    manager_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    photo: Optional[str] = None
    user_type: Optional[UserType] = None
    user_status: Optional[UserStatus] = None
    company_id: Optional[int] = None
    manager_id: Optional[int] = None
    user_1c_id: Optional[int] = None
    user_1c_login: Optional[str] = None
    user_1c_password: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    photo: Optional[str] = None
    user_type: Optional[UserType] = None
    user_status: Optional[UserStatus] = None
    company_id: Optional[int] = None
    manager_id: Optional[int] = None
    user_1c_id: Optional[int] = None
    user_1c_login: Optional[str] = None
    user_1c_password: Optional[str] = None


class UserPartialUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    photo: Optional[str] = None
    user_type: Optional[UserType] = None
    user_status: Optional[UserStatus] = None
    company_id: Optional[int] = None
    manager_id: Optional[int] = None


class UserRead(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    user_type: UserType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ManagerRead(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    photo: Optional[str] = None
    user_type: UserType
    company_rel: Optional[CompanyResponse] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    photo: Optional[str] = None
    user_type: UserType
    company_id: Optional[int] = None
    company_rel: Optional[CompanyResponse] = None
    manager: Optional["ManagerRead"] = None
    manager_id: Optional[int] = None
    user_1c_id: Optional[int] = None
    user_1c_login: Optional[str] = None
    user_1c_password: Optional[str] = None
    created_at: datetime
    user_status: Optional[UserStatus] = None
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    id: int
    access_token: str
    expires_in: datetime
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str
    password: str
    device_id: str | None = None
    firebase_token: str | None = None


class JwtTokenResponse(BaseModel):
    id: int
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: datetime
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    refresh_token: str
