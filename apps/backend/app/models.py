# apps/backend/app/models.py
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import BigInteger, DateTime
from sqlmodel import JSON, Column, Field, SQLModel


def utcnow() -> datetime:
    """Waktu sekarang dalam UTC, timezone-aware."""
    return datetime.now(timezone.utc)


class ChatHistory(SQLModel, table=True):
    __tablename__ = "chat_histories"

    id: Optional[UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id")
    role: str  # 'user' atau 'assistant'
    content: str
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class Profile(SQLModel, table=True):
    __tablename__ = "profiles"
    id: UUID = Field(primary_key=True)
    full_name: Optional[str] = None
    # BigInteger: chat ID Telegram bisa melebihi batas integer 32-bit
    telegram_chat_id: Optional[int] = Field(
        default=None, unique=True, sa_type=BigInteger
    )
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class Note(SQLModel, table=True):
    __tablename__ = "notes"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    content: str
    source: str = Field(default="web")
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class TimeLog(SQLModel, table=True):
    __tablename__ = "time_logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    project_name: str
    started_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )
    # ended_at NULL = timer masih jalan
    ended_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
    duration_minutes: Optional[int] = None


class Donation(SQLModel, table=True):
    __tablename__ = "donations"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="profiles.id")
    amount: int
    message: Optional[str] = None
    payment_method: str
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class InviteCode(SQLModel, table=True):
    __tablename__ = "invite_codes"

    code: str = Field(primary_key=True)
    auth_user_id: UUID
    full_name: Optional[str] = None
    used_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
    # BigInteger: sama seperti Profile.telegram_chat_id
    used_by_chat_id: Optional[int] = Field(default=None, sa_type=BigInteger)
    expires_at: datetime = Field(sa_type=DateTime(timezone=True))
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )
