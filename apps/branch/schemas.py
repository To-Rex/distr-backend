from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BranchBase(BaseModel):
    name: str
    company_id: Optional[int] = None


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    company_id: Optional[int] = None


class BranchResponse(BranchBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
