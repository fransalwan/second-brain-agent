# apps/backend/app/brief_formatter.py
import html
from datetime import date
from typing import Sequence
from .priority import PrioritizedTask

INDO_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
INDO_MONTHS = [
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
]


def format_brief_message(
    top_tasks: Sequence[tuple[PrioritizedTask, bool]],
    total_overdue_count: int,
    target_date: date,
    habits: Sequence[object] | None = None,
) -> str:
    """Menyusun teks Brief Pagi dalam format HTML Telegram deterministik (0 kuota LLM).

    top_tasks: list of (PrioritizedTask, is_start_here)
    total_overdue_count: jumlah seluruh tugas yang sudah lewat deadline
    target_date: tanggal lokal brief dikirim
    habits: list of HabitStatus (opsional)
    """
    day_name = INDO_DAYS[target_date.weekday()]
    month_name = INDO_MONTHS[target_date.month - 1]
    date_header = f"{day_name}, {target_date.day} {month_name} {target_date.year}"

    lines: list[str] = [f"☀️ <b>Brief Pagi</b> | {date_header}\n"]

    if total_overdue_count > 0:
        lines.append(
            f"⚠️ <b>Perhatian:</b> Ada {total_overdue_count} tugas yang sudah lewat deadline!\n"
        )

    if not top_tasks:
        lines.append("Fokus utama kamu hari ini:")
        lines.append(
            "🎉 Tidak ada tugas pending saat ini. Santai sejenak atau gunakan /tasks untuk mencatat hal baru!\n"
        )
    else:
        lines.append("Fokus utama kamu hari ini:\n")
        for item, is_first in top_tasks:
            task_title = html.escape(item.task.title)
            area_name = html.escape(item.area_name)
            reason = html.escape(item.reason)
            urgent_badge = " [MENDESAK]" if item.task.is_urgent else ""

            if is_first:
                lines.append(
                    f"👉 <b>Mulai dari sini:</b> <b>{task_title}</b>{urgent_badge} [{area_name}]\n"
                    f"   <i>Alasan: {reason}</i>\n"
                )
            else:
                lines.append(
                    f"• <b>{task_title}</b>{urgent_badge} [{area_name}]\n"
                    f"   <i>Alasan: {reason}</i>\n"
                )

    if habits:
        completed_count = sum(
            1 for h in habits if getattr(h, "is_completed_today", False)
        )
        total_count = len(habits)
        chips = [
            f"{'[✓]' if getattr(h, 'is_completed_today', False) else '[ ]'} {html.escape(h.habit.name)}"
            for h in habits
        ]
        lines.append(
            f"🌱 <b>Habit hari ini ({completed_count}/{total_count}):</b>\n"
            + " • ".join(chips)
            + "\n"
        )

    lines.append("💡 Tugas lainnya bisa kamu cek kapan saja dengan mengetik /tasks.")
    return "\n".join(lines).strip()
