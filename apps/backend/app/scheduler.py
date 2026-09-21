# apps/backend/app/scheduler.py
import html
import logging
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from sqlmodel import col, or_, select
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes

from .brief_formatter import format_brief_message
from .config import settings
from .database import SessionLocal
from .habits import get_user_habits_status
from .models import Area, Profile, Task, TimeLog, utcnow
from .priority import get_top_tasks_for_brief, prioritize_tasks
from .recharge import build_break_reminder_keyboard

logger = logging.getLogger(__name__)

LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)
CHECK_INTERVAL_SECONDS = 900  # 15 menit
BREAK_REMINDER_THRESHOLD_MINUTES = 90  # 90 menit fokus terus menerus
BREAK_CHECK_INTERVAL_SECONDS = 300  # 5 menit
NIGHT_CHECK_INTERVAL_SECONDS = 300  # 5 menit


def is_past_night_cutoff(
    current_time: time, cutoff: time, morning_end: time = time(4, 0)
) -> bool:
    """Mengecek apakah current_time berada di rentang batas jam kerja malam hingga pagi hari."""
    if cutoff >= morning_end:
        return current_time >= cutoff or current_time < morning_end
    else:
        return cutoff <= current_time < morning_end


async def check_and_send_briefs(bot: Bot) -> int:
    """Memeriksa profil yang memenuhi syarat untuk menerima Brief Pagi hari ini dan mengirimkannya.

    Kriteria profil:
    1. telegram_chat_id terdaftar
    2. brief_time <= waktu lokal saat ini
    3. last_brief_date IS NULL ATAU last_brief_date < tanggal lokal hari ini

    Mengembalikan jumlah brief yang sukses terkirim.
    """
    now_local = datetime.now(LOCAL_TZ)
    current_time = now_local.time()
    current_date = now_local.date()

    async with SessionLocal() as session:
        stmt = select(Profile).where(
            Profile.telegram_chat_id.is_not(None),
            Profile.brief_time <= current_time,
            or_(
                Profile.last_brief_date.is_(None),
                Profile.last_brief_date < current_date,
            ),
        )
        result = await session.execute(stmt)
        eligible_profiles = result.scalars().all()

    if not eligible_profiles:
        return 0

    sent_count = 0
    for profile in eligible_profiles:
        try:
            # Query tugas pending dan area milik user
            async with SessionLocal() as session:
                tasks_res = await session.execute(
                    select(Task).where(
                        Task.user_id == profile.id, Task.status == "pending"
                    )
                )
                tasks = tasks_res.scalars().all()

                areas_res = await session.execute(
                    select(Area)
                    .where(Area.user_id == profile.id)
                    .order_by(Area.position.asc())
                )
                areas = areas_res.scalars().all()

                habits_status = await get_user_habits_status(
                    session, profile.id, current_date
                )

            total_overdue = sum(
                1 for t in tasks if t.deadline and t.deadline < current_date
            )
            prioritized = prioritize_tasks(tasks, areas, current_date)
            top_tasks = get_top_tasks_for_brief(prioritized, limit=3)
            message_text = format_brief_message(
                top_tasks, total_overdue, current_date, habits=habits_status
            )

            # Kirim pesan via bot
            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=message_text,
                parse_mode=ParseMode.HTML,
            )

            # Update last_brief_date HANYA jika pengiriman berhasil
            async with SessionLocal() as session:
                p = await session.get(Profile, profile.id)
                if p:
                    p.last_brief_date = current_date
                    session.add(p)
                    await session.commit()

            sent_count += 1
            logger.info(
                "Brief pagi berhasil dikirim ke user %s (chat_id=%s)",
                profile.id,
                profile.telegram_chat_id,
            )
        except Exception as e:
            logger.exception(
                "Gagal mengirim brief pagi ke user %s (chat_id=%s): %s",
                profile.id,
                profile.telegram_chat_id,
                e,
            )
            # JANGAN update last_brief_date jika gagal agar dapat dicoba lagi pada interval berikutnya

    return sent_count


