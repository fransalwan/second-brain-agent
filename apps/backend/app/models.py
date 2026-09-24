import uuid
from datetime import date, date as dt_date, datetime, time, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import BigInteger, Date, DateTime, Time
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
    email: Optional[str] = Field(default=None, index=True)
    full_name: Optional[str] = None
    # BigInteger: chat ID Telegram bisa melebihi batas integer 32-bit
    telegram_chat_id: Optional[int] = Field(
        default=None, unique=True, sa_type=BigInteger
    )
    brief_time: time = Field(default=time(7, 0), sa_type=Time)
    last_brief_date: Optional[date] = Field(default=None, sa_type=Date)
    night_cutoff_time: time = Field(default=time(23, 0), sa_type=Time)
    last_weekly_report_date: Optional[date] = Field(default=None, sa_type=Date)
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
    break_reminder_sent: bool = Field(default=False)
    night_warning_sent: bool = Field(default=False)


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


class Area(SQLModel, table=True):
    __tablename__ = "areas"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    name: str
    position: int
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    area_id: Optional[int] = Field(default=None, foreign_key="areas.id", index=True)
    title: str
    deadline: Optional[date] = Field(default=None, sa_type=Date)
    is_urgent: bool = Field(default=False)
    status: str = Field(default="pending")
    completed_at: Optional[datetime] = Field(
        default=None, sa_type=DateTime(timezone=True)
    )
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class Habit(SQLModel, table=True):
    __tablename__ = "habits"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    name: str
    is_active: bool = Field(default=True)
    position: int = Field(default=1)
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class HabitLog(SQLModel, table=True):
    __tablename__ = "habit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    habit_id: int = Field(foreign_key="habits.id", index=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    completed_date: date = Field(sa_type=Date)
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class ThesisChapter(SQLModel, table=True):
    __tablename__ = "thesis_chapters"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    chapter_num: int  # 1 sampai 5
    title: str
    status: str = Field(default="Belum Mulai")  # Belum Mulai, Drafting, Revisi, Selesai
    progress: int = Field(default=0)  # 0 - 100
    updated_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class SupervisionLog(SQLModel, table=True):
    __tablename__ = "supervision_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    notes: str
    action_items: Optional[str] = None
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class ExperimentMetric(SQLModel, table=True):
    __tablename__ = "experiment_metrics"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    model_name: str
    metrics_summary: str  # Misal "Akurasi: 92.4%, F1: 91.8%, Loss: 0.14"
    parameters: Optional[str] = None  # Misal "Epoch: 50, LR: 0.001"
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class SleepLog(SQLModel, table=True):
    __tablename__ = "sleep_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    date: dt_date = Field(sa_type=Date, index=True)
    hours: float
    quality: str = Field(default="Cukup")  # "Kurang", "Cukup", "Nyenyak"
    notes: Optional[str] = None
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class HydrationLog(SQLModel, table=True):
    __tablename__ = "hydration_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    date: dt_date = Field(sa_type=Date, index=True)
    glasses: int = Field(default=1)  # 1 gelas = 250ml
    target_glasses: int = Field(default=8)  # 8 gelas = 2000ml
    updated_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class HealthCheckLog(SQLModel, table=True):
    __tablename__ = "health_check_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    date: dt_date = Field(sa_type=Date, index=True)
    took_vitamin: bool = Field(default=False)
    did_stretch: bool = Field(default=False)
    burnout_score: int = Field(default=0)  # 0 - 100
    notes: Optional[str] = None
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class CourseAssignment(SQLModel, table=True):
    __tablename__ = "course_assignments"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    course_name: str = Field(index=True)
    title: str
    assignment_type: str = Field(default="Individu")  # Individu, Kelompok, Praktikum, Reading
    deadline: Optional[datetime] = Field(
        default=None, sa_type=DateTime(timezone=True)
    )
    weight_percent: Optional[int] = Field(default=None)  # contoh: 15 untuk 15%
    status: str = Field(default="pending")  # pending, done
    notes: Optional[str] = None
    completed_at: Optional[datetime] = Field(
        default=None, sa_type=DateTime(timezone=True)
    )
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class CourseExam(SQLModel, table=True):
    __tablename__ = "course_exams"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    course_name: str = Field(index=True)
    exam_type: str = Field(default="UTS")  # UTS, UAS, Kuis, Praktikum
    exam_date: datetime = Field(sa_type=DateTime(timezone=True))
    room_or_link: Optional[str] = None
    rules: Optional[str] = Field(default="Closed Book")  # Closed Book, Open Book, Take-Home
    topics: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))
    target_score: Optional[int] = Field(default=85)
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )


class CourseProject(SQLModel, table=True):
    __tablename__ = "course_projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id", index=True)
    course_name: str = Field(index=True)
    title: str
    deadline: Optional[datetime] = Field(
        default=None, sa_type=DateTime(timezone=True)
    )
    milestones: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))
    deliverables: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default="in_progress")  # in_progress, completed
    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )
