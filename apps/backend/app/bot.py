import logging
import secrets
from datetime import datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

import httpx
from sqlmodel import col, select, text
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from .agent import run_agent
from .config import settings
from .database import SessionLocal
from .brief_formatter import INDO_DAYS, INDO_MONTHS
from .habits import check_habit_for_today, get_user_habits_status
from .models import (
    Area,
    Habit,
    HabitLog,
    InviteCode,
    Note,
    Profile,
    Task,
    TimeLog,
    utcnow,
)
from .priority import prioritize_tasks
from .recharge import (
    build_chill_menu_keyboard,
    build_coffee_keyboard,
    build_hangout_keyboard,
    build_movie_keyboard,
    build_music_keyboard,
    get_random_activity,
    get_random_movie,
)
from .scheduler import setup_brief_scheduler
from .weekly_report import (
    format_weekly_report_html,
    generate_weekly_insight_llm,
    get_weekly_stats,
)

logger = logging.getLogger(__name__)

# Ambil token langsung dari Pydantic Settings
TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_MAX_LEN = 4096
LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)

# Request HTTPX dengan timeout lebih toleran (mencegah ConnectTimeout pada koneksi lambat/fluktuatif)
ptb_request = HTTPXRequest(
    connect_timeout=20.0,
    read_timeout=20.0,
    write_timeout=20.0,
    pool_timeout=10.0,
)

# Bangun Application: updater(None) hanya jika mode webhook.
# Pada mode polling (default), updater internal dibiarkan aktif untuk start_polling.
builder = Application.builder().token(TELEGRAM_BOT_TOKEN).request(ptb_request)
if settings.TELEGRAM_MODE == "webhook":
    builder = builder.updater(None)
ptb_app = builder.build()

NOT_LINKED_MSG = (
    "Akun Telegram ini belum terhubung ke Second Brain.\n\n"
    "Kalau kamu punya kode undangan, kirim:\n"
    "/connect KODE-KAMU\n\n"
    "Chat ID kamu: {chat_id}"
)


async def get_profile_by_chat_id(chat_id: int) -> Profile | None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Profile).where(Profile.telegram_chat_id == chat_id)
        )
        return result.scalars().first()


async def save_raw_note(profile: Profile, content: str) -> int:
    """Cadangan kalau AI gagal: pesan tetap tersimpan apa adanya."""
    async with SessionLocal() as session:
        note = Note(user_id=profile.id, content=content, source="telegram")
        session.add(note)
        await session.commit()
        await session.refresh(note)
        return note.id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)

    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    name = f", {profile.full_name}" if profile.full_name else ""
    await update.effective_message.reply_text(
        f"Halo{name}! Akun kamu sudah terhubung.\n\n"
        "Perintah langsung (tanpa LLM):\n"
        "• /areas — lihat daftar area hidup\n"
        "• /tasks — lihat daftar tugas pending\n"
        "• /done <id> — tandai tugas selesai\n"
        "• /habits — lihat progres habit harian\n"
        "• /check <id> — centang habit\n"
        "• /timer — lihat status timer aktif\n"
        "• /stop — hentikan timer aktif\n"
        "• /night [HH:MM] — atur batas jam kerja malam\n"
        "• /chill — menu mode jeda (YouTube Music, kopi, film, hangout)\n"
        "• /kopi — pesan kopi cepat di ShopeeFood\n\n"
        "Contoh pesan chat (diproses AI):\n"
        "• area saya: Kuliah, Usaha, Pribadi\n"
        "• ide: bikin fitur export notes ke markdown\n"
        "• mulai ngoding second brain\n"
        "• udahan dulu\n"
        "• jenuh banget nih, puterin lagu santai\n"
        "• rekap hari ini\n"
        "• cari catatan soal vue"
    )


