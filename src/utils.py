from sqlalchemy.orm import Session

from src.db import engine


def get_db():
    with Session(engine) as session:
        yield session
