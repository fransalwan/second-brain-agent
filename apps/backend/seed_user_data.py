# apps/backend/seed_user_data.py
"""Script seeding data komprehensif untuk pengguna fransalwan55@gmail.com.

Mengisi data realistis di seluruh modul:
- Area hidup (Areas) terurut prioritas
- Tugas pending berbagai tier (Urgent, Near Deadline, Backlog Area) & Tugas completed
- Habit aktif dengan riwayat centang (streaks aktif)
- Sesi fokus (Time Logs) harian & pekanan
- Catatan & ide dengan tags saling terhubung untuk Knowledge Graph
"""

import asyncio
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlmodel import col, delete, select

from app.config import settings
from app.database import SessionLocal
from app.models import Area, Habit, HabitLog, Note, Profile, Task, TimeLog, utcnow

TARGET_EMAIL = "fransalwan55@gmail.com"
LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)


async def seed_data():
    today = datetime.now(LOCAL_TZ).date()

    async with SessionLocal() as session:
        # 1. Cari Profil Pengguna
        prof_res = await session.execute(
            select(Profile).where(Profile.email == TARGET_EMAIL)
        )
        profile = prof_res.scalars().first()

        if not profile:
            print(f"Error: Profil dengan email {TARGET_EMAIL} tidak ditemukan!")
            return

        user_id = profile.id
        print(
            f"Mempersiapkan data seed untuk user: {profile.full_name} ({TARGET_EMAIL}) [ID: {user_id}]"
        )

        # Pastikan konfigurasi profil optimal
        profile.brief_time = time(7, 0)
        profile.night_cutoff_time = time(22, 30)
        session.add(profile)
        await session.commit()

        # 2. Bersihkan data dummy lama (kecuali profil)
        await session.execute(delete(HabitLog).where(HabitLog.user_id == user_id))
        await session.execute(delete(Habit).where(Habit.user_id == user_id))
        await session.execute(delete(Task).where(Task.user_id == user_id))
        await session.execute(delete(Area).where(Area.user_id == user_id))
        await session.execute(delete(TimeLog).where(TimeLog.user_id == user_id))
        await session.execute(delete(Note).where(Note.user_id == user_id))
        await session.commit()
        print("Data lama berhasil dibersihkan untuk inisialisasi baru.")

        # 3. Buat Area Hidup (4 Area Terurut Prioritas)
        areas_data = [
            Area(user_id=user_id, name="Usaha & Karir", position=1),
            Area(user_id=user_id, name="Kuliah & Riset", position=2),
            Area(user_id=user_id, name="Second Brain Agent", position=3),
            Area(user_id=user_id, name="Pribadi & Kesehatan", position=4),
        ]
        for a in areas_data:
            session.add(a)
        await session.commit()

        # Reload areas untuk mendapatkan ID
        areas_res = await session.execute(
            select(Area).where(Area.user_id == user_id).order_by(Area.position.asc())
        )
        areas = {a.name: a.id for a in areas_res.scalars().all()}
        print(f"Berhasil membuat {len(areas)} Area Hidup.")

        # 4. Buat Tugas (Tasks: Tier 1 Urgent, Tier 2 Deadline, Tier 3 Backlog, & Completed)
        # Helper datetime UTC
        def local_dt(d: date, hour: int, minute: int) -> datetime:
            return (
                datetime.combine(d, time(hour, minute))
                .replace(tzinfo=LOCAL_TZ)
                .astimezone(timezone.utc)
            )

        tasks_data = [
            # TIER 1: Urgent (Mendesak)
            Task(
                user_id=user_id,
                area_id=areas["Usaha & Karir"],
                title="Kirim revisi invoice & konfirmasi pembayaran klien",
                is_urgent=True,
                deadline=today,
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Kuliah & Riset"],
                title="Submit bab 3 metodologi penelitian ke portal kampus",
                is_urgent=True,
                deadline=today + timedelta(days=1),
                status="pending",
            ),
            # TIER 2: Mendekati Deadline (Dalam 2-3 hari ke depan)
            Task(
                user_id=user_id,
                area_id=areas["Second Brain Agent"],
                title="Review PR open source & buat rilis release v1.1.0",
                is_urgent=False,
                deadline=today + timedelta(days=2),
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Usaha & Karir"],
                title="Presentasi laporan performa triwulan ke stakeholder",
                is_urgent=False,
                deadline=today + timedelta(days=3),
                status="pending",
            ),
            # TIER 3: Backlog Berdasarkan Bobot Area Hidup
            Task(
                user_id=user_id,
                area_id=areas["Kuliah & Riset"],
                title="Membaca 2 paper jurnal internasional tentang Autonomous AI Agents",
                is_urgent=False,
                deadline=None,
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Second Brain Agent"],
                title="Eksplorasi integrasi export catatan ke format Markdown & PDF",
                is_urgent=False,
                deadline=None,
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Pribadi & Kesehatan"],
                title="Beli biji kopi arabika fresh roast & vitamin harian",
                is_urgent=False,
                deadline=today + timedelta(days=4),
                status="pending",
            ),
            # COMPLETED TASKS (Untuk metrik mingguan & dashboard)
            Task(
                user_id=user_id,
                area_id=areas["Second Brain Agent"],
                title="Implementasi fitur Voice Note Transcriber via Gemini Multimodal Audio",
                is_urgent=True,
                status="completed",
                completed_at=local_dt(today - timedelta(days=1), 16, 30),
            ),
            Task(
                user_id=user_id,
                area_id=areas["Second Brain Agent"],
                title="Buat visualisasi relasi ide interaktif (Knowledge Graph Canvas)",
                is_urgent=False,
                status="completed",
                completed_at=local_dt(today, 11, 45),
            ),
            Task(
                user_id=user_id,
                area_id=areas["Usaha & Karir"],
                title="Setup sistem autentikasi kredensial login & registrasi mandiri",
                is_urgent=False,
                status="completed",
                completed_at=local_dt(today, 14, 20),
            ),
            Task(
                user_id=user_id,
                area_id=areas["Pribadi & Kesehatan"],
                title="Medical check-up rutin bulanan",
                is_urgent=False,
                status="completed",
                completed_at=local_dt(today - timedelta(days=3), 10, 15),
            ),
        ]
        for t in tasks_data:
            session.add(t)
        await session.commit()
        print(f"Berhasil membuat {len(tasks_data)} Tugas (Pending & Selesai).")

        # 5. Buat Habits & Riwayat Centang (Streaks)
        habits_data = [
            Habit(
                user_id=user_id,
                name="Olahraga Pagi 20 Menit",
                position=1,
                is_active=True,
            ),
            Habit(
                user_id=user_id,
                name="Membaca Buku 15 Menit",
                position=2,
                is_active=True,
            ),
            Habit(
                user_id=user_id,
                name="Review Prioritas & Rencana Harian",
                position=3,
                is_active=True,
            ),
            Habit(
                user_id=user_id,
                name="Minum Air Putih 2 Liter",
                position=4,
                is_active=True,
            ),
        ]
        for h in habits_data:
            session.add(h)
        await session.commit()

        # Reload habits untuk ID
        habits_res = await session.execute(
            select(Habit).where(Habit.user_id == user_id).order_by(Habit.position.asc())
        )
        habits_list = habits_res.scalars().all()

        # Buat logs centang streak
        # Habit 1: centang 4 hari berturut-turut (termasuk hari ini) -> streak 4
        # Habit 2: centang 3 hari berturut-turut -> streak 3
        # Habit 3: centang hari ini -> streak 1
        # Habit 4: belum dicentang hari ini (centang kemarin) -> streak 1 tapi siap dicentang hari ini
        habit_logs = []
        for day_offset in range(4):  # today, yesterday, -2, -3
            habit_logs.append(
                HabitLog(
                    user_id=user_id,
                    habit_id=habits_list[0].id,
                    completed_date=today - timedelta(days=day_offset),
                )
            )
        for day_offset in range(3):  # today, yesterday, -2
            habit_logs.append(
                HabitLog(
                    user_id=user_id,
                    habit_id=habits_list[1].id,
                    completed_date=today - timedelta(days=day_offset),
                )
            )
        habit_logs.append(
            HabitLog(user_id=user_id, habit_id=habits_list[2].id, completed_date=today)
        )
        habit_logs.append(
            HabitLog(
                user_id=user_id,
                habit_id=habits_list[3].id,
                completed_date=today - timedelta(days=1),
            )
        )

        for hl in habit_logs:
            session.add(hl)
        await session.commit()
        print(f"Berhasil membuat {len(habits_list)} Habit aktif dengan streak logs.")

        # 6. Buat Sesi Fokus (Time Logs)
        # Sesi hari ini: 60m dan 45m = 105m (1 jam 45 menit fokus)
        # Sesi hari-hari sebelumnya dalam sepekan
        time_logs_data = [
            # Hari ini
            TimeLog(
                user_id=user_id,
                project_name="Second Brain Agent",
                started_at=local_dt(today, 9, 30),
                ended_at=local_dt(today, 10, 30),
                duration_minutes=60,
                break_reminder_sent=False,
            ),
            TimeLog(
                user_id=user_id,
                project_name="Usaha & Karir",
                started_at=local_dt(today, 13, 15),
                ended_at=local_dt(today, 14, 0),
                duration_minutes=45,
                break_reminder_sent=False,
            ),
            # Kemarin
            TimeLog(
                user_id=user_id,
                project_name="Second Brain Agent",
                started_at=local_dt(today - timedelta(days=1), 14, 0),
                ended_at=local_dt(today - timedelta(days=1), 15, 30),
                duration_minutes=90,
                break_reminder_sent=True,
            ),
            # 2 hari lalu
            TimeLog(
                user_id=user_id,
                project_name="Kuliah & Riset",
                started_at=local_dt(today - timedelta(days=2), 10, 0),
                ended_at=local_dt(today - timedelta(days=2), 11, 15),
                duration_minutes=75,
                break_reminder_sent=False,
            ),
            # 3 hari lalu
            TimeLog(
                user_id=user_id,
                project_name="Usaha & Karir",
                started_at=local_dt(today - timedelta(days=3), 15, 0),
                ended_at=local_dt(today - timedelta(days=3), 16, 0),
                duration_minutes=60,
                break_reminder_sent=False,
            ),
            # 4 hari lalu
            TimeLog(
                user_id=user_id,
                project_name="Second Brain Agent",
                started_at=local_dt(today - timedelta(days=4), 16, 0),
                ended_at=local_dt(today - timedelta(days=4), 16, 45),
                duration_minutes=45,
                break_reminder_sent=False,
            ),
        ]
        for tl in time_logs_data:
            session.add(tl)
        await session.commit()
        print(f"Berhasil membuat {len(time_logs_data)} Sesi Fokus (Time Logs).")

        # 7. Buat Catatan & Ide Saling Terhubung (Knowledge Graph)
        notes_data = [
            Note(
                user_id=user_id,
                content="Arsitektur 3-tier priority queue: mendesak (Tier 1), deadline dekat (Tier 2), dan bobot area hidup (Tier 3) untuk menghindari cognitive overload.",
                tags=["prioritas", "arsitektur", "agent"],
                source="telegram",
            ),
            Note(
                user_id=user_id,
                content="Riset multimodal audio Gemini 2.5 Flash: transkripsi suara instan kata per kata untuk input hands-free saat mobile.",
                tags=["agent", "ai", "suara"],
                source="telegram",
            ),
            Note(
                user_id=user_id,
                content="Simulasi fisika graf interaktif di HTML5 Canvas: menggunakan gaya tolak Coulomb dan pegas Euler untuk menata simpul catatan ide secara organik.",
                tags=["vue", "graf", "arsitektur"],
                source="web",
            ),
            Note(
                user_id=user_id,
                content="Prinsip Zero Data Loss: jika model AI mengalami kendala jaringan atau timeout, transkripsi suara dan chat wajib disimpan apa adanya ke tabel notes.",
                tags=["arsitektur", "keamanan", "agent"],
                source="telegram",
            ),
            Note(
                user_id=user_id,
                content="Ide fitur Mode Jeda: integrasi kurasi playlist YouTube Music dan deep link ShopeeFood untuk kopi saat burnout.",
                tags=["recharge", "musik", "kopi"],
                source="telegram",
            ),
            Note(
                user_id=user_id,
                content="Catatan buku Deep Work oleh Cal Newport: batasi sesi fokus maksimal 90 menit per blok untuk mempertahankan kualitas kognitif prima.",
                tags=["produktivitas", "buku", "fokus"],
                source="web",
            ),
            Note(
                user_id=user_id,
                content="Strategi open-source launch: dokumentasi README yang ramah pemula, lisensi MIT, dan onboarding mandiri tanpa invite code manual.",
                tags=["opensource", "bisnis", "agent"],
                source="web",
            ),
            Note(
                user_id=user_id,
                content="Checklist optimasi Supabase: aktifkan Row Level Security (RLS) di semua tabel dan gunakan Session Pooler IPv4 untuk koneksi stabil.",
                tags=["backend", "keamanan", "database"],
                source="web",
            ),
            Note(
                user_id=user_id,
                content="Desain sistem Bedtime Guardian: pengingat lembut batas jam kerja malam agar ritme sirkadian tetap konsisten dan tidak begadang.",
                tags=["produktivitas", "recharge", "fokus"],
                source="telegram",
            ),
            Note(
                user_id=user_id,
                content="[Voice Note]: Ingatkan review metrik mingguan setiap Minggu malam jam 8 dan diskusikan rencana sprint berikutnya bersama tim.",
                tags=["suara", "prioritas", "produktivitas"],
                source="telegram",
            ),
        ]
        for n in notes_data:
            session.add(n)
        await session.commit()
        print(
            f"Berhasil membuat {len(notes_data)} Catatan dengan tags beririsan untuk Knowledge Graph."
        )

    print("\n[OK] DATA SEEDING SELESAI DENGAN SUKSES 100%!")


if __name__ == "__main__":
    asyncio.run(seed_data())