async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    message = update.effective_message

    existing = await get_profile_by_chat_id(chat_id)
    if existing is not None:
        await message.reply_text("Akun ini sudah terhubung.")
        return

    if not context.args:
        await message.reply_text("Format: /connect KODE-KAMU")
        return

    code = context.args[0].strip().upper()

    async with SessionLocal() as session:
        result = await session.execute(
            select(InviteCode)
            .where(
                InviteCode.code == code,
                col(InviteCode.used_at).is_(None),
                InviteCode.expires_at > utcnow(),
            )
            .with_for_update()
        )
        invite = result.scalars().first()

        if invite is None:
            await message.reply_text(
                "Kode tidak valid, sudah dipakai, atau sudah kedaluwarsa."
            )
            return

        # Disalin sebelum commit: setelah commit objek bisa expired dan
        # akses atributnya memicu lazy-load yang tidak valid di konteks async.
        full_name = invite.full_name

        existing_profile = await session.get(Profile, invite.auth_user_id)
        if existing_profile is not None:
            await message.reply_text(
                "Profil untuk akun ini sudah terdaftar atau sudah terhubung ke Telegram."
            )
            return

        session.add(
            Profile(
                id=invite.auth_user_id,
                full_name=full_name,
                telegram_chat_id=chat_id,
            )
        )
        invite.used_at = utcnow()
        invite.used_by_chat_id = chat_id
        await session.commit()

    logger.info("Profil baru terhubung lewat invite code, chat_id=%s", chat_id)

    name = f", {full_name}" if full_name else ""
    await message.reply_text(
        f"Berhasil terhubung{name}! Kirim /start untuk melihat contoh perintah."
    )


def generate_invite_code() -> str:
    """Format: SB-XXXX-XXXX menggunakan hex uppercase acak."""
    part1 = secrets.token_hex(2).upper()
    part2 = secrets.token_hex(2).upper()
    return f"SB-{part1}-{part2}"


