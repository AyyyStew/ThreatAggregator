from pydantic import BaseModel, Field, Json
from datetime import datetime
import uuid


class Threat(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    ipv4: str | None
    url: str | None
    date: datetime
    source: str
    original_data: Json | None
    abuseIPDBData: Json | None = None
