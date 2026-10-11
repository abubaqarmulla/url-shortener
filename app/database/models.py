from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password = Column(
        String(255),
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    urls = relationship(
        "URL",
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class URL(Base):
    __tablename__ = "urls"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    original_url = Column(
        String(2048),
        nullable=False,
    )

    short_code = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    expires_at = Column(
        DateTime,
        nullable=True,
    )

    click_count = Column(
        Integer,
        default=0,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    owner = relationship(
        "User",
        back_populates="urls",
    )