async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    message = update.effective_message

    # Chat non-admin yang memanggil /invite diperlakukan seolah perintah tidak ada
    if settings.ADMIN_CHAT_ID is None or chat_id != settings.ADMIN_CHAT_ID:
        return

    if not context.args or len(context.args) < 2:
        await message.reply_text("Format: /invite <nama> <email>")
        return

    email = context.args[-1].strip().lower()
    full_name = " ".join(context.args[:-1]).strip()

    if "@" not in email or "." not in email:
        await message.reply_text("Email tidak valid. Format: /invite <nama> <email>")
        return

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        await message.reply_text(
            "SUPABASE_URL atau SUPABASE_SERVICE_ROLE_KEY belum dikonfigurasi di backend."
        )
        return

    admin_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin/users"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }

    user_id: UUID | None = None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                admin_url,
                headers=headers,
                json={
                    "email": email,
                    "email_confirm": True,
                    "user_metadata": {"full_name": full_name},
                },
            )

            if resp.status_code in (200, 201):
                user_id = UUID(resp.json()["id"])
            elif resp.status_code == 422:
                logger.info(
                    "User %s sudah terdaftar di Supabase Auth (422), mengambil UUID eksisting",
                    email,
                )
                get_resp = await client.get(admin_url, headers=headers)
                if get_resp.status_code == 200:
                    data = get_resp.json()
                    users_list = (
                        data.get("users", data) if isinstance(data, dict) else data
                    )
                    for u in users_list:
                        if u.get("email", "").lower() == email:
                            user_id = UUID(u["id"])
                            break

                # Fallback: jika pagination API tidak memuat user, query langsung ke auth.users
                if user_id is None:
                    async with SessionLocal() as session:
                        result = await session.execute(
                            text(
                                "SELECT id FROM auth.users WHERE lower(email) = lower(:email) LIMIT 1"
                            ),
                            {"email": email},
                        )
                        row = result.first()
                        if row:
                            user_id = (
                                row[0]
                                if isinstance(row[0], UUID)
                                else UUID(str(row[0]))
                            )

                if user_id is None:
                    await message.reply_text(
                        f"User {email} sudah terdaftar di auth.users, tetapi gagal mengambil UUID-nya."
                    )
                    return
            else:
                logger.error(
                    "Supabase Admin API error (%s): %s", resp.status_code, resp.text
                )
                await message.reply_text(
                    f"Gagal memproses user di Supabase Auth ({resp.status_code}): {resp.text[:200]}"
                )
                return
    except Exception as e:
        logger.exception("Gagal menghubungi Supabase Auth Admin API")
        await message.reply_text(f"Terjadi kesalahan saat memproses Supabase Auth: {e}")
        return

    code = generate_invite_code()
    expires_at = utcnow() + timedelta(days=7)

    async with SessionLocal() as session:
        invite_entry = InviteCode(
            code=code,
            auth_user_id=user_id,
            full_name=full_name,
            expires_at=expires_at,
        )
        session.add(invite_entry)
        await session.commit()

    local_tz = ZoneInfo(settings.APP_TIMEZONE)
    exp_str = expires_at.astimezone(local_tz).strftime("%d %b %Y %H:%M")

    await message.reply_text(
        f"Kode undangan untuk {full_name} ({email}):\n\n"
        f"/connect {code}\n\n"
        f"Berlaku hingga {exp_str}."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat_id = update.effective_chat.id
    text = message.text.strip()

    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await message.reply_text(NOT_LINKED_MSG.format(chat_id=chat_id))
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        reply = await run_agent(profile.id, chat_id, text)
    except Exception:
        logger.exception("Agent gagal memproses pesan dari chat_id=%s", chat_id)
        note_id = await save_raw_note(profile, text)
        reply = f"⚠️ AI sedang bermasalah, tapi pesanmu sudah disimpan sebagai catatan mentah (#{note_id})."

    await message.reply_text(reply[:TELEGRAM_MAX_LEN])


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat_id = update.effective_chat.id

    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await message.reply_text(NOT_LINKED_MSG.format(chat_id=chat_id))
        return

    voice_or_audio = message.voice or message.audio
    if not voice_or_audio:
        return

    if voice_or_audio.duration and voice_or_audio.duration > 300:
        await message.reply_text("⚠️ Rekaman suara maksimal 5 menit.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # 1. Unduh audio bytes dari Telegram
    try:
        tg_file = await context.bot.get_file(voice_or_audio.file_id)
        audio_bytearray = await tg_file.download_as_bytearray()
        audio_bytes = bytes(audio_bytearray)
    except Exception:
        logger.exception("Gagal mengunduh audio Telegram chat_id=%s", chat_id)
        await message.reply_text("⚠️ Gagal mengunduh rekaman suara dari Telegram. Coba kirim ulang.")
        return

    mime_type = getattr(voice_or_audio, "mime_type", None) or "audio/ogg"

    # 2. Transkripsi dengan Gemini Multimodal
    try:
        from google.genai import Client, types
        genai_client = Client(api_key=settings.GOOGLE_API_KEY)
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        prompt = (
            "Transkripsikan pesan suara bahasa Indonesia ini secara akurat kata demi kata. "
            "Koreksi kesalahan ejaan kecil yang wajar bila jelas konteksnya. "
            "Hanya berikan teks hasil transkripsi tanpa tanda kutip, tanpa kata pengantar, dan tanpa penutup apapun."
        )
        response = genai_client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[audio_part, prompt],
        )
        transcribed_text = response.text.strip() if response and response.text else ""
    except Exception:
        logger.exception("Gagal transkripsi suara Gemini chat_id=%s", chat_id)
        await message.reply_text("⚠️ Gagal mentranskripsikan suara saat menghubungi AI. Coba lagi sebentar atau ketik langsung.")
        return

    if not transcribed_text:
        await message.reply_text("🎙️ Suara tidak terdengar jelas atau kosong. Silakan coba lagi.")
        return

    # 3. Proses lewat Agent
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        reply = await run_agent(profile.id, chat_id, transcribed_text)
    except Exception:
        logger.exception("Agent gagal memproses suara dari chat_id=%s", chat_id)
        note_id = await save_raw_note(profile, f"[Voice Note]: {transcribed_text}")
        reply = f"⚠️ AI bermasalah saat memproses aksi, tapi transkripsi sudah disimpan sebagai catatan mentah (#{note_id})."

    formatted_reply = f"🎙️ \"{transcribed_text}\"\n\n{reply}"
    await message.reply_text(formatted_reply[:TELEGRAM_MAX_LEN])


async def areas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(Area).where(Area.user_id == profile.id).order_by(Area.position.asc())
        )
        areas = result.scalars().all()

    if not areas:
        await update.effective_message.reply_text(
            "Kamu belum memiliki area hidup.\n\n"
            "Contoh untuk mengatur area: kirim\n"
            "area saya: Kuliah, Usaha, Pribadi"
        )
        return

    lines = ["Daftar Area:"]
    for a in areas:
        lines.append(f"{a.position}. {a.name}")
    await update.effective_message.reply_text("\n".join(lines))


