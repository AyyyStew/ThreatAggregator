import os


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{BASE_DIR}/data/threats.db"
