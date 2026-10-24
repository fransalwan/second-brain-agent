# apps/backend/app/ambient.py
"""Modul logika ambient tracking: pelacakan otomatis via OS watcher / VS Code."""

from datetime import datetime, time, timezone
import html
import logging
import re
from typing import Any, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlmodel import col, select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram.constants import ParseMode

from .config import settings
from .habits import check_habit_for_today, get_user_habits_status
from .models import (
    Area,
    CourseAssignment,
    ExperimentMetric,
    Habit,
    HabitLog,
    Note,
    Profile,
    SupervisionLog,
    Task,
    ThesisChapter,
    TimeLog,
    utcnow,
)
from .scheduler import is_past_night_cutoff

logger = logging.getLogger(__name__)
LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)


def _fmt_duration(minutes: int) -> str:
    """Format menit ke format jam dan menit yang ramah dibaca."""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0 and mins > 0:
        return f"{hours} jam {mins} menit"
    elif hours > 0:
        return f"{hours} jam"
    return f"{mins} menit"


def _diff_seconds(t1: datetime, t2: datetime) -> float:
    """Hitung selisih detik antara t1 dan t2, aman untuk offset-naive (SQLite) & offset-aware (PostgreSQL)."""
    if t1.tzinfo is not None and t2.tzinfo is None:
        t2 = t2.replace(tzinfo=timezone.utc)
    elif t1.tzinfo is None and t2.tzinfo is not None:
        t1 = t1.replace(tzinfo=timezone.utc)
    return (t1 - t2).total_seconds()


async def get_profile_by_email(session: AsyncSession, email: str) -> Optional[Profile]:
    """Cari profil user berdasarkan email (case-insensitive) dengan fallback alias universitas & github."""
    clean_email = email.strip().lower()
    res = await session.execute(select(Profile).where(Profile.email == clean_email))
    profile = res.scalars().first()
    if profile:
        return profile

    # Alias fallback untuk akun Frans Alwan Purba
    frans_aliases = {
        "fransalwanpurba@mail.ugm.ac.id": "fransalwan55@gmail.com",
        "fransalwan": "fransalwan55@gmail.com",
        "fransalwan55@gmail.com": "fransalwanpurba@mail.ugm.ac.id",
    }
    alt_email = frans_aliases.get(clean_email)
    if alt_email:
        res_alt = await session.execute(select(Profile).where(Profile.email == alt_email))
        profile = res_alt.scalars().first()
        if profile:
            return profile

    # Fallback jika email commit mengandung 'fransalwan' atau 'frans'
    if "frans" in clean_email:
        res_like = await session.execute(
            select(Profile).where(col(Profile.email).contains("frans"))
        )
        profile = res_like.scalars().first()
        if profile:
            return profile

    return None