async def tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    async with SessionLocal() as session:
        tasks_res = await session.execute(
            select(Task).where(Task.user_id == profile.id, Task.status == "pending")
        )
        tasks = tasks_res.scalars().all()

        areas_res = await session.execute(
            select(Area).where(Area.user_id == profile.id).order_by(Area.position.asc())
        )
        areas = areas_res.scalars().all()

    if not tasks:
        await update.effective_message.reply_text("Tidak ada tugas pending.")
        return

    today = datetime.now(LOCAL_TZ).date()
    prioritized = prioritize_tasks(tasks, areas, today)

    lines = ["Daftar Tugas Pending:"]
    for item in prioritized:
        task = item.task
        area_tag = f"[{item.area_name}] "
        urgent_tag = "[MENDESAK] " if task.is_urgent else ""
        lines.append(f"#{task.id} {area_tag}{urgent_tag}{task.title} — {item.reason}")

    lines.append("\nGunakan /done <id> untuk menandai selesai.")
    await update.effective_message.reply_text("\n".join(lines))


async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    if not context.args:
        await update.effective_message.reply_text("Format: /done <id>\nContoh: /done 1")
        return

    raw_id = context.args[0].lstrip("#").strip()
    if not raw_id.isdigit():
        await update.effective_message.reply_text(
            "ID tugas harus berupa angka. Contoh: /done 1"
        )
        return

    task_id = int(raw_id)
    async with SessionLocal() as session:
        result = await session.execute(
            select(Task).where(Task.id == task_id, Task.user_id == profile.id)
        )
        task = result.scalars().first()
        if task is None:
            await update.effective_message.reply_text(
                f"Tugas #{task_id} tidak ditemukan."
            )
            return

        if task.status == "completed":
            await update.effective_message.reply_text(
                f"Tugas #{task_id} ('{task.title}') sudah selesai."
            )
            return

        # PENTING: status dan completed_at WAJIB diisi dalam satu operasi (constraint tasks_completed_consistent)
        task.status = "completed"
        task.completed_at = utcnow()
        session.add(task)
        await session.commit()
        title = task.title

    await update.effective_message.reply_text(f"✅ Selesai: #{task_id} - {title}")


async def habits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    today = datetime.now(LOCAL_TZ).date()
    async with SessionLocal() as session:
        habits_status = await get_user_habits_status(session, profile.id, today)

    if not habits_status:
        await update.effective_message.reply_text(
            "Kamu belum memiliki habit terdaftar.\n\n"
            "Contoh menambah habit:\n"
            "Kirim chat: 'buat habit: Olahraga 15 menit' atau 'habit baru: Baca jurnal'"
        )
        return

    day_name = INDO_DAYS[today.weekday()]
    month_name = INDO_MONTHS[today.month - 1]
    date_header = f"{day_name}, {today.day} {month_name} {today.year}"

    completed_count = sum(1 for h in habits_status if h.is_completed_today)
    total_count = len(habits_status)

    lines = [
        f"🌱 Habit Hari Ini ({date_header}):\n"
        f"Progres: {completed_count}/{total_count} selesai\n"
    ]
    for h in habits_status:
        box = "[✓]" if h.is_completed_today else "[ ]"
        streak_str = f" 🔥 {h.streak} hari" if h.streak > 0 else ""
        lines.append(f"#{h.habit.id} {box} {h.habit.name}{streak_str}")

    lines.append("\nCentang habit: /check <id>\nContoh: /check 1")
    await update.effective_message.reply_text("\n".join(lines))


async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Format: /check <id>\nContoh: /check 1"
        )
        return

    raw_id = context.args[0].lstrip("#").strip()
    if not raw_id.isdigit():
        await update.effective_message.reply_text(
            "ID habit harus berupa angka. Contoh: /check 1"
        )
        return

    habit_id = int(raw_id)
    today = datetime.now(LOCAL_TZ).date()

    async with SessionLocal() as session:
        habit, already_done, streak = await check_habit_for_today(
            session, profile.id, habit_id, today
        )

    if habit is None:
        # Pesan identik untuk ID fiktif dan ID milik pengguna lain (Aturan 3 & Keamanan)
        await update.effective_message.reply_text(f"Habit #{habit_id} tidak ditemukan.")
        return

    streak_suffix = (
        f" 🔥 {streak} hari berturut-turut!"
        if streak > 1
        else (" 🔥 Hari ke-1!" if streak == 1 else "")
    )
    if already_done:
        await update.effective_message.reply_text(
            f"Habit #{habit.id} ('{habit.name}') sudah dicentang hari ini.{streak_suffix}"
        )
    else:
        await update.effective_message.reply_text(
            f"✅ Mantap! Habit #{habit.id} ('{habit.name}') selesai hari ini.{streak_suffix}"
        )


