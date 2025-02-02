from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime
import json

from .database import Base


class Threat(Base):
    __tablename__ = "threats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ipv4 = Column(String, unique=True, nullable=True)
    url = Column(String, unique=True, nullable=True)
    date = Column(DateTime)
    source = Column(String)
    original_data = Column(String)
    abuseIPDBData = Column(String)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.original_data = json.dumps(kwargs.get("original_data", {}))
        self.abuseIPDBData = json.dumps(kwargs.get("abuseIPDBData", {}))