async def start_ambient_timer(
    session: AsyncSession,
    email: str,
    project_name: str,
    source: str = "vscode",
    context: Optional[str] = None,
    notify_telegram: bool = True,
    bot: Optional[Any] = None,
) -> dict:
    """Memulai timer fokus secara otomatis dari ambient watcher."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    clean_project = project_name.strip()
    if not clean_project:
        return {"status": "error", "message": "project_name tidak boleh kosong"}

    # Cek timer aktif saat ini
    res = await session.execute(
        select(TimeLog).where(
            TimeLog.user_id == profile.id,
            col(TimeLog.ended_at).is_(None),
        )
    )
    running = res.scalars().first()

    # 1. Idempotent: jika project yang sama sudah berjalan, jangan buat timer ganda
    if running and running.project_name.lower() == clean_project.lower():
        now_utc = utcnow()
        elapsed_min = int(max(0, _diff_seconds(now_utc, running.started_at)) // 60)
        return {
            "status": "already_running",
            "project": running.project_name,
            "started_at": running.started_at.isoformat(),
            "elapsed_minutes": elapsed_min,
        }

    # 2. Context Switching: jika project lain sedang jalan, selesaikan dulu project lama
    switched_from = None
    if running:
        switched_from = running.project_name
        running.ended_at = utcnow()
        duration_sec = _diff_seconds(running.ended_at, running.started_at)
        if duration_sec < 60:
            # Sesi mikro kurang dari 1 menit -> abaikan
            await session.delete(running)
        else:
            running.duration_minutes = int(duration_sec // 60)
            session.add(running)
        await session.commit()

    # 3. Cek Night Cutoff (Bedtime Guardian)
    night_cutoff = (
        profile.night_cutoff_time if profile.night_cutoff_time else time(23, 0)
    )
    now_local = datetime.now(LOCAL_TZ)
    is_late_night = is_past_night_cutoff(now_local.time(), night_cutoff)

    # 4. Buat TimeLog baru
    new_timer = TimeLog(
        user_id=profile.id,
        project_name=clean_project,
        night_warning_sent=is_late_night,
    )
    session.add(new_timer)
    await session.commit()
    await session.refresh(new_timer)

    # 5. Notifikasi Telegram Pasif (jika user punya chat ID dan bot aktif)
    if notify_telegram and profile.telegram_chat_id and bot:
        try:
            msg = (
                f"⏱️ <b>[Auto-Timer]</b> Sesi fokus dimulai untuk: "
                f"<b>{html.escape(clean_project)}</b> (via {html.escape(source)})"
            )
            if context:
                msg += f"\n🎯 <i>Aktivitas: {html.escape(context)}</i>"
            if switched_from:
                msg += f"\n<i>(Menggantikan sesi sebelumnya: {html.escape(switched_from)})</i>"
            if is_late_night:
                cutoff_str = night_cutoff.strftime("%H:%M")
                curr_str = now_local.strftime("%H:%M")
                msg += (
                    f"\n\n⚠️ <i>Peringatan: Sekarang pukul {curr_str}, "
                    f"melewati batas jam kerja ({cutoff_str}). Jangan begadang ya!</i>"
                )
            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"Gagal mengirim notif Telegram ambient start: {e}")

    return {
        "status": "started",
        "project": new_timer.project_name,
        "started_at": new_timer.started_at.isoformat(),
        "is_late_night": is_late_night,
    }


async def stop_ambient_timer(
    session: AsyncSession,
    email: str,
    project_name: Optional[str] = None,
    reason: str = "window_closed",
    notify_telegram: bool = True,
    bot: Optional[Any] = None,
) -> dict:
    """Menghentikan timer fokus secara otomatis saat window ditutup atau idle."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    res = await session.execute(
        select(TimeLog).where(
            TimeLog.user_id == profile.id,
            col(TimeLog.ended_at).is_(None),
        )
    )
    running = res.scalars().first()

    if not running:
        return {
            "status": "no_active_timer",
            "message": "Tidak ada timer yang sedang berjalan",
        }

    if project_name and running.project_name.lower() != project_name.strip().lower():
        return {
            "status": "ignored",
            "reason": "different_project_running",
            "running_project": running.project_name,
        }

    # Hitung durasi
    now_utc = utcnow()
    duration_sec = _diff_seconds(now_utc, running.started_at)
    project = running.project_name

    # Filter sesi mikro (< 60 detik)
    if duration_sec < 60:
        await session.delete(running)
        await session.commit()
        return {
            "status": "discarded",
            "project": project,
            "reason": "duration_too_short",
            "duration_seconds": int(duration_sec),
        }

    duration_min = int(duration_sec // 60)
    running.ended_at = now_utc
    running.duration_minutes = duration_min
    session.add(running)
    await session.commit()

    # Otomatis centang habit kerja/ngoding jika durasi memenuhi syarat (>= 15 menit)
    auto_habits = await auto_check_habits_on_focus(
        session=session,
        user_id=profile.id,
        project_name=project,
        duration_minutes=duration_min,
        min_minutes=15,
    )

    # Notifikasi ringkasan pasif jika durasi cukup berarti (>= 2 menit)
    if notify_telegram and profile.telegram_chat_id and bot and duration_min >= 2:
        try:
            dur_text = _fmt_duration(duration_min)
            reason_label = (
                "VS Code ditutup" if reason == "window_closed" else "Waktu idle / jeda"
            )
            msg = (
                f"⏱️ <b>[Auto-Timer]</b> Sesi fokus selesai: <b>{html.escape(project)}</b>\n"
                f"⏳ Durasi: <b>{dur_text}</b> ({reason_label})\n"
            )
            if auto_habits:
                msg += "🔥 <b>Habit Harian Otomatis Dicentang:</b>\n"
                for ah in auto_habits:
                    msg += f"• <b>{html.escape(ah['name'])}</b> (Streak: {ah['streak']} hari 🔥)\n"
            msg += "Data berhasil disinkronkan ke dashboard! 🎯"
            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"Gagal mengirim notif Telegram ambient stop: {e}")

    return {
        "status": "stopped",
        "project": project,
        "duration_minutes": duration_min,
        "reason": reason,
        "auto_checked_habits": auto_habits,
    }


DEFAULT_WORK_HABIT_KEYWORDS = {
    "ngoding",
    "coding",
    "code",
    "fokus",
    "deep work",
    "kerja",
    "work",
    "project",
    "belajar",
    "riset",
    "program",
    "build",
}