async def timer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(TimeLog).where(
                TimeLog.user_id == profile.id, col(TimeLog.ended_at).is_(None)
            )
        )
        running = result.scalars().first()

    if running is None:
        await update.effective_message.reply_text(
            "Tidak ada timer yang sedang berjalan.\n\n"
            "Untuk mulai fokus, kirim chat: 'mulai [nama project]'"
        )
        return

    now_utc = utcnow()
    started_at = running.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    elapsed = int((now_utc - started_at).total_seconds() // 60)
    started_local = started_at.astimezone(LOCAL_TZ).strftime("%H:%M")

    await update.effective_message.reply_text(
        f"⏱️ Timer Aktif: '{running.project_name}'\n"
        f"Mulai: pukul {started_local} (berjalan {elapsed} menit)\n\n"
        "Ketik /stop untuk menghentikan timer."
    )


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(TimeLog).where(
                TimeLog.user_id == profile.id, col(TimeLog.ended_at).is_(None)
            )
        )
        running = result.scalars().first()
        if running is None:
            await update.effective_message.reply_text(
                "Tidak ada timer yang sedang berjalan."
            )
            return

        started_at = running.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        running.ended_at = utcnow()
        running.duration_minutes = int(
            (running.ended_at - started_at).total_seconds() // 60
        )
        project = running.project_name
        duration = running.duration_minutes
        session.add(running)
        await session.commit()

    await update.effective_message.reply_text(
        f"⏹️ Timer '{project}' dihentikan.\n"
        f"Total durasi fokus: {duration} menit. Kerja bagus!"
    )


async def night_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    if not context.args:
        cutoff = profile.night_cutoff_time or time(23, 0)
        await update.effective_message.reply_text(
            f"🌙 Batas jam kerja malammu saat ini diatur ke pukul <b>{cutoff.strftime('%H:%M')}</b>.\n\n"
            f"Untuk mengubahnya, ketik:\n"
            f"<code>/night HH:MM</code> (contoh: <code>/night 22:30</code>)",
            parse_mode=ParseMode.HTML,
        )
        return

    raw_val = context.args[0].strip()
    try:
        new_time = datetime.strptime(raw_val, "%H:%M").time()
    except ValueError:
        await update.effective_message.reply_text(
            "❌ Format jam tidak valid. Gunakan format 24 jam <code>HH:MM</code>, contoh: <code>/night 22:30</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    async with SessionLocal() as session:
        p = await session.get(Profile, profile.id)
        if p:
            p.night_cutoff_time = new_time
            session.add(p)
            await session.commit()

    await update.effective_message.reply_text(
        f"✅ Batas jam kerja malam berhasil diubah ke pukul <b>{new_time.strftime('%H:%M')}</b>.",
        parse_mode=ParseMode.HTML,
    )


async def chill_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    text = (
        "🌿 <b>Mode Jeda — Saatnya Rehat Sejenak</b>\n\n"
        "Pikiran butuh waktu jeda agar kembali jernih dan segar. "
        "Pilih mood booster yang kamu inginkan di bawah ini:"
    )
    await update.effective_message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=build_chill_menu_keyboard(),
    )


async def coffee_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    text = (
        "☕ <b>Pesan Kopi di ShopeeFood</b>\n\n"
        "Pilih menu kopi favoritmu untuk langsung membuka pencarian di ShopeeFood:"
    )
    await update.effective_message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=build_coffee_keyboard(),
    )


