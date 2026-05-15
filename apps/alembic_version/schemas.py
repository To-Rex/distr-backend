from pydantic import BaseModel, ConfigDict, Field


class AlembicVersionCreate(BaseModel):
    version_num: str = Field(
        ..., max_length=32, description="Alembic migration version raqami"
    )


class AlembicVersionResponse(BaseModel):
    version_num: str

    model_config = ConfigDict(from_attributes=True)