async def auto_check_habits_on_focus(
    session: AsyncSession,
    user_id: UUID,
    project_name: str,
    duration_minutes: int,
    min_minutes: int = 15,
) -> list[dict]:
    """Mencari dan mencentang habit kerja/ngoding yang cocok jika durasi fokus memenuhi syarat."""
    if duration_minutes < min_minutes:
        return []

    today = datetime.now(LOCAL_TZ).date()
    statuses = await get_user_habits_status(session, user_id, today)

    project_words = {w.lower() for w in project_name.split() if len(w) > 2}

    checked = []
    for s in statuses:
        if s.is_completed_today:
            continue
        h_name_lower = s.habit.name.lower()
        is_match = any(kw in h_name_lower for kw in DEFAULT_WORK_HABIT_KEYWORDS) or any(
            pw in h_name_lower for pw in project_words
        )
        if is_match and s.habit.id is not None:
            habit, already_done, streak = await check_habit_for_today(
                session, user_id, s.habit.id, today
            )
            if habit and not already_done:
                checked.append(
                    {
                        "id": habit.id,
                        "name": habit.name,
                        "streak": streak,
                    }
                )
    return checked


async def check_habit_by_keyword(
    session: AsyncSession,
    email: str,
    habit_keyword: str,
    notify_telegram: bool = True,
    bot: Optional[Any] = None,
) -> dict:
    """Mencentang habit berdasarkan nama atau kata kunci (untuk trigger ambient mandiri)."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    today = datetime.now(LOCAL_TZ).date()
    statuses = await get_user_habits_status(session, profile.id, today)

    kw_lower = habit_keyword.strip().lower()
    target_status = None
    for s in statuses:
        if kw_lower in s.habit.name.lower():
            target_status = s
            break

    if not target_status or target_status.habit.id is None:
        return {
            "status": "not_found",
            "message": f"Tidak ditemukan habit aktif yang mengandung kata '{habit_keyword}'",
        }

    habit, already_done, streak = await check_habit_for_today(
        session, profile.id, target_status.habit.id, today
    )
    if not habit:
        return {"status": "error", "message": "Gagal memproses habit"}

    if notify_telegram and profile.telegram_chat_id and bot and not already_done:
        try:
            msg = (
                f"🔥 <b>[Auto-Habit]</b> Habit harian berhasil dicentang!\n"
                f"🎯 <b>{html.escape(habit.name)}</b>\n"
                f"⚡ Streak saat ini: <b>{streak} hari berturut-turut!</b>"
            )
            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"Gagal mengirim notif Telegram auto habit: {e}")

    return {
        "status": "success",
        "habit_id": habit.id,
        "habit_name": habit.name,
        "already_completed": already_done,
        "streak": streak,
    }


async def get_ambient_status(session: AsyncSession, email: str) -> dict:
    """Mendapatkan status terkini untuk daemon ambient: timer aktif, area hidup, dll."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    # Timer aktif
    res_timer = await session.execute(
        select(TimeLog).where(
            TimeLog.user_id == profile.id,
            col(TimeLog.ended_at).is_(None),
        )
    )
    running = res_timer.scalars().first()

    active_timer_data = None
    if running:
        elapsed = int(max(0, _diff_seconds(utcnow(), running.started_at)) // 60)
        active_timer_data = {
            "project_name": running.project_name,
            "started_at": running.started_at.isoformat(),
            "elapsed_minutes": elapsed,
        }

    # Area hidup
    res_areas = await session.execute(
        select(Area).where(Area.user_id == profile.id).order_by(Area.position.asc())
    )
    areas = [
        {"id": a.id, "name": a.name, "position": a.position}
        for a in res_areas.scalars().all()
    ]

    return {
        "status": "ok",
        "user": {
            "id": str(profile.id),
            "email": profile.email,
            "full_name": profile.full_name,
            "has_telegram": profile.telegram_chat_id is not None,
        },
        "active_timer": active_timer_data,
        "areas": areas,
    }


async def handle_git_commit_event(
    session: AsyncSession,
    email: str,
    commit_message: str,
    repo_name: Optional[str] = None,
    branch: Optional[str] = None,
    notify_telegram: bool = True,
    bot: Optional[Any] = None,
) -> dict:
    """Memproses event git commit untuk 3 repo akademik (materi-kuliah, thesis-manuscripts, thesis-experiments):
    - Menyelesaikan task yang ID atau kata kuncinya cocok
    - Mengupdate progres Bab Naskah Skripsi (Bab 1 - 5)
    - Menyimpan log bimbingan dospem (anti-ghosting)
    - Mencatat metrik evaluasi eksperimen machine learning
    - Menyelesaikan tugas kuliah (CourseAssignment)
    - Mencatat streak habit harian yang relevan
    """
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    clean_msg = commit_message.strip()
    if not clean_msg:
        return {"status": "ignored", "reason": "empty_commit_message"}

    git_stop_words = {
        "feat", "fix", "chore", "refactor", "docs", "test", "style", "perf",
        "merge", "branch", "update", "wip", "selesaikan", "beres", "kelar",
        "done", "tambah", "ubah", "hapus", "add", "remove", "dan", "yang",
        "di", "ke", "dari", "ini", "itu",
    }
    msg_words = {
        w.lower().strip(".,:;!()[]{}'\"") for w in clean_msg.split() if len(w) > 2
    } - git_stop_words

    completed_tasks = []
    now_utc = utcnow()

    # 1. Ekstrak Task ID eksplisit: #12, task #12, fix #12, tugas 12, dll.
    explicit_ids = set()
    for m in re.finditer(r"#(\d+)", clean_msg):
        explicit_ids.add(int(m.group(1)))
    for m in re.finditer(
        r"(?i)\b(?:tugas|task|id:?|fix|fixes|fixed|closes?|closed|done)\s*#?(\d+)\b",
        clean_msg,
    ):
        explicit_ids.add(int(m.group(1)))

    if explicit_ids:
        # Cari task pending berdasarkan ID yang diekstrak
        res_tasks = await session.execute(
            select(Task).where(
                Task.user_id == profile.id,
                col(Task.id).in_(list(explicit_ids)),
                Task.status == "pending",
            )
        )
        tasks_to_complete = res_tasks.scalars().all()
        for t in tasks_to_complete:
            t.status = "completed"
            t.completed_at = now_utc
            session.add(t)
            completed_tasks.append({"id": t.id, "title": t.title})
        if tasks_to_complete:
            await session.commit()

    # 2. Jika tidak ada task ID eksplisit, coba pencocokan kata kunci judul tugas
    if not completed_tasks:
        res_all_pending = await session.execute(
            select(Task).where(
                Task.user_id == profile.id,
                Task.status == "pending",
            )
        )
        pending_tasks = res_all_pending.scalars().all()

        for t in pending_tasks:
            t_words = {
                w.lower().strip(".,:;!()[]{}'\"") for w in t.title.split() if len(w) > 2
            } - git_stop_words
            overlap = t_words.intersection(msg_words)
            if len(overlap) >= 2 or (len(t_words) == 1 and len(overlap) == 1):
                t.status = "completed"
                t.completed_at = now_utc
                session.add(t)
                completed_tasks.append({"id": t.id, "title": t.title})
                await session.commit()
                break

    # 3. Deteksi Domain Repositori Akademik & Proses Spesifik
    academic_sync = {
        "repo_type": "general",
        "chapter_updated": None,
        "supervision_logged": None,
        "metric_recorded": None,
        "assignment_completed": None,
    }

    norm_repo = (repo_name or "").lower().strip()
    norm_msg = clean_msg.lower()

    is_thesis_manuscript = any(
        kw in norm_repo for kw in ["thesis-manuscripts", "manuscript", "naskah", "skripsi-naskah"]
    ) or any(
        kw in norm_msg for kw in ["bab 1", "bab 2", "bab 3", "bab 4", "bab 5", "chapter 1", "chapter 2", "chapter 3", "chapter 4", "chapter 5", "dospem", "bimbingan skripsi"]
    )

    is_thesis_experiment = any(
        kw in norm_repo for kw in ["thesis-experiments", "experiment", "eksperimen"]
    ) or any(
        kw in norm_msg for kw in ["xgboost", "lightgbm", "catboost", "random forest", "accuracy:", "acc:", "f1:", "auc:", "loss:"]
    )

    is_coursework = any(
        kw in norm_repo for kw in ["materi-kuliah", "kuliah", "coursework", "matkul"]
    ) or any(
        kw in norm_msg for kw in ["tugas kuliah", "praktikum", "kuis", "tubes", "ujian"]
    )

    # A. THESIS MANUSCRIPTS SYNC
    if is_thesis_manuscript and not is_thesis_experiment:
        academic_sync["repo_type"] = "thesis-manuscripts"

        # Deteksi bab naskah skripsi
        chap_num = None
        m_chap = re.search(r"\b(?:bab|chapter)\s*([1-5])\b", norm_msg)
        if m_chap:
            chap_num = int(m_chap.group(1))
        elif "pendahuluan" in norm_msg:
            chap_num = 1
        elif any(k in norm_msg for k in ["tinjauan pustaka", "landasan teori", "kajian pustaka"]):
            chap_num = 2
        elif any(k in norm_msg for k in ["metodologi", "metode penelitian"]):
            chap_num = 3
        elif any(k in norm_msg for k in ["hasil", "pembahasan", "analisis"]):
            chap_num = 4
        elif any(k in norm_msg for k in ["kesimpulan", "saran"]):
            chap_num = 5

        if chap_num:
            from .thesis import get_or_create_thesis_chapters
            await get_or_create_thesis_chapters(session, profile.id)

            res_c = await session.execute(
                select(ThesisChapter).where(
                    ThesisChapter.user_id == profile.id,
                    ThesisChapter.chapter_num == chap_num,
                )
            )
            chap = res_c.scalars().first()
            if chap:
                m_pct = re.search(r"(\d{1,3})\s*%", clean_msg)
                if m_pct:
                    new_prog = min(100, max(0, int(m_pct.group(1))))
                    new_status = "Selesai" if new_prog >= 100 else ("Revisi" if "revisi" in norm_msg else "Drafting")
                elif any(k in norm_msg for k in ["selesai", "acc", "kelar", "done", "final"]):
                    new_prog = 100
                    new_status = "Selesai"
                elif "revisi" in norm_msg:
                    new_prog = min(95, max(chap.progress or 0, 75))
                    new_status = "Revisi"
                elif any(k in norm_msg for k in ["draft", "tulis", "wip", "tambah", "kerjakan"]):
                    new_prog = min(90, max((chap.progress or 0) + 15, 30))
                    new_status = "Drafting"
                else:
                    new_prog = min(95, (chap.progress or 0) + 10)
                    new_status = chap.status if chap.status != "Belum Mulai" else "Drafting"

                chap.progress = new_prog
                chap.status = new_status
                chap.updated_at = now_utc
                session.add(chap)
                await session.commit()
                academic_sync["chapter_updated"] = {
                    "chapter_num": chap.chapter_num,
                    "title": chap.title,
                    "progress": chap.progress,
                    "status": chap.status,
                }

        # Deteksi notulensi bimbingan dospem
        if any(k in norm_msg for k in ["bimbingan", "dospem", "catatan bimbingan", "feedback dospem", "review pembimbing", "revisi dospem"]):
            new_log = SupervisionLog(
                user_id=profile.id,
                notes=clean_msg,
                action_items="Tercatat otomatis via Git Commit di repo thesis-manuscripts",
                created_at=now_utc,
            )
            session.add(new_log)
            await session.commit()
            academic_sync["supervision_logged"] = clean_msg

    # B. THESIS EXPERIMENTS SYNC
    elif is_thesis_experiment:
        academic_sync["repo_type"] = "thesis-experiments"

        # Model name
        m_model = re.search(r"(?i)\b(XGBoost|LightGBM|CatBoost|Random\s*Forest|MLP|SVM|IDCS[-_]EJOR|IDCS|Baseline|Decision\s*Tree|Deep\s*Learning)\b", clean_msg)
        if m_model:
            model_name = m_model.group(1).strip()
        else:
            m_generic = re.search(r"(?i)(?:model|algo(?:rithm)?)\s*[:=]\s*([a-zA-Z0-9_\-]+)", clean_msg)
            model_name = m_generic.group(1).strip() if m_generic else "IDCS ML Experiment"

        # Metrics
        metrics_parts = []
        m_acc = re.search(r"(?i)\bacc(?:uracy)?\s*[:=]\s*([\d\.]+%?)", clean_msg)
        if m_acc:
            metrics_parts.append(f"Akurasi: {m_acc.group(1)}")
        m_f1 = re.search(r"(?i)\bf1(?:-score)?\s*[:=]\s*([\d\.]+%?)", clean_msg)
        if m_f1:
            metrics_parts.append(f"F1: {m_f1.group(1)}")
        m_auc = re.search(r"(?i)\bauc(?:-roc)?\s*[:=]\s*([\d\.]+%?)", clean_msg)
        if m_auc:
            metrics_parts.append(f"AUC: {m_auc.group(1)}")
        m_loss = re.search(r"(?i)\bloss\s*[:=]\s*([\d\.]+)", clean_msg)
        if m_loss:
            metrics_parts.append(f"Loss: {m_loss.group(1)}")

        # Parameters
        param_parts = []
        m_epoch = re.search(r"(?i)\bepoch[s]?\s*[:=]\s*(\d+)", clean_msg)
        if m_epoch:
            param_parts.append(f"Epoch: {m_epoch.group(1)}")
        m_lr = re.search(r"(?i)\blr\s*[:=]\s*([\d\.e-]+)", clean_msg)
        if m_lr:
            param_parts.append(f"LR: {m_lr.group(1)}")
        m_batch = re.search(r"(?i)\bbatch(?:_size)?\s*[:=]\s*(\d+)", clean_msg)
        if m_batch:
            param_parts.append(f"Batch: {m_batch.group(1)}")

        metrics_summary = ", ".join(metrics_parts) if metrics_parts else clean_msg[:120]
        params_str = ", ".join(param_parts) if param_parts else None

        res_em = await session.execute(
            select(ExperimentMetric).where(
                ExperimentMetric.user_id == profile.id,
                ExperimentMetric.model_name == model_name,
            )
        )
        existing_em = res_em.scalars().first()
        if existing_em:
            existing_em.metrics_summary = metrics_summary
            if params_str:
                existing_em.parameters = params_str
            session.add(existing_em)
        else:
            new_em = ExperimentMetric(
                user_id=profile.id,
                model_name=model_name,
                metrics_summary=metrics_summary,
                parameters=params_str,
                created_at=now_utc,
            )
            session.add(new_em)
        await session.commit()
        academic_sync["metric_recorded"] = {
            "model_name": model_name,
            "metrics_summary": metrics_summary,
            "parameters": params_str,
        }

    # C. COURSEWORK SYNC (materi-kuliah)
    elif is_coursework:
        academic_sync["repo_type"] = "materi-kuliah"

        res_ca = await session.execute(
            select(CourseAssignment).where(
                CourseAssignment.user_id == profile.id,
                CourseAssignment.status == "pending",
            )
        )
        pending_assignments = res_ca.scalars().all()
        matched_assignment = None

        for ca in pending_assignments:
            ca_title_words = {w.lower() for w in ca.title.split() if len(w) > 2}
            ca_course_words = {w.lower() for w in ca.course_name.split() if len(w) > 2}
            overlap = (ca_title_words | ca_course_words).intersection(msg_words)
            if overlap:
                matched_assignment = ca
                break

        if matched_assignment:
            matched_assignment.status = "done"
            matched_assignment.completed_at = now_utc
            session.add(matched_assignment)
            await session.commit()
            academic_sync["assignment_completed"] = {
                "id": matched_assignment.id,
                "course_name": matched_assignment.course_name,
                "title": matched_assignment.title,
            }
        elif any(k in norm_msg for k in ["tugas", "praktikum", "kuis", "tubes"]):
            new_ca = CourseAssignment(
                user_id=profile.id,
                course_name="Materi Kuliah",
                title=clean_msg[:100],
                assignment_type="Individu",
                status="done",
                completed_at=now_utc,
                notes="Diselesaikan via Git Commit di repo materi-kuliah",
                created_at=now_utc,
            )
            session.add(new_ca)
            await session.commit()
            academic_sync["assignment_completed"] = {
                "id": new_ca.id,
                "course_name": new_ca.course_name,
                "title": new_ca.title,
            }

    # 4. Otomatis centang habit harian berdasarkan konteks repository
    project_label = repo_name or "Coding"
    if academic_sync["repo_type"] == "thesis-manuscripts":
        project_label = "Menulis Skripsi"
    elif academic_sync["repo_type"] == "thesis-experiments":
        project_label = "Riset Eksperimen"
    elif academic_sync["repo_type"] == "materi-kuliah":
        project_label = "Belajar Kuliah"

    auto_habits = await auto_check_habits_on_focus(
        session=session,
        user_id=profile.id,
        project_name=project_label,
        duration_minutes=25,
        min_minutes=15,
    )

    # 5. Kirim notifikasi Telegram pasif
    has_academic_activity = any(
        academic_sync.get(k)
        for k in ["chapter_updated", "supervision_logged", "metric_recorded", "assignment_completed"]
    )
    if (
        notify_telegram
        and profile.telegram_chat_id
        and bot
        and (completed_tasks or auto_habits or has_academic_activity)
    ):
        try:
            repo_display = html.escape(repo_name) if repo_name else "local-repo"
            branch_display = f" ({html.escape(branch)})" if branch else ""
            msg = (
                f"🎯 <b>[Git Academic Sync]</b> Commit terdeteksi!\n"
                f"📦 <code>{repo_display}</code>{branch_display}\n"
                f'💬 <i>"{html.escape(clean_msg[:120])}"</i>\n\n'
            )
            if academic_sync.get("chapter_updated"):
                cu = academic_sync["chapter_updated"]
                msg += f"📚 <b>Naskah Skripsi:</b> Bab {cu['chapter_num']} ({html.escape(cu['title'])}) -> <b>{cu['progress']}%</b> [{cu['status']}]\n"
            if academic_sync.get("supervision_logged"):
                msg += f"👨‍🏫 <b>Bimbingan Dospem:</b> Catatan revisi berhasil disimpan ke riset!\n"
            if academic_sync.get("metric_recorded"):
                mr = academic_sync["metric_recorded"]
                msg += f"🧪 <b>Eksperimen AI:</b> {html.escape(mr['model_name'])} ({html.escape(mr['metrics_summary'])})\n"
            if academic_sync.get("assignment_completed"):
                ac = academic_sync["assignment_completed"]
                msg += f"🎓 <b>Tugas Kuliah Selesai:</b> {html.escape(ac['title'])} ({html.escape(ac['course_name'])})\n"

            if completed_tasks:
                msg += "\n✅ <b>Tugas Berhasil Diselesaikan:</b>\n"
                for ct in completed_tasks:
                    msg += f"• <b>{html.escape(ct['title'])}</b> (ID: #{ct['id']})\n"
            if auto_habits:
                msg += "\n🔥 <b>Habit Harian Tercentang:</b>\n"
                for ah in auto_habits:
                    msg += f"• <b>{html.escape(ah['name'])}</b> (Streak: {ah['streak']} hari 🔥)\n"

            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"Gagal mengirim notif Telegram git commit: {e}")

    return {
        "status": "success",
        "completed_tasks": completed_tasks,
        "auto_checked_habits": auto_habits,
        "academic_sync": academic_sync,
        "repo": repo_name,
        "branch": branch,
    }