async def chill_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data or ""

    if data == "chill:main":
        text = (
            "🌿 <b>Mode Jeda — Saatnya Rehat Sejenak</b>\n\n"
            "Pikiran butuh waktu jeda agar kembali jernih dan segar. "
            "Pilih mood booster yang kamu inginkan di bawah ini:"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=build_chill_menu_keyboard(),
        )
    elif data == "chill:music":
        text = (
            "🎵 <b>Pilih Soundtrack Relaksasimu (YouTube Music)</b>\n\n"
            "Klik salah satu playlist kurasi di bawah untuk langsung memutar musik pengembali mood:"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=build_music_keyboard(),
        )
    elif data == "chill:coffee":
        text = (
            "☕ <b>Pesan Kopi di ShopeeFood</b>\n\n"
            "Pilih menu kopi favoritmu untuk langsung membuka pencarian di ShopeeFood:"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=build_coffee_keyboard(),
        )
    elif data == "chill:movie":
        m = get_random_movie()
        text = (
            f"🎬 <b>Rekomendasi Tontonan Ringan</b>\n\n"
            f"<b>{m['title']}</b> ({m['type']})\n"
            f"• <b>Genre:</b> {m['genre']}\n"
            f"• <b>Platform:</b> {m['platform']}\n\n"
            f"💡 <i>{m['reason']}</i>"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=build_movie_keyboard(),
        )
    elif data == "chill:hangout":
        act = get_random_activity()
        text = (
            f"🚶‍♂️ <b>Ide Reset Pikiran & Hangout</b>\n\n"
            f"<b>{act['title']}</b>\n\n"
            f"{act['detail']}"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=build_hangout_keyboard(),
        )


async def weekly_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    profile = await get_profile_by_chat_id(chat_id)
    if profile is None:
        await update.effective_message.reply_text(
            NOT_LINKED_MSG.format(chat_id=chat_id)
        )
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    today = datetime.now(LOCAL_TZ).date()

    async with SessionLocal() as session:
        stats = await get_weekly_stats(session, profile.id, today)

    insight = await generate_weekly_insight_llm(stats)
    report_html = format_weekly_report_html(stats, insight=insight)

    await update.effective_message.reply_text(
        report_html,
        parse_mode=ParseMode.HTML,
    )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Error saat memproses update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Gagal memproses pesan. Coba lagi sebentar."
        )


private = filters.ChatType.PRIVATE
ptb_app.add_handler(CommandHandler("start", start, filters=private))
ptb_app.add_handler(CommandHandler("connect", connect, filters=private))
ptb_app.add_handler(CommandHandler("invite", invite, filters=private))
ptb_app.add_handler(CommandHandler(["areas", "area"], areas_cmd, filters=private))
ptb_app.add_handler(CommandHandler(["tasks", "tugas"], tasks_cmd, filters=private))
ptb_app.add_handler(CommandHandler("done", done_cmd, filters=private))
ptb_app.add_handler(CommandHandler(["habits", "habit"], habits_cmd, filters=private))
ptb_app.add_handler(CommandHandler("check", check_cmd, filters=private))
ptb_app.add_handler(CommandHandler(["timer", "status"], timer_cmd, filters=private))
ptb_app.add_handler(CommandHandler("stop", stop_cmd, filters=private))
ptb_app.add_handler(CommandHandler(["night", "bedtime"], night_cmd, filters=private))
ptb_app.add_handler(
    CommandHandler(["chill", "recharge", "jeda"], chill_cmd, filters=private)
)
ptb_app.add_handler(CommandHandler(["kopi", "coffee"], coffee_cmd, filters=private))
ptb_app.add_handler(CommandHandler(["weekly", "laporan"], weekly_cmd, filters=private))
ptb_app.add_handler(CallbackQueryHandler(chill_callback, pattern=r"^chill:"))
ptb_app.add_handler(
    MessageHandler(
        private & filters.UpdateType.MESSAGE & (filters.VOICE | filters.AUDIO),
        handle_voice_message,
    )
)
# UpdateType.MESSAGE = abaikan pesan yang di-edit (supaya tidak diproses dua kali)
ptb_app.add_handler(
    MessageHandler(
        private & filters.UpdateType.MESSAGE & filters.TEXT & ~filters.COMMAND,
        handle_message,
    )
)
ptb_app.add_error_handler(on_error)

# Daftarkan periodic checker untuk Brief Pagi
setup_brief_scheduler(ptb_app)
