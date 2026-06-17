from datetime import datetime

from pydantic import BaseModel, ConfigDict

from apps.user.schemas import UserResponse


class WorkingSessionBase(BaseModel):
    session: datetime
    device_name: str
    app: str | None = None
    is_testing: bool | None = None


class WorkingSessionCreate(WorkingSessionBase):
    app: str
    is_testing: bool = False


class WorkingSessionResponse(WorkingSessionBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorkerSessionResponse(BaseModel):
    user: UserResponse
    session: WorkingSessionResponse
    model_config = ConfigDict(from_attributes=True)


class WorkStartTimeResponse(BaseModel):
    session: datetime
    is_yesterday: bool