async def check_bedtime_status(session: AsyncSession, email: str) -> dict:
    """Mengecek status jam malam untuk ambient watcher (sinkronisasi cutoff dari profil DB)."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    night_cutoff = (
        profile.night_cutoff_time if profile.night_cutoff_time else time(23, 0)
    )
    now_local = datetime.now(LOCAL_TZ)
    current_t = now_local.time()
    past_bedtime = is_past_night_cutoff(current_t, night_cutoff)

    cutoff_str = night_cutoff.strftime("%H:%M")
    current_str = now_local.strftime("%H:%M")

    if past_bedtime:
        message = (
            f"🌙 Sudah pukul {current_str} (batas jam malam {cutoff_str}). "
            f"Waktunya istirahat dan simpan pekerjaanmu!"
        )
    else:
        message = (
            f"✅ Masih dalam jam kerja ({current_str}). Batas malam: {cutoff_str}."
        )

    return {
        "status": "ok",
        "is_past_bedtime": past_bedtime,
        "cutoff_time": cutoff_str,
        "current_time": current_str,
        "message": message,
    }


async def handle_quick_capture(
    session: AsyncSession,
    email: str,
    text: str,
    source: str = "quick_capture",
    notify_telegram: bool = True,
    bot: Optional[Any] = None,
) -> dict:
    """Memproses tangkapan ide/tugas cepat dari Global Desktop Quick Capture."""
    import asyncio

    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    clean_text = text.strip()
    if not clean_text:
        return {"status": "error", "message": "Teks tangkapan tidak boleh kosong"}

    reply = ""
    processed_by = "agent_ai"
    try:
        from .agent import run_agent

        chat_id = profile.telegram_chat_id or 0
        # Timeout 10s untuk agent processing (fallback jika hang)
        reply = await asyncio.wait_for(
            run_agent(profile.id, chat_id, clean_text), timeout=10.0
        )
    except asyncio.TimeoutError:
        logger.warning("Agent processing timeout, using Zero Data Loss fallback (note)")
        new_note = Note(
            user_id=profile.id,
            content=clean_text,
            source=source,
            tags=["quick_capture", "inbox"],
        )
        session.add(new_note)
        await session.commit()
        reply = "⏱️ Ide disimpan ke Inbox (agent timeout)"
        processed_by = "note_fallback_timeout"
    except Exception as e:
        logger.warning(
            f"Gagal memproses via AI agent ({type(e).__name__}), fallback: {e}"
        )
        new_note = Note(
            user_id=profile.id,
            content=clean_text,
            source=source,
            tags=["quick_capture", "inbox"],
        )
        session.add(new_note)
        await session.commit()
        reply = "Ide disimpan ke Inbox."
        processed_by = "note_fallback"

    if notify_telegram and profile.telegram_chat_id and bot:
        try:
            msg = (
                f"💡 <b>[Quick Capture]</b> Tangkapan baru diterima:\n"
                f'📝 <i>"{html.escape(clean_text)}"</i>\n\n'
                f"🤖 <b>Respon:</b> {html.escape(reply)}"
            )
            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"Gagal mengirim notif Telegram quick capture: {e}")

    return {
        "status": "success",
        "processed_by": processed_by,
        "reply": reply,
        "text": clean_text,
    }


async def handle_thesis_sync(
    session: AsyncSession,
    email: str,
    experiments_data: Optional[dict] = None,
    manuscripts_data: Optional[dict] = None,
    notify_telegram: bool = True,
    bot: Optional[Any] = None,
) -> dict:
    """Menyinkronkan hasil eksperimen dan catatan bimbingan skripsi dari repo lokal ke database."""
    profile = await get_profile_by_email(session, email)
    if not profile:
        return {
            "status": "error",
            "message": f"User dengan email '{email}' tidak ditemukan",
        }

    synced_metrics = 0
    synced_logs = 0

    # 1. Inisialisasi 5 Bab Tesis jika belum ada
    res_chaps = await session.execute(
        select(ThesisChapter).where(ThesisChapter.user_id == profile.id)
    )
    existing_chaps = res_chaps.scalars().all()
    if not existing_chaps:
        default_chaps = [
            (1, "Pendahuluan & Rumusan Masalah IDCS", "Drafting", 40),
            (2, "Tinjauan Pustaka XAI & Stabilitas SRA", "Drafting", 35),
            (3, "Metodologi Penelitian & Replikasi EJOR", "Drafting", 50),
            (4, "Hasil Eksperimen HMEQ/VUB & Analisis", "Belum Mulai", 15),
            (5, "Kesimpulan, Trade-off & Rekomendasi", "Belum Mulai", 0),
        ]
        for cnum, title, status, prog in default_chaps:
            chap = ThesisChapter(
                user_id=profile.id,
                chapter_num=cnum,
                title=title,
                status=status,
                progress=prog,
            )
            session.add(chap)
        await session.commit()

    # 2. Sync Experiment Metrics dari thesis-experiments
    if experiments_data and "sample_metrics" in experiments_data:
        for m in experiments_data["sample_metrics"]:
            res_m = await session.execute(
                select(ExperimentMetric).where(
                    ExperimentMetric.user_id == profile.id,
                    ExperimentMetric.model_name == m["model_name"],
                )
            )
            existing = res_m.scalars().first()
            if not existing:
                new_metric = ExperimentMetric(
                    user_id=profile.id,
                    model_name=m["model_name"],
                    metrics_summary=m["metrics_summary"],
                    parameters=m.get("parameters"),
                )
                session.add(new_metric)
                synced_metrics += 1
            else:
                existing.metrics_summary = m["metrics_summary"]
                existing.parameters = m.get("parameters")
                session.add(existing)

    # 3. Sync Supervision Logs dari thesis-manuscripts
    if manuscripts_data and "supervision_logs" in manuscripts_data:
        for log in manuscripts_data["supervision_logs"]:
            res_l = await session.execute(
                select(SupervisionLog).where(
                    SupervisionLog.user_id == profile.id,
                    SupervisionLog.notes == log["notes"],
                )
            )
            existing_log = res_l.scalars().first()
            if not existing_log:
                new_log = SupervisionLog(
                    user_id=profile.id,
                    notes=log["notes"],
                    action_items=log.get("action_items"),
                )
                session.add(new_log)
                synced_logs += 1
            elif log.get("action_items"):
                existing_log.action_items = log["action_items"]
                session.add(existing_log)

    await session.commit()

    # Notifikasi Telegram jika bot aktif
    if notify_telegram and profile.telegram_chat_id and bot:
        try:
            tg_msg = (
                f"🔬 <b>[Thesis Sync]</b> Repositori Riset Berhasil Disinkronkan!\n\n"
                f"📊 <b>Eksperimen IDCS:</b> {synced_metrics} metrik baru ter-update ke Tab Riset.\n"
                f"📝 <b>Bimbingan Naskah:</b> {synced_logs} catatan revisi tersinkron.\n"
                f"Tabel metrik siap diekspor ke format LaTeX untuk Bab 4!"
            )
            await bot.send_message(
                chat_id=profile.telegram_chat_id,
                text=tg_msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"Gagal mengirim notif Telegram thesis sync: {e}")

    return {
        "status": "success",
        "synced_metrics": synced_metrics,
        "synced_supervisions": synced_logs,
    }