async def check_and_send_break_reminders(bot: Bot) -> int:
    """Memeriksa timer yang sedang berjalan >= BREAK_REMINDER_THRESHOLD_MINUTES dan belum diingatkan.

    Mengirimkan pengingat istirahat ramah dan menandai break_reminder_sent = True (1x per sesi).
    """
    now_utc = utcnow()
    async with SessionLocal() as session:
        stmt = (
            select(TimeLog, Profile)
            .join(Profile, TimeLog.user_id == Profile.id)
            .where(
                col(TimeLog.ended_at).is_(None),
                TimeLog.break_reminder_sent.is_(False),
                Profile.telegram_chat_id.is_not(None),
            )
        )
        result = await session.execute(stmt)
        running_timers = result.all()

    if not running_timers:
        return 0

    sent_count = 0
    for time_log, profile in running_timers:
        started_at = time_log.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        elapsed_minutes = int((now_utc - started_at).total_seconds() // 60)
        if elapsed_minutes >= BREAK_REMINDER_THRESHOLD_MINUTES:
            project_title = html.escape(time_log.project_name)
            message_text = (
                f"☕ <b>Waktunya Istirahat Sejenak!</b>\n\n"
                f"Kamu sudah fokus pada <b>{project_title}</b> selama <b>{elapsed_minutes} menit</b>.\n"
                f"Berdiri sejenak, regangkan badan, atau minum air agar pikiran tetap segar.\n\n"
                f'Ketik /stop atau chat <i>"udahan dulu"</i> jika ingin menghentikan timer.'
            )
            try:
                await bot.send_message(
                    chat_id=profile.telegram_chat_id,
                    text=message_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=build_break_reminder_keyboard(),
                )
                async with SessionLocal() as session:
                    tl = await session.get(TimeLog, time_log.id)
                    if tl:
                        tl.break_reminder_sent = True
                        session.add(tl)
                        await session.commit()
                sent_count += 1
                logger.info(
                    "Pengingat istirahat terkirim ke user %s (chat_id=%s, durasi=%s menit)",
                    profile.id,
                    profile.telegram_chat_id,
                    elapsed_minutes,
                )
            except Exception as e:
                logger.exception(
                    "Gagal mengirim pengingat istirahat ke user %s: %s",
                    profile.id,
                    e,
                )

    return sent_count


async def check_and_send_night_warnings(bot: Bot) -> int:
    """Memeriksa timer yang sedang berjalan saat sudah melewati batas jam kerja malam.

    Mengirimkan pengingat tidur ramah dan menandai night_warning_sent = True (1x per sesi).
    """
    now_utc = utcnow()
    now_local = datetime.now(LOCAL_TZ)
    current_time = now_local.time()

    async with SessionLocal() as session:
        stmt = (
            select(TimeLog, Profile)
            .join(Profile, TimeLog.user_id == Profile.id)
            .where(
                col(TimeLog.ended_at).is_(None),
                TimeLog.night_warning_sent.is_(False),
                Profile.telegram_chat_id.is_not(None),
            )
        )
        result = await session.execute(stmt)
        running_timers = result.all()

    if not running_timers:
        return 0

    sent_count = 0
    for time_log, profile in running_timers:
        cutoff = profile.night_cutoff_time or time(23, 0)
        if not is_past_night_cutoff(current_time, cutoff):
            continue

        started_at = time_log.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        elapsed_minutes = int((now_utc - started_at).total_seconds() // 60)

        project_title = html.escape(time_log.project_name)
        cutoff_str = cutoff.strftime("%H:%M")
        message_text = (
            f"🌙 <b>Sudah Larut Malam!</b>\n\n"
            f"Waktu saat ini sudah melewati batas jam kerja malammu (pukul {cutoff_str}).\n"
            f"Kamu masih memiliki timer aktif pada <b>{project_title}</b> ({elapsed_minutes} menit).\n\n"
            f"Saatnya mengistirahatkan pikiran dan tubuh agar besok bangun segar dan bertenaga.\n"
            f'Ketik /stop atau chat <i>"udahan dulu"</i> untuk menghentikan timer.'
        )
        try:
            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=message_text,
                parse_mode=ParseMode.HTML,
            )
            async with SessionLocal() as session:
                tl = await session.get(TimeLog, time_log.id)
                if tl:
                    tl.night_warning_sent = True
                    session.add(tl)
                    await session.commit()
            sent_count += 1
            logger.info(
                "Pengingat jam malam terkirim ke user %s (chat_id=%s, cutoff=%s)",
                profile.id,
                profile.telegram_chat_id,
                cutoff_str,
            )
        except Exception as e:
            logger.exception(
                "Gagal mengirim pengingat jam malam ke user %s: %s",
                profile.id,
                e,
            )

    return sent_count


async def brief_job_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback pembungkus untuk JobQueue python-telegram-bot (Brief Pagi)."""
    await check_and_send_briefs(context.bot)


async def break_job_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback pembungkus untuk JobQueue python-telegram-bot (Pengingat Istirahat)."""
    await check_and_send_break_reminders(context.bot)


async def night_job_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback pembungkus untuk JobQueue python-telegram-bot (Batas Jam Malam)."""
    await check_and_send_night_warnings(context.bot)


def setup_brief_scheduler(application: Application) -> None:
    """Mendaftarkan periodic checker (Brief Pagi, Istirahat, & Jam Malam) ke JobQueue PTB."""
    if application.job_queue is None:
        logger.warning(
            "JobQueue tidak tersedia pada Application; scheduler tidak didaftarkan."
        )
        return

    # 1. Brief Pagi: first 10s, interval 15 menit
    application.job_queue.run_repeating(
        brief_job_callback,
        interval=CHECK_INTERVAL_SECONDS,
        first=10,
        name="check_and_send_briefs",
    )
    logger.info(
        "Scheduler brief pagi berhasil didaftarkan (interval: %s detik, first: 10s).",
        CHECK_INTERVAL_SECONDS,
    )

    # 2. Pengingat Istirahat Timer: first 15s, interval 5 menit
    application.job_queue.run_repeating(
        break_job_callback,
        interval=BREAK_CHECK_INTERVAL_SECONDS,
        first=15,
        name="check_break_reminders",
    )
    logger.info(
        "Scheduler pengingat istirahat timer berhasil didaftarkan (interval: %s detik, threshold: %s menit).",
        BREAK_CHECK_INTERVAL_SECONDS,
        BREAK_REMINDER_THRESHOLD_MINUTES,
    )

    # 3. Pengingat Batas Jam Malam: first 20s, interval 5 menit
    application.job_queue.run_repeating(
        night_job_callback,
        interval=NIGHT_CHECK_INTERVAL_SECONDS,
        first=20,
        name="check_night_warnings",
    )
    logger.info(
        "Scheduler pengingat batas jam malam berhasil didaftarkan (interval: %s detik).",
        NIGHT_CHECK_INTERVAL_SECONDS,
    )
