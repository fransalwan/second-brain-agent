# apps/backend/app/health.py
"""Modul Kesehatan (Sleep Tracker, Hydration Tracker, Micro-Stretching, & Burnout Index).

Menyediakan fungsi pendukung untuk:
- Pelacakan durasi & kualitas tidur harian (/tidur)
- Pemantauan hidrasi air minum harian (/minum)
- Panduan micro-stretching peregangan anti sakit leher & punggung (/stretch)
- Check-in vitamin & suplemen harian (/vitamin)
- Deteksi dini risiko kelelahan dan burnout kognitif (/kesehatan)
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, desc, func, select

from .config import settings
from .habits import check_habit_for_today
from .models import (
    Habit,
    HealthCheckLog,
    HydrationLog,
    Profile,
    SleepLog,
    TimeLog,
    utcnow,
)

LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)


# ==========================================
# 1. SLEEP & RECOVERY TRACKER
# ==========================================
async def log_sleep(
    session: AsyncSession,
    user_id: UUID,
    log_date: date,
    hours: float,
    quality: Optional[str] = None,
    notes: Optional[str] = None,
) -> SleepLog:
    """Mencatat atau memperbarui durasi dan kualitas tidur pada tanggal tertentu."""
    if not quality:
        if hours < 6.0:
            quality = "Kurang"
        elif hours <= 8.0:
            quality = "Cukup"
        else:
            quality = "Nyenyak"

    stmt = select(SleepLog).where(
        SleepLog.user_id == user_id,
        SleepLog.date == log_date,
    )
    result = await session.execute(stmt)
    log = result.scalars().first()

    if log:
        log.hours = hours
        log.quality = quality
        if notes:
            log.notes = notes
    else:
        log = SleepLog(
            user_id=user_id,
            date=log_date,
            hours=hours,
            quality=quality,
            notes=notes,
            created_at=utcnow(),
        )
        session.add(log)

    await session.commit()
    await session.refresh(log)
    return log


async def get_sleep_summary(
    session: AsyncSession,
    user_id: UUID,
    current_date: date,
    days: int = 7,
) -> Tuple[Optional[SleepLog], float, int]:
    """Mengambil log tidur hari ini, rata-rata durasi tidur N hari terakhir, dan total entri."""
    start_date = current_date - timedelta(days=days - 1)
    stmt = (
        select(SleepLog)
        .where(
            SleepLog.user_id == user_id,
            SleepLog.date >= start_date,
            SleepLog.date <= current_date,
        )
        .order_by(desc(SleepLog.date))
    )
    result = await session.execute(stmt)
    logs = list(result.scalars().all())

    today_log = next((l for l in logs if l.date == current_date), None)
    total_hours = sum(l.hours for l in logs)
    avg_hours = round(total_hours / len(logs), 1) if logs else 0.0

    return today_log, avg_hours, len(logs)


# ==========================================
# 2. HYDRATION TRACKER
# ==========================================
def render_water_bar(glasses: int, target: int = 8, length: int = 8) -> str:
    """Menghasilkan progress bar visual hidrasi bergaya [🥤🥤🥤🥤░░░░]."""
    clamped = max(0, min(target, glasses))
    empty_count = max(0, target - clamped)
    bar = "🥤" * clamped + "░" * empty_count
    ml_current = glasses * 250
    ml_target = target * 250
    return f"[{bar}] {glasses}/{target} Gelas ({ml_current} / {ml_target} ml)"


async def log_hydration(
    session: AsyncSession,
    user_id: UUID,
    log_date: date,
    delta_glasses: int = 1,
    set_glasses: Optional[int] = None,
) -> HydrationLog:
    """Menambah atau mengatur jumlah gelas air minum hari ini (1 gelas = 250ml)."""
    stmt = select(HydrationLog).where(
        HydrationLog.user_id == user_id,
        HydrationLog.date == log_date,
    )
    result = await session.execute(stmt)
    log = result.scalars().first()

    if log:
        if set_glasses is not None:
            log.glasses = max(0, set_glasses)
        else:
            log.glasses = max(0, log.glasses + delta_glasses)
        log.updated_at = utcnow()
    else:
        initial = set_glasses if set_glasses is not None else max(1, delta_glasses)
        log = HydrationLog(
            user_id=user_id,
            date=log_date,
            glasses=initial,
            target_glasses=8,
            updated_at=utcnow(),
        )
        session.add(log)

    await session.commit()
    await session.refresh(log)
    return log


async def get_hydration(
    session: AsyncSession,
    user_id: UUID,
    log_date: date,
) -> Tuple[int, int]:
    """Mengambil jumlah gelas dan target gelas hidrasi hari ini."""
    stmt = select(HydrationLog).where(
        HydrationLog.user_id == user_id,
        HydrationLog.date == log_date,
    )
    result = await session.execute(stmt)
    log = result.scalars().first()
    if log:
        return log.glasses, log.target_glasses
    return 0, 8


# ==========================================
# 3. HEALTH CHECK (VITAMIN & STRETCHING)
# ==========================================
async def get_or_create_health_check(
    session: AsyncSession,
    user_id: UUID,
    log_date: date,
) -> HealthCheckLog:
    """Mengambil atau membuat entri catatan kesehatan harian."""
    stmt = select(HealthCheckLog).where(
        HealthCheckLog.user_id == user_id,
        HealthCheckLog.date == log_date,
    )
    result = await session.execute(stmt)
    log = result.scalars().first()
    if not log:
        log = HealthCheckLog(
            user_id=user_id,
            date=log_date,
            took_vitamin=False,
            did_stretch=False,
            burnout_score=0,
            created_at=utcnow(),
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
    return log


async def log_vitamin_check(
    session: AsyncSession,
    user_id: UUID,
    log_date: date,
) -> Tuple[HealthCheckLog, bool]:
    """Mencatat konsumsi vitamin dan otomatis mencentang habit terkait jika ada."""
    log = await get_or_create_health_check(session, user_id, log_date)
    log.took_vitamin = True
    session.add(log)
    await session.commit()

    # Cari apakah user punya habit seputar vitamin / suplemen
    habit_checked = False
    habits_res = await session.execute(
        select(Habit).where(Habit.user_id == user_id, Habit.is_active == True)
    )
    for h in habits_res.scalars().all():
        name_lower = h.name.lower()
        if "vitamin" in name_lower or "suplemen" in name_lower:
            await check_habit_for_today(session, user_id, h.id, log_date)
            habit_checked = True
            break

    return log, habit_checked


async def log_stretch_check(
    session: AsyncSession,
    user_id: UUID,
    log_date: date,
) -> Tuple[HealthCheckLog, bool]:
    """Mencatat sesi peregangan dan otomatis mencentang habit terkait jika ada."""
    log = await get_or_create_health_check(session, user_id, log_date)
    log.did_stretch = True
    session.add(log)
    await session.commit()

    # Cari apakah user punya habit seputar stretching / peregangan / olahraga
    habit_checked = False
    habits_res = await session.execute(
        select(Habit).where(Habit.user_id == user_id, Habit.is_active == True)
    )
    for h in habits_res.scalars().all():
        name_lower = h.name.lower()
        if (
            "stretch" in name_lower
            or "peregangan" in name_lower
            or "olahraga" in name_lower
            or "senam" in name_lower
        ):
            await check_habit_for_today(session, user_id, h.id, log_date)
            habit_checked = True
            break

    return log, habit_checked


def get_stretching_guide_html() -> str:
    """Mengembalikan panduan langkah micro-stretching anti kaku leher & punggung."""
    return (
        "🧘 <b>Panduan Micro-Stretching 3 Menit (Anti Sakit Meja Kerja)</b>\n\n"
        "Cocok dilakukan di sela-sela menulis naskah atau ngoding:\n\n"
        "1. <b>Neck Release (Peregangan Leher):</b>\n"
        "   • Miringkan kepala ke kanan, tahan 15 detik dengan tangan kanan.\n"
        "   • Ulangi untuk sisi kiri. Bernapas perlahan.\n\n"
        "2. <b>Wrist & Forearm Flex (Anti Carpal Tunnel):</b>\n"
        "   • Luruskan tangan ke depan, tarik jemari ke belakang menggunakan tangan lain selama 15 detik.\n"
        "   • Putar pergelangan tangan searah jarum jam dan sebaliknya.\n\n"
        "3. <b>Seated Spine Twist & Chest Opener (Punggung & Dada):</b>\n"
        "   • Duduk tegak, putar badan ke kanan sambil memegang sandaran kursi. Tahan 15 detik.\n"
        "   • Busungkan dada, tarik kedua belikat ke belakang untuk melegakan postur bungkuk.\n\n"
        "<i>Tubuhmu adalah aset termahal riset dan karirmu. Segarkan badan sejenak!</i>"
    )


# ==========================================
# 4. BURNOUT RISK INDEX CALCULATION
# ==========================================
async def calculate_burnout_risk(
    session: AsyncSession,
    user_id: UUID,
    current_date: date,
) -> Dict:
    """Menghitung skor risiko burnout (0-100) berdasarkan 3 pilar:

    1. Lembur malam berturut-turut (> cutoff time / 23:00)
    2. Kurang tidur dalam 3 hari terakhir (< 6 jam)
    3. Intensitas jam fokus hari ini
    """
    profile = await session.get(Profile, user_id)
    cutoff = profile.night_cutoff_time if profile else time(23, 0)

    score = 0
    reasons = []

    # 1. Analisis Tidur 3 Hari Terakhir
    past_3_days = current_date - timedelta(days=3)
    sleep_res = await session.execute(
        select(SleepLog).where(
            SleepLog.user_id == user_id,
            SleepLog.date >= past_3_days,
            SleepLog.date <= current_date,
        )
    )
    sleep_entries = sleep_res.scalars().all()
    short_sleep_days = sum(1 for s in sleep_entries if s.hours < 6.0)

    if short_sleep_days >= 2:
        score += 35
        reasons.append(f"Kurang tidur (< 6 jam) selama {short_sleep_days} hari terakhir")
    elif short_sleep_days == 1:
        score += 15
        reasons.append("Tidur kurang dari 6 jam semalam")

    # 2. Analisis Lembur Malam 3 Hari Terakhir
    # Konversi batas cutoff ke rentang UTC untuk hari-hari terakhir
    late_night_count = 0
    for offset in range(1, 4):
        check_d = current_date - timedelta(days=offset)
        # Ambil time_logs yang berjalan melewati cutoff
        start_check = datetime.combine(check_d, cutoff).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc)
        end_check = start_check + timedelta(hours=6)
        logs_res = await session.execute(
            select(TimeLog).where(
                TimeLog.user_id == user_id,
                TimeLog.started_at >= start_check,
                TimeLog.started_at <= end_check,
            )
        )
        if logs_res.scalars().first():
            late_night_count += 1

    if late_night_count >= 2:
        score += 30
        reasons.append(f"Lembur malam melewati jam {cutoff.strftime('%H:%M')} selama {late_night_count} hari")
    elif late_night_count == 1:
        score += 15
        reasons.append(f"Lembur melewati jam {cutoff.strftime('%H:%M')} tadi malam")

    # 3. Intensitas Fokus Hari Ini
    start_today = datetime.combine(current_date, time(0, 0)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    today_logs_res = await session.execute(
        select(TimeLog).where(
            TimeLog.user_id == user_id,
            TimeLog.started_at >= start_today,
            TimeLog.ended_at.is_not(None),
        )
    )
    today_logs = today_logs_res.scalars().all()
    today_minutes = sum(
        int((t.ended_at - t.started_at).total_seconds() / 60)
        for t in today_logs
        if t.ended_at
    )

    if today_minutes >= 480:  # > 8 jam
        score += 35
        reasons.append(f"Fokus intensif sangat tinggi hari ini ({today_minutes // 60} jam {today_minutes % 60} m)")
    elif today_minutes >= 360:  # > 6 jam
        score += 20
        reasons.append(f"Fokus kerja hari ini melebihi 6 jam ({today_minutes // 60} jam)")

    score = min(100, max(0, score))

    if score < 35:
        level = "Rendah 🟢 (Kondisi Prima)"
        tip = "Energi dan konsentrasimu berada di zona optimal. Lanjutkan ritme kerja yang sehat!"
    elif score <= 65:
        level = "Moderat 🟡 (Waspada Kelelahan)"
        tip = "Mulai terasa akumulasi kelelahan. Pastikan istirahat cukup malam ini dan minum air putih."
    else:
        level = "Tinggi 🔴 (Butuh Pemulihan Segera!)"
        tip = "Beban kognitif dan fisikmu berlebih. Hindari lembur malam ini, tidur sebelum 22:30, dan luangkan waktu rehat!"

    return {
        "score": score,
        "level": level,
        "reasons": reasons,
        "tip": tip,
        "today_focus_mins": today_minutes,
    }


# ==========================================
# 5. DASHBOARD FORMATTER
# ==========================================
def format_health_dashboard_html(
    sleep_log: Optional[SleepLog],
    avg_sleep: float,
    glasses: int,
    target_glasses: int,
    health_check: Optional[HealthCheckLog],
    burnout_data: Dict,
) -> str:
    """Memformat seluruh indikator kesehatan dalam tampilan Telegram HTML yang rapi."""
    # Tidur
    if sleep_log:
        sleep_str = f"<b>{sleep_log.hours} Jam</b> ({sleep_log.quality})"
    else:
        sleep_str = "<i>Belum dicatat</i> (ketik /tidur)"

    # Air
    water_bar = render_water_bar(glasses, target_glasses, length=8)

    # Vitamin & Stretch
    vit_status = "✅ Sudah" if (health_check and health_check.took_vitamin) else "⚪ Belum (/vitamin)"
    stretch_status = "✅ Sudah" if (health_check and health_check.did_stretch) else "⚪ Belum (/stretch)"

    # Burnout
    burnout_score = burnout_data["score"]
    burnout_level = burnout_data["level"]
    burnout_tip = burnout_data["tip"]
    reasons = burnout_data["reasons"]

    lines = [
        "❤️ <b>Dashboard Kesehatan & Vitalitas Pengembang</b>",
        f"<i>Prioritas #1: Menjaga fisik & mental tetap prima.</i>\n",
        f"🛌 <b>Tidur Semalam:</b> {sleep_str}",
        f"📊 <b>Rata-rata 7 Hari:</b> {avg_sleep} jam/hari\n",
        f"💧 <b>Hidrasi Hari Ini:</b>\n  {water_bar}\n",
        f"💊 <b>Vitamin / Suplemen:</b> {vit_status}",
        f"🧘 <b>Micro-Stretching:</b> {stretch_status}\n",
        f"🧠 <b>Burnout Risk Index:</b> <b>{burnout_score}/100</b> — {burnout_level}",
    ]

    if reasons:
        lines.append("<i>Faktor beban:</i>")
        for r in reasons:
            lines.append(f"• {r}")

    lines.append(f"\n💡 <i>Saran:</i> {burnout_tip}")
    lines.append("\n<i>Ketik perintah cepat:</i> /tidur, /minum, /stretch, /vitamin")

    return "\n".join(lines)
