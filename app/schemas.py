from pydantic import BaseModel, Json, UUID4, field_serializer, ConfigDict
from datetime import datetime


class Threat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    ipv4: str | None
    url: str | None
    date: datetime
    source: str
    original_data: Json | None
    abuseIPDBData: Json | None = None

    @field_serializer("id")
    def serialize_id(self, id: UUID4):
        return str(id)

    @field_serializer("date")
    def serialize_date(self, date: datetime):
        return date.isoformat()
