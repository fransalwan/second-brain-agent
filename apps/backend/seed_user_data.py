# apps/backend/seed_user_data.py
"""Script seeding data komprehensif untuk pengguna fransalwan55@gmail.com.

Mengisi data realistis di SELURUH modul dan fitur:
1. Profile: Konfigurasi brief time & bedtime cutoff
2. Areas: 4 Area hidup terurut (1. Kesehatan, 2. Kuliah dan Riset, 3. Karir, 4. Usaha)
3. Tasks: Tugas pending berbagai tier (Urgent, Hari Ini, Besok, Sisa Hari) & Tugas Completed
4. Habits & HabitLogs: Habit aktif dengan streak berjalan (termasuk habit terkait kesehatan)
5. TimeLogs: Sesi fokus kerja harian & mingguan untuk visualisasi grafik & laporan /weekly
6. Notes: Catatan ide & bank literatur paper (#paper, #literatur) yang saling terhubung untuk Knowledge Graph
7. ThesisChapters: Status progres naskah Bab 1 s/d Bab 5 untuk /thesis
8. SupervisionLogs: Riwayat bimbingan dospem & tracking anti-ghosting untuk /bimbingan
9. ExperimentMetrics: Log metrik benchmark eksperimen model AI untuk /metric
10. SleepLogs: Riwayat tidur 7 hari terakhir untuk /tidur & korelasi produktivitas
11. HydrationLogs: Catatan asupan air minum hari ini (5/8 gelas) untuk /minum
12. HealthCheckLogs: Status check-in vitamin & peregangan untuk /kesehatan
"""

import asyncio
import sys
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlmodel import col, delete, select

from app.config import settings
from app.database import SessionLocal
from app.models import (
    Area,
    ExperimentMetric,
    Habit,
    HabitLog,
    HealthCheckLog,
    HydrationLog,
    Note,
    Profile,
    SleepLog,
    SupervisionLog,
    Task,
    ThesisChapter,
    TimeLog,
    utcnow,
)

TARGET_EMAIL = "fransalwan55@gmail.com"
LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)


