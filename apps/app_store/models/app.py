from datetime import date
from typing import Optional

from pydantic import BaseModel


class AppCreate(BaseModel):
    name: str
    developer: str
    shortDescription: str
    description: Optional[str] = ""
    category: str
    tags: Optional[str] = ""
    published: Optional[bool] = False


class AppUpdate(BaseModel):
    name: Optional[str] = None
    developer: Optional[str] = None
    shortDescription: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    icon: Optional[str] = None
    published: Optional[bool] = None


class VersionCreate(BaseModel):
    version: str
    minAndroid: Optional[str] = "8.0"
    changelog: Optional[str] = ""


class VersionUpdate(BaseModel):
    changelog: Optional[str] = None
    minAndroid: Optional[str] = None
