from sqlalchemy import Column, Enum, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from config import statuses
from core.entities.base import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    proxy_ip = Column(String, nullable=False)
    proxy_port = Column(Integer, nullable=False)
    proxy_username = Column(String, nullable=False)
    proxy_password = Column(String, nullable=False)
    status = Column(
        Enum(
            statuses.STATUS_IN_WORK,
            statuses.STATUS_LIMIT_REACHED,
            statuses.STATUS_SPAM_BLOCK,
            statuses.STATUS_FREE,
            statuses.STATUS_ON_PAUSE,
            name="status_enum",
        ),
        nullable=False,
        default=statuses.STATUS_FREE,
    )

    def __repr__(self):
        return f"<Account(phone={self.phone}, name={self.name}, status={self.status})>"
