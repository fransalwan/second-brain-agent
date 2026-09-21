# apps/backend/app/priority.py
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Sequence
from .models import Area, Task

# Jendela hari untuk kategori "Segera"
SOON_WINDOW_DAYS = 3

INDO_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


class PriorityTier(str, Enum):
    NOW = "sekarang"
    SOON = "segera"
    LATER = "lainnya"


@dataclass(frozen=True)
class PrioritizedTask:
    task: Task
    area: Area | None
    tier: PriorityTier
    reason: str

    @property
    def area_name(self) -> str:
        return self.area.name if self.area else "Tanpa Area"


def _compute_reason(task: Task, area: Area | None, today: date) -> str:
    """Menghasilkan alasan singkat dalam bahasa manusia yang menjelaskan kenapa tugas diprioritaskan."""
    # 1. Lewat deadline
    if task.deadline and task.deadline < today:
        days = (today - task.deadline).days
        if days == 1:
            return "lewat deadline 1 hari"
        return f"lewat deadline {days} hari"

    # 2. Deadline hari ini
    if task.deadline and task.deadline == today:
        return "deadline hari ini"

    # 3. Ditandai mendesak (tanpa deadline atau deadline masa depan)
    if task.is_urgent:
        return "ditandai mendesak"

    # 4. Deadline mendekat (1 s/d SOON_WINDOW_DAYS)
    if task.deadline and today < task.deadline <= today + timedelta(
        days=SOON_WINDOW_DAYS
    ):
        days = (task.deadline - today).days
        day_name = INDO_DAYS[task.deadline.weekday()]
        if days == 1:
            return f"deadline besok ({day_name})"
        elif days == 2:
            return f"deadline lusa ({day_name})"
        return f"deadline {days} hari lagi ({day_name})"

    # 5. Deadline jauh (> SOON_WINDOW_DAYS)
    if task.deadline and task.deadline > today + timedelta(days=SOON_WINDOW_DAYS):
        days = (task.deadline - today).days
        return f"deadline {days} hari lagi"

    # 6. Tanpa deadline & tidak mendesak
    if area:
        if area.position == 1:
            return f"area prioritas utama ({area.name})"
        return f"area {area.name}"

    return "tanpa area"


def prioritize_tasks(
    tasks: Sequence[Task],
    areas: Sequence[Area],
    today: date,
) -> list[PrioritizedTask]:
    """Fungsi murni deterministik untuk mengurutkan tugas ke dalam 3 tingkatan prioritas:

    1. Tingkat 'Sekarang':
       - Kriteria: deadline < hari ini, deadline == hari ini, ATAU is_urgent.
       - Urutan: posisi area ASC, jumlah hari terlambat DESC (terbanyak dulu), created_at ASC.
    2. Tingkat 'Segera':
       - Kriteria: deadline 1 sampai SOON_WINDOW_DAYS hari lagi.
       - Urutan: tanggal deadline terdekat ASC, posisi area ASC, created_at ASC.
    3. Tingkat 'Lainnya':
       - Kriteria: deadline > SOON_WINDOW_DAYS hari lagi ATAU tanpa deadline.
       - Urutan: posisi area ASC, deadline terdekat ASC (tanpa deadline paling belakang), created_at ASC.

    Tugas tanpa area ditaruh di posisi terakhir di tingkatannya masing-masing.
    """
    area_map = {a.id: a for a in areas if a.id is not None}

    def get_pos(task: Task) -> int:
        if task.area_id and task.area_id in area_map:
            return area_map[task.area_id].position
        return 999_999

    def get_created_at(task: Task) -> datetime:
        if task.created_at is not None:
            return task.created_at
        return datetime.min.replace(tzinfo=timezone.utc)

    now_items: list[PrioritizedTask] = []
    soon_items: list[PrioritizedTask] = []
    later_items: list[PrioritizedTask] = []

    for t in tasks:
        area = area_map.get(t.area_id) if t.area_id else None
        reason = _compute_reason(t, area, today)

        is_now = (t.deadline is not None and t.deadline <= today) or t.is_urgent
        if is_now:
            now_items.append(
                PrioritizedTask(task=t, area=area, tier=PriorityTier.NOW, reason=reason)
            )
        else:
            is_soon = (
                t.deadline is not None
                and today < t.deadline <= today + timedelta(days=SOON_WINDOW_DAYS)
            )
            if is_soon:
                soon_items.append(
                    PrioritizedTask(
                        task=t, area=area, tier=PriorityTier.SOON, reason=reason
                    )
                )
            else:
                later_items.append(
                    PrioritizedTask(
                        task=t, area=area, tier=PriorityTier.LATER, reason=reason
                    )
                )

    # -----------------------------------------------------------------------
    # 1. Tingkat "Sekarang"
    # Urutan: posisi area ASC, jumlah hari terlambat DESC, created_at ASC
    # -----------------------------------------------------------------------
    def sort_key_now(item: PrioritizedTask):
        t = item.task
        pos = get_pos(t)
        days_overdue = (
            (today - t.deadline).days if (t.deadline and t.deadline < today) else 0
        )
        return (pos, -days_overdue, get_created_at(t))

    now_items.sort(key=sort_key_now)

    # -----------------------------------------------------------------------
    # 2. Tingkat "Segera"
    # Urutan: tanggal deadline terdekat ASC, posisi area ASC, created_at ASC
    # -----------------------------------------------------------------------
    def sort_key_soon(item: PrioritizedTask):
        t = item.task
        return (t.deadline, get_pos(t), get_created_at(t))

    soon_items.sort(key=sort_key_soon)

    # -----------------------------------------------------------------------
    # 3. Tingkat "Lainnya"
    # Urutan: posisi area ASC, deadline terdekat ASC (tanpa deadline paling belakang), created_at ASC
    # -----------------------------------------------------------------------
    def sort_key_later(item: PrioritizedTask):
        t = item.task
        pos = get_pos(t)
        dl_key = (0, t.deadline) if t.deadline is not None else (1, date.max)
        return (pos, dl_key, get_created_at(t))

    later_items.sort(key=sort_key_later)

    return now_items + soon_items + later_items


def get_top_tasks_for_brief(
    prioritized_tasks: Sequence[PrioritizedTask],
    limit: int = 3,
) -> list[tuple[PrioritizedTask, bool]]:
    """Mengambil maksimal `limit` tugas teratas untuk brief pagi.
    Tugas pertama ditandai True ('mulai dari sini').
    """
    top = prioritized_tasks[:limit]
    return [(item, idx == 0) for idx, item in enumerate(top)]