async def seed_data():
    today = datetime.now(LOCAL_TZ).date()

    async with SessionLocal() as session:
        # ==========================================
        # 1. CARI PROFIL PENGGUNA
        # ==========================================
        prof_res = await session.execute(
            select(Profile).where(Profile.email == TARGET_EMAIL)
        )
        profile = prof_res.scalars().first()

        if not profile:
            print(f"Error: Profil dengan email {TARGET_EMAIL} tidak ditemukan!")
            return

        user_id = profile.id
        print(f"Mempersiapkan data seed untuk: {profile.full_name} ({TARGET_EMAIL}) [ID: {user_id}]")

        # Konfigurasi profil optimal
        profile.brief_time = time(7, 0)
        profile.night_cutoff_time = time(22, 30)
        session.add(profile)
        await session.commit()

        # ==========================================
        # 2. BERSIHKAN DATA LAMA
        # ==========================================
        await session.execute(delete(SleepLog).where(SleepLog.user_id == user_id))
        await session.execute(delete(HydrationLog).where(HydrationLog.user_id == user_id))
        await session.execute(delete(HealthCheckLog).where(HealthCheckLog.user_id == user_id))
        await session.execute(delete(ThesisChapter).where(ThesisChapter.user_id == user_id))
        await session.execute(delete(SupervisionLog).where(SupervisionLog.user_id == user_id))
        await session.execute(delete(ExperimentMetric).where(ExperimentMetric.user_id == user_id))
        await session.execute(delete(HabitLog).where(HabitLog.user_id == user_id))
        await session.execute(delete(Habit).where(Habit.user_id == user_id))
        await session.execute(delete(Task).where(Task.user_id == user_id))
        await session.execute(delete(Area).where(Area.user_id == user_id))
        await session.execute(delete(TimeLog).where(TimeLog.user_id == user_id))
        await session.execute(delete(Note).where(Note.user_id == user_id))
        await session.commit()
        print("Data lama berhasil dibersihkan untuk inisialisasi menyeluruh.")

        # ==========================================
        # 3. AREA HIDUP (4 Area Sesuai Prioritas Utama)
        # ==========================================
        areas_data = [
            Area(user_id=user_id, name="Kesehatan", position=1),
            Area(user_id=user_id, name="Kuliah dan Riset", position=2),
            Area(user_id=user_id, name="Karir", position=3),
            Area(user_id=user_id, name="Usaha", position=4),
        ]
        for a in areas_data:
            session.add(a)
        await session.commit()

        areas_res = await session.execute(
            select(Area).where(Area.user_id == user_id).order_by(Area.position.asc())
        )
        areas = {a.name: a.id for a in areas_res.scalars().all()}
        print(f"Berhasil membuat {len(areas)} Area Hidup (Kesehatan, Kuliah dan Riset, Karir, Usaha).")

        # Helper datetime UTC
        def local_dt(d: date, hour: int, minute: int) -> datetime:
            return (
                datetime.combine(d, time(hour, minute))
                .replace(tzinfo=LOCAL_TZ)
                .astimezone(timezone.utc)
            )

        # ==========================================
        # 4. TUGAS (TASKS: Tier 1, 2, 3 & Completed)
        # ==========================================
        tasks_data = [
            # --- AREA 1: KESEHATAN (Prioritas #1) ---
            Task(
                user_id=user_id,
                area_id=areas["Kesehatan"],
                title="Medical checkup & periksa kesehatan gigi tahunan",
                is_urgent=True,
                deadline=today + timedelta(days=2),
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Kesehatan"],
                title="Restock multivitamin, Omega-3, & suplemen Vitamin D3",
                is_urgent=False,
                deadline=today + timedelta(days=4),
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Kesehatan"],
                title="Beli ergonomic wrist rest untuk keyboard & mouse",
                is_urgent=False,
                deadline=None,
                status="completed",
                completed_at=local_dt(today - timedelta(days=1), 16, 0),
            ),

            # --- AREA 2: KULIAH DAN RISET (Hit /matkul countdown!) ---
            Task(
                user_id=user_id,
                area_id=areas["Kuliah dan Riset"],
                title="Submit revisi proposal naskah Bab 3 ke Dospem",
                is_urgent=True,
                deadline=today,  # Countdown: HARI INI!
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Kuliah dan Riset"],
                title="Presentasi seminar mingguan progres model attention",
                is_urgent=False,
                deadline=today + timedelta(days=1),  # Countdown: BESOK!
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Kuliah dan Riset"],
                title="Kompilasi tabel metrik evaluasi eksperimen Bab 4",
                is_urgent=False,
                deadline=today + timedelta(days=3),  # Countdown: Sisa 3 hari
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Kuliah dan Riset"],
                title="Review 3 paper transformer arsitektur terbaru",
                is_urgent=False,
                deadline=today + timedelta(days=5),  # Countdown: Sisa 5 hari
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Kuliah dan Riset"],
                title="Finalisasi batasan masalah & rumusan Bab 1",
                is_urgent=False,
                deadline=None,
                status="completed",
                completed_at=local_dt(today - timedelta(days=2), 15, 0),
            ),

            # --- AREA 3: KARIR ---
            Task(
                user_id=user_id,
                area_id=areas["Karir"],
                title="Rilis v1.1 Second Brain Agent & update showcase README",
                is_urgent=False,
                deadline=today + timedelta(days=3),
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Karir"],
                title="Tulis artikel teknis: Autonomous AI Agent Architecture di Medium",
                is_urgent=False,
                deadline=today + timedelta(days=6),
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Karir"],
                title="Setup automated testing pipeline di GitHub Actions",
                is_urgent=False,
                deadline=None,
                status="completed",
                completed_at=local_dt(today - timedelta(days=3), 17, 30),
            ),

            # --- AREA 4: USAHA ---
            Task(
                user_id=user_id,
                area_id=areas["Usaha"],
                title="Kirim revisi invoice & konfirmasi pembayaran CV PELANGI EFRATA",
                is_urgent=True,
                deadline=today,
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Usaha"],
                title="Follow up penawaran proyek dashboard analitik klien baru",
                is_urgent=False,
                deadline=today + timedelta(days=2),
                status="pending",
            ),
            Task(
                user_id=user_id,
                area_id=areas["Usaha"],
                title="Rekonsiliasi cashflow dan pencatatan buku kas operasional",
                is_urgent=False,
                deadline=None,
                status="completed",
                completed_at=local_dt(today - timedelta(days=1), 18, 0),
            ),
        ]
        for t in tasks_data:
            session.add(t)
        await session.commit()
        print(f"Berhasil membuat {len(tasks_data)} Tugas (Tasks) di 4 Area Hidup.")

        # ==========================================
        # 5. HABITS & HABIT LOGS (Streaks)
        # ==========================================
        habits_info = [
            ("Minum 2L Air Putih", 6),
            ("Peregangan 5 Menit", 4),
            ("Minum Vitamin Harian", 5),
            ("Deep Work Riset 90 Menit", 7),
            ("Tidur Sebelum 22:30", 4),
            ("Jalan Pagi 15 Menit", 3),
        ]
        created_habits = []
        for h_name, streak in habits_info:
            h = Habit(user_id=user_id, name=h_name, is_active=True)
            session.add(h)
            created_habits.append((h, streak))
        await session.commit()

        # Buat habit logs untuk membentuk streak
        total_habit_logs = 0
        for h, streak in created_habits:
            await session.refresh(h)
            for day_offset in range(streak):
                d = today - timedelta(days=day_offset)
                hl = HabitLog(
                    habit_id=h.id,
                    user_id=user_id,
                    completed_date=d,
                    created_at=datetime.combine(d, time(8, 0)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc),
                )
                session.add(hl)
                total_habit_logs += 1
        await session.commit()
        print(f"Berhasil membuat {len(created_habits)} Habit aktif dengan {total_habit_logs} Habit Logs (Streak aktif).")

        # ==========================================
        # 6. TIME LOGS (SESI FOKUS DEEP WORK)
        time_logs_data = [
            # Hari Ini
            TimeLog(
                user_id=user_id,
                project_name="Thesis Bab 3",
                started_at=local_dt(today, 9, 30),
                ended_at=local_dt(today, 11, 30),
                duration_minutes=120,
                break_reminder_sent=True,
            ),
            TimeLog(
                user_id=user_id,
                project_name="Second Brain Agent",
                started_at=local_dt(today, 13, 30),
                ended_at=local_dt(today, 15, 0),
                duration_minutes=90,
                break_reminder_sent=True,
            ),
            # 1 hari lalu
            TimeLog(
                user_id=user_id,
                project_name="Eksperimen Model AI",
                started_at=local_dt(today - timedelta(days=1), 10, 0),
                ended_at=local_dt(today - timedelta(days=1), 12, 0),
                duration_minutes=120,
                break_reminder_sent=True,
            ),
            TimeLog(
                user_id=user_id,
                project_name="CV PELANGI EFRATA",
                started_at=local_dt(today - timedelta(days=1), 14, 0),
                ended_at=local_dt(today - timedelta(days=1), 15, 30),
                duration_minutes=90,
                break_reminder_sent=True,
            ),
            # 2 hari lalu
            TimeLog(
                user_id=user_id,
                project_name="Thesis Bab 2",
                started_at=local_dt(today - timedelta(days=2), 9, 0),
                ended_at=local_dt(today - timedelta(days=2), 11, 0),
                duration_minutes=120,
                break_reminder_sent=True,
            ),
            # 3 hari lalu
            TimeLog(
                user_id=user_id,
                project_name="Second Brain Agent",
                started_at=local_dt(today - timedelta(days=3), 14, 0),
                ended_at=local_dt(today - timedelta(days=3), 16, 0),
                duration_minutes=120,
                break_reminder_sent=True,
            ),
            # 4 hari lalu
            TimeLog(
                user_id=user_id,
                project_name="Riset Literatur Paper",
                started_at=local_dt(today - timedelta(days=4), 10, 0),
                ended_at=local_dt(today - timedelta(days=4), 11, 30),
                duration_minutes=90,
                break_reminder_sent=False,
            ),
        ]
        for tl in time_logs_data:
            session.add(tl)
        await session.commit()
        print(f"Berhasil membuat {len(time_logs_data)} Sesi Fokus (Time Logs) harian & pekanan.")

        # ==========================================
        # 7. CATATAN & BANK LITERATUR (KNOWLEDGE GRAPH & /paper)
        # ==========================================
        notes_data = [
            # Bank Literatur Paper
            Note(
                user_id=user_id,
                content="Vaswani et al. (2017) 'Attention Is All You Need': Arsitektur transformer murni berbasis self-attention mekanisme tanpa ketergantungan urutan recurrency, memungkinkan komputasi paralel masif pada GPU.",
                tags=["paper", "literatur", "ai", "thesis"],
                source="paper",
            ),
            Note(
                user_id=user_id,
                content="Devlin et al. (2018) 'BERT': Pre-training deep bidirectional representations from unlabeled text untuk transfer learning NLP dan representasi semantik tinggi.",
                tags=["paper", "literatur", "ai", "nlp"],
                source="paper",
            ),
            Note(
                user_id=user_id,
                content="Chung et al. (2014) 'Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling': Analisis perbandingan komputasi dan retensi memori antara LSTM dan GRU.",
                tags=["paper", "literatur", "nlp", "arsitektur"],
                source="paper",
            ),
            # Catatan Ide & Arsitektur Sistem
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
                content="Desain sistem Bedtime Guardian: pengingat lembut batas jam kerja malam agar ritme sirkadian tetap konsisten dan tidak begadang.",
                tags=["produktivitas", "recharge", "fokus"],
                source="telegram",
            ),
        ]
        for n in notes_data:
            session.add(n)
        await session.commit()
        print(f"Berhasil membuat {len(notes_data)} Catatan (termasuk Bank Literatur Paper & Knowledge Graph).")

        # ==========================================
        # 8. THESIS CHAPTERS (/thesis)
        # ==========================================
        chapters_data = [
            ThesisChapter(user_id=user_id, chapter_num=1, title="Pendahuluan", status="Selesai", progress=100),
            ThesisChapter(user_id=user_id, chapter_num=2, title="Landasan Teori", status="Review Dospem", progress=85),
            ThesisChapter(user_id=user_id, chapter_num=3, title="Metodologi Penelitian", status="Drafting", progress=50),
            ThesisChapter(user_id=user_id, chapter_num=4, title="Hasil & Pembahasan", status="Drafting", progress=20),
            ThesisChapter(user_id=user_id, chapter_num=5, title="Kesimpulan & Saran", status="Belum Mulai", progress=0),
        ]
        for ch in chapters_data:
            session.add(ch)
        await session.commit()
        print(f"Berhasil membuat {len(chapters_data)} Bab Thesis (Progres gabungan ~51%).")

        # ==========================================
        # 9. SUPERVISION LOGS (/bimbingan)
        # ==========================================
        supervision_data = [
            SupervisionLog(
                user_id=user_id,
                notes="Dospem menyetujui arsitektur Bab 3, minta perjelas batasan masalah & perbandingan F1 score",
                action_items="Tambahkan tabel komparasi parameter baseline di Bab 4",
                created_at=datetime.combine(today - timedelta(days=4), time(14, 30)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc),
            ),
            SupervisionLog(
                user_id=user_id,
                notes="Review outline Bab 2 & sitasi jurnal terbaru (Transformer-based NLP)",
                action_items="Perbanyak sitasi jurnal internasional Q1/Q2 5 tahun terakhir",
                created_at=datetime.combine(today - timedelta(days=12), time(10, 15)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc),
            ),
            SupervisionLog(
                user_id=user_id,
                notes="Pengajuan judul dan latar belakang penelitian disetujui",
                action_items="Susun draft Bab 1 dan instrumen pengumpulan dataset",
                created_at=datetime.combine(today - timedelta(days=25), time(11, 0)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc),
            ),
        ]
        for s in supervision_data:
            session.add(s)
        await session.commit()
        print(f"Berhasil membuat {len(supervision_data)} Riwayat Bimbingan Dospem.")

        # ==========================================
        # 10. EXPERIMENT METRICS (/metric)
        # ==========================================
        metrics_data = [
            ExperimentMetric(
                user_id=user_id,
                model_name="Transformer-Encoder",
                metrics_summary="Akurasi: 94.8%, F1: 94.2%, Loss: 0.089",
                parameters="Epoch: 40, LR: 0.0005, Heads: 8, Warmup: 1000",
                created_at=datetime.combine(today - timedelta(days=1), time(16, 20)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc),
            ),
            ExperimentMetric(
                user_id=user_id,
                model_name="BiLSTM-Attention",
                metrics_summary="Akurasi: 92.4%, F1: 91.8%, Loss: 0.142",
                parameters="Epoch: 50, LR: 0.001, Hidden: 256, Dropout: 0.3",
                created_at=datetime.combine(today - timedelta(days=2), time(11, 45)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc),
            ),
            ExperimentMetric(
                user_id=user_id,
                model_name="Baseline-SVM",
                metrics_summary="Akurasi: 84.1%, F1: 82.7%",
                parameters="Kernel: RBF, C: 1.0, Gamma: scale",
                created_at=datetime.combine(today - timedelta(days=4), time(15, 10)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc),
            ),
        ]
        for em in metrics_data:
            session.add(em)
        await session.commit()
        print(f"Berhasil membuat {len(metrics_data)} Log Metrik Eksperimen Model AI.")

        # ==========================================
        # 11. SLEEP LOGS (/tidur - 7 HARI TERAKHIR)
        # ==========================================
        sleep_history = [
            (today, 7.0, "Cukup"),
            (today - timedelta(days=1), 7.5, "Nyenyak"),
            (today - timedelta(days=2), 6.5, "Cukup"),
            (today - timedelta(days=3), 5.5, "Kurang"),
            (today - timedelta(days=4), 7.0, "Cukup"),
            (today - timedelta(days=5), 8.0, "Nyenyak"),
            (today - timedelta(days=6), 6.0, "Cukup"),
        ]
        for s_date, hours, qual in sleep_history:
            sl = SleepLog(
                user_id=user_id,
                date=s_date,
                hours=hours,
                quality=qual,
                created_at=datetime.combine(s_date, time(7, 30)).replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc),
            )
            session.add(sl)
        await session.commit()
        print(f"Berhasil membuat {len(sleep_history)} Log Tidur 7 hari terakhir (Rata-rata 6.8 jam).")

        # ==========================================
        # 12. HYDRATION & HEALTH CHECK (/minum, /vitamin, /kesehatan)
        # ==========================================
        hydration = HydrationLog(
            user_id=user_id,
            date=today,
            glasses=5,
            target_glasses=8,
            updated_at=utcnow(),
        )
        session.add(hydration)

        health_check = HealthCheckLog(
            user_id=user_id,
            date=today,
            took_vitamin=True,
            did_stretch=True,
            burnout_score=20,
            notes="Kondisi fisik prima, fokus terjaga",
            created_at=utcnow(),
        )
        session.add(health_check)
        await session.commit()
        print("Berhasil membuat Log Hidrasi (5/8 gelas) dan Health Check (Vitamin & Peregangan Selesai).")

    print("\n=======================================================")
    print("🎉 MASTER SEED BERHASIL DIEKSEKUSI 100%!")
    print("Seluruh modul kini terisi data nyata & siap diuji:")
    print("• /thesis     -> Bab 1-5 dengan progres naskah 51%")
    print("• /bimbingan  -> 3 riwayat catatan dospem & counter 4 hari")
    print("• /metric     -> 3 benchmark model (Transformer, BiLSTM, SVM)")
    print("• /paper      -> 3 intisari jurnal/paper terindeks")
    print("• /matkul     -> 4 tugas kuliah dengan countdown (HARI INI, BESOK, H-3)")
    print("• /tidur      -> Riwayat tidur 7 hari (rata-rata 6.8 jam)")
    print("• /minum      -> 5/8 gelas (1250 / 2000 ml)")
    print("• /kesehatan  -> Skor Burnout 20/100 (Rendah 🟢 Kondisi Prima)")
    print("• /weekly     -> Waktu fokus ~10+ jam dan habit streaks aktif")
    print("=======================================================")


if __name__ == "__main__":
    asyncio.run(seed_data())
