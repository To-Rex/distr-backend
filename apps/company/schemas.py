from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    name: str = Field(..., max_length=255)
    inn: Optional[str] = Field(None, max_length=50)
    base_url: Optional[str] = Field("", max_length=500)
    asl_belgi_token: Optional[str] = Field("", max_length=500)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    inn: Optional[str] = Field(None, max_length=50)
    base_url: Optional[str] = Field(None, max_length=500)
    asl_belgi_token: Optional[str] = Field(None, max_length=500)


class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecurityKeyBase(BaseModel):
    key: str = Field(..., max_length=255)
    company_id: int


class SecurityKeyCreate(SecurityKeyBase):
    pass


class SecurityKeyUpdate(BaseModel):
    key: Optional[str] = Field(None, max_length=255)


class SecurityKeyResponse(SecurityKeyBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

