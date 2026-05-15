from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: str
    name: str
    labelUz: str
    appCount: int


class StatsResponse(BaseModel):
    totalApps: int
    totalVersions: int
    totalDownloads: int
    totalCategories: int
