import uuid
import json
from sqlalchemy import Column, String, DateTime
from sqlalchemy.types import TypeDecorator, VARCHAR

from .database import Base


class JSONEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class Threat(Base):
    __tablename__ = "threats"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ipv4 = Column(String, unique=True, nullable=True)
    url = Column(String, unique=True, nullable=True)
    date = Column(DateTime, index=True)
    source = Column(String)
    original_data = Column(JSONEncodedDict)
    abuseIPDBData = Column(JSONEncodedDict)
