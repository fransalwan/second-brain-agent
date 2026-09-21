# apps/backend/app/habits.py
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence, Set
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from .models import Habit, HabitLog


@dataclass(frozen=True)
class HabitStatus:
    habit: Habit
    is_completed_today: bool
    streak: int


def calculate_streak(completed_dates: Set[date], today: date) -> int:
    """Menghitung rentetan hari berturut-turut (streak) penyelesaian habit.

    Jika hari ini sudah selesai: dihitung mundur mulai dari hari ini.
    Jika hari ini belum selesai: jika kemarin selesai, streak kemarin tetap dihitung (belum putus).
    Jika kemarin dan hari ini tidak ada: streak = 0.
    """
    if not completed_dates:
        return 0

    current_check = today
    if today not in completed_dates:
        # Periksa apakah kemarin selesai (streak masih hidup menunggu centang hari ini)
        current_check = today - timedelta(days=1)
        if current_check not in completed_dates:
            return 0

    streak = 0
    while current_check in completed_dates:
        streak += 1
        current_check -= timedelta(days=1)

    return streak


async def get_user_habits_status(
    session: AsyncSession, user_id: UUID, today: date
) -> list[HabitStatus]:
    """Mengambil seluruh habit aktif milik user beserta status penyelesaian dan streak hari ini."""
    habits_res = await session.execute(
        select(Habit)
        .where(Habit.user_id == user_id, Habit.is_active.is_(True))
        .order_by(Habit.position.asc(), Habit.id.asc())
    )
    habits = habits_res.scalars().all()
    if not habits:
        return []

    habit_ids = [h.id for h in habits if h.id is not None]

    # Ambil seluruh log penyelesaian untuk habit-habit aktif ini
    logs_res = await session.execute(
        select(HabitLog.habit_id, HabitLog.completed_date).where(
            HabitLog.user_id == user_id,
            col(HabitLog.habit_id).in_(habit_ids),
        )
    )

    dates_by_habit: dict[int, set[date]] = {hid: set() for hid in habit_ids}
    for hid, c_date in logs_res.all():
        dates_by_habit[hid].add(c_date)

    result: list[HabitStatus] = []
    for h in habits:
        c_dates = dates_by_habit.get(h.id, set())
        is_completed = today in c_dates
        streak = calculate_streak(c_dates, today)
        result.append(
            HabitStatus(habit=h, is_completed_today=is_completed, streak=streak)
        )

    return result


async def check_habit_for_today(
    session: AsyncSession, user_id: UUID, habit_id: int, today: date
) -> tuple[Habit | None, bool, int]:
    """Mencatat centang habit untuk hari ini secara idempotent.

    Mengembalikan (habit, was_already_completed, current_streak).
    Jika habit tidak ditemukan atau bukan milik user, mengembalikan (None, False, 0).
    """
    habit = await session.get(Habit, habit_id)
    if habit is None or habit.user_id != user_id or not habit.is_active:
        return None, False, 0

    # Cek apakah sudah dicentang hari ini
    existing_log = await session.execute(
        select(HabitLog).where(
            HabitLog.habit_id == habit.id,
            HabitLog.completed_date == today,
            HabitLog.user_id == user_id,
        )
    )
    already_done = existing_log.scalars().first() is not None

    if not already_done:
        new_log = HabitLog(
            habit_id=habit.id,
            user_id=user_id,
            completed_date=today,
        )
        session.add(new_log)
        await session.commit()

    # Hitung streak terbaru
    logs_res = await session.execute(
        select(HabitLog.completed_date).where(
            HabitLog.habit_id == habit.id,
            HabitLog.user_id == user_id,
        )
    )
    all_dates = set(logs_res.scalars().all())
    streak = calculate_streak(all_dates, today)

    return habit, already_done, streak
