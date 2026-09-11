from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class Profile(SQLModel, table=True):
    __tablename__ = "profiles"
    id: UUID = Field(primary_key=True)
    full_name: Optional[str] = None
    telegram_chat_id: Optional[int] = Field(default=None, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Note(SQLModel, table=True):
    __tablename__ = "notes"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id")
    content: str
    source: str = Field(default="web")
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TimeLog(SQLModel, table=True):
    __tablename__ = "time_logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id")
    project_name: str
    duration_minutes: int
    started_at: datetime = Field(default_factory=datetime.utcnow)


class Donation(SQLModel, table=True):
    __tablename__ = "donations"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="profiles.id")
    amount: int
    message: Optional[str] = None
    payment_method: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
