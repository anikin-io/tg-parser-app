import os
from pathlib import Path

from sqlalchemy import create_engine

from core.entities.base import Base

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "sqlite_database" / "telegram_accounts.db"
os.makedirs(DATABASE_PATH.parent, exist_ok=True)

engine = create_engine(f"sqlite:///{DATABASE_PATH.as_posix()}", echo=False)


def init_db():
    """Создание таблиц, если их нет."""
    Base.metadata.create_all(engine)
