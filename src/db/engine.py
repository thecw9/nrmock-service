from sqlalchemy import create_engine

from src.config import Config

config = Config()

if config.POSTGRES_URI is None:
    raise Exception("DATABASE_URI is not set")

engine = create_engine(config.POSTGRES_URI, echo=True)
