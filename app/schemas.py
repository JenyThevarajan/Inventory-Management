from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class AssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    asset_type: str = "Dataset"
    description: str = ""
    owner: str = ""
    team: str = ""
    status: str = "Available"
    location: str = ""
    license: str = "Unknown"
    tags: str = ""
    version: str = "1.0"

class AssetRead(AssetCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime

class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_id: int
    action: str
    detail: str
    created_at: datetime
