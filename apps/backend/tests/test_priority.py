# apps/backend/tests/test_priority.py
from datetime import date, datetime, timezone
import sys
from pathlib import Path
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Area, Task
from app.priority import (
    SOON_WINDOW_DAYS,
    PriorityTier,
    get_top_tasks_for_brief,
    prioritize_tasks,
)


def test_overdue_area2_vs_today_area1():
    """Skenario wajib: 4 tugas overdue di Area 2, 1 tugas deadline hari ini di Area 1.
    Tugas Area 1 HARUS berada di posisi pertama karena posisi area memimpin di tingkat 'Sekarang'.
    """
    today = date(2026, 9, 25)  # Jumat
    u_id = uuid.uuid4()

    area1 = Area(id=1, user_id=u_id, name="Kuliah", position=1)
    area2 = Area(id=2, user_id=u_id, name="Usaha", position=2)
    areas = [area1, area2]

    tasks = [
        Task(
            id=101,
            user_id=u_id,
            area_id=2,
            title="Overdue Usaha 5 hari",
            deadline=date(2026, 9, 20),
            status="pending",
        ),
        Task(
            id=102,
            user_id=u_id,
            area_id=2,
            title="Overdue Usaha 4 hari",
            deadline=date(2026, 9, 21),
            status="pending",
        ),
        Task(
            id=103,
            user_id=u_id,
            area_id=2,
            title="Overdue Usaha 3 hari",
            deadline=date(2026, 9, 22),
            status="pending",
        ),
        Task(
            id=104,
            user_id=u_id,
            area_id=2,
            title="Overdue Usaha 1 hari",
            deadline=date(2026, 9, 24),
            status="pending",
        ),
        Task(
            id=201,
            user_id=u_id,
            area_id=1,
            title="Submit Tugas Kuliah Hari Ini",
            deadline=date(2026, 9, 25),
            status="pending",
        ),
    ]

    result = prioritize_tasks(tasks, areas, today)
    assert len(result) == 5

    # Tugas pertama WAJIB milik Area 1
    assert result[0].task.id == 201
    assert result[0].area.name == "Kuliah"
    assert result[0].tier == PriorityTier.NOW
    assert result[0].reason == "deadline hari ini"

    # 4 tugas berikutnya di Area 2 terurut dari keterlambatan terbanyak (5, 4, 3, 1 hari)
    assert [r.task.id for r in result[1:]] == [101, 102, 103, 104]
    assert result[1].reason == "lewat deadline 5 hari"
    assert result[2].reason == "lewat deadline 4 hari"
    assert result[3].reason == "lewat deadline 3 hari"
    assert result[4].reason == "lewat deadline 1 hari"
    print("Test 1 PASSED: Kasus 4 overdue Area 2 vs 1 today Area 1 terverifikasi.")


def test_all_tasks_without_deadline():
    """Skenario: semua tugas tanpa deadline.
    Tugas mendesak masuk tingkat 'Sekarang' (diurutkan posisi area).
    Tugas biasa masuk tingkat 'Lainnya' (diurutkan posisi area, lalu FIFO created_at).
    """
    today = date(2026, 9, 25)
    u_id = uuid.uuid4()

    area1 = Area(id=1, user_id=u_id, name="Kuliah", position=1)
    area2 = Area(id=2, user_id=u_id, name="Usaha", position=2)
    area3 = Area(id=3, user_id=u_id, name="Pribadi", position=3)
    areas = [area1, area2, area3]

    t_now = datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc)
    t_earlier = datetime(2026, 9, 25, 8, 0, tzinfo=timezone.utc)

    tasks = [
        Task(
            id=1,
            user_id=u_id,
            area_id=2,
            title="Bug Kritis Usaha",
            is_urgent=True,
            created_at=t_now,
        ),
        Task(
            id=2,
            user_id=u_id,
            area_id=1,
            title="Thesis Bab 2",
            is_urgent=False,
            created_at=t_now,
        ),
        Task(
            id=3,
            user_id=u_id,
            area_id=1,
            title="Baca Referensi",
            is_urgent=False,
            created_at=t_earlier,
        ),
        Task(
            id=4,
            user_id=u_id,
            area_id=3,
            title="Beli Susu",
            is_urgent=False,
            created_at=t_now,
        ),
        Task(
            id=5,
            user_id=u_id,
            area_id=1,
            title="Tugas Kuliah Mendesak",
            is_urgent=True,
            created_at=t_now,
        ),
    ]

    result = prioritize_tasks(tasks, areas, today)
    order_ids = [r.task.id for r in result]

    # Tingkat 'Sekarang': mendesak Area 1 (id 5), lalu mendesak Area 2 (id 1)
    assert order_ids[:2] == [5, 1]
    assert result[0].tier == PriorityTier.NOW
    assert result[0].reason == "ditandai mendesak"
    assert result[1].tier == PriorityTier.NOW
    assert result[1].reason == "ditandai mendesak"

    # Tingkat 'Lainnya': Area 1 (id 3 duluan karena created_at lebih awal, lalu id 2), lalu Area 3 (id 4)
    assert order_ids[2:] == [3, 2, 4]
    assert result[2].reason == "area prioritas utama (Kuliah)"
    assert result[3].reason == "area prioritas utama (Kuliah)"
    assert result[4].reason == "area Pribadi"
    print("Test 2 PASSED: Semua tugas tanpa deadline terurut sempurna.")


def test_multiple_overdue_same_area():
    """Skenario: beberapa tugas lewat deadline di area yang sama.
    Harus terurut dari keterlambatan terbanyak dulu.
    """
    today = date(2026, 9, 25)
    u_id = uuid.uuid4()
    area1 = Area(id=1, user_id=u_id, name="Kuliah", position=1)

    tasks = [
        Task(
            id=1, user_id=u_id, area_id=1, title="Tugas A", deadline=date(2026, 9, 24)
        ),  # lewat 1 hari
        Task(
            id=2, user_id=u_id, area_id=1, title="Tugas B", deadline=date(2026, 9, 22)
        ),  # lewat 3 hari
        Task(
            id=3, user_id=u_id, area_id=1, title="Tugas C", deadline=date(2026, 9, 20)
        ),  # lewat 5 hari
    ]

    result = prioritize_tasks(tasks, [area1], today)
    assert [r.task.id for r in result] == [3, 2, 1]
    assert result[0].reason == "lewat deadline 5 hari"
    assert result[1].reason == "lewat deadline 3 hari"
    assert result[2].reason == "lewat deadline 1 hari"
    print(
        "Test 3 PASSED: Beberapa tugas overdue di area yang sama terurut keterlambatan terbanyak."
    )


def test_friday_proximity_and_soon_window():
    """Skenario: Hari ini adalah Jumat (25 Sep 2026).
    Verifikasi kedekatan hari:
    - Jumat (hari ini): 'deadline hari ini'
    - Sabtu (besok): 'deadline besok (Sabtu)'
    - Minggu (lusa): 'deadline lusa (Minggu)'
    - Senin (+3 hari): 'deadline 3 hari lagi (Senin)'
    - Selasa (+4 hari, di luar SOON_WINDOW_DAYS): masuk 'Lainnya', 'deadline 4 hari lagi'
    """
    today = date(2026, 9, 25)  # Jumat
    u_id = uuid.uuid4()
    area1 = Area(id=1, user_id=u_id, name="Kuliah", position=1)

    tasks = [
        Task(id=1, user_id=u_id, area_id=1, title="Jumat", deadline=date(2026, 9, 25)),
        Task(id=2, user_id=u_id, area_id=1, title="Sabtu", deadline=date(2026, 9, 26)),
        Task(id=3, user_id=u_id, area_id=1, title="Minggu", deadline=date(2026, 9, 27)),
        Task(id=4, user_id=u_id, area_id=1, title="Senin", deadline=date(2026, 9, 28)),
        Task(id=5, user_id=u_id, area_id=1, title="Selasa", deadline=date(2026, 9, 29)),
    ]

    result = prioritize_tasks(tasks, [area1], today)
    assert [r.task.id for r in result] == [1, 2, 3, 4, 5]

    # Cek tingkatan
    assert result[0].tier == PriorityTier.NOW
    assert result[0].reason == "deadline hari ini"

    assert result[1].tier == PriorityTier.SOON
    assert result[1].reason == "deadline besok (Sabtu)"

    assert result[2].tier == PriorityTier.SOON
    assert result[2].reason == "deadline lusa (Minggu)"

    assert result[3].tier == PriorityTier.SOON
    assert result[3].reason == "deadline 3 hari lagi (Senin)"

    # Selasa (+4 hari) masuk tingkatan 'Lainnya'
    assert result[4].tier == PriorityTier.LATER
    assert result[4].reason == "deadline 4 hari lagi"
    print(
        "Test 4 PASSED: Konteks hari Jumat dan proksimitas deadline 3 hari terverifikasi."
    )


def test_tasks_without_area_last_in_tier():
    """Skenario: tugas tanpa area harus berada di posisi terakhir di tingkatannya masing-masing."""
    today = date(2026, 9, 25)
    u_id = uuid.uuid4()
    area1 = Area(id=1, user_id=u_id, name="Kuliah", position=1)

    tasks = [
        # Tingkat Sekarang:
        Task(
            id=1, user_id=u_id, area_id=None, title="Urgent Tanpa Area", is_urgent=True
        ),
        Task(id=2, user_id=u_id, area_id=1, title="Urgent Kuliah", is_urgent=True),
        # Tingkat Segera:
        Task(
            id=3,
            user_id=u_id,
            area_id=None,
            title="Besok Tanpa Area",
            deadline=date(2026, 9, 26),
        ),
        Task(
            id=4,
            user_id=u_id,
            area_id=1,
            title="Besok Kuliah",
            deadline=date(2026, 9, 26),
        ),
        # Tingkat Lainnya:
        Task(
            id=5, user_id=u_id, area_id=None, title="Santai Tanpa Area", deadline=None
        ),
        Task(id=6, user_id=u_id, area_id=1, title="Santai Kuliah", deadline=None),
    ]

    result = prioritize_tasks(tasks, [area1], today)
    order_ids = [r.task.id for r in result]

    # Sekarang: Kuliah (2) dulu baru Tanpa Area (1)
    assert order_ids[:2] == [2, 1]
    # Segera: Kuliah (4) dulu baru Tanpa Area (3)
    assert order_ids[2:4] == [4, 3]
    # Lainnya: Kuliah (6) dulu baru Tanpa Area (5)
    assert order_ids[4:] == [6, 5]

    assert result[1].area_name == "Tanpa Area"
    assert result[5].reason == "tanpa area"
    print("Test 5 PASSED: Tugas tanpa area selalu di posisi terakhir tingkatannya.")


def test_tie_breaker_created_at():
    """Skenario: kondisi identik diselesaikan dengan FIFO created_at."""
    today = date(2026, 9, 25)
    u_id = uuid.uuid4()
    area1 = Area(id=1, user_id=u_id, name="Kuliah", position=1)

    t1 = datetime(2026, 9, 25, 7, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 25, 9, 0, tzinfo=timezone.utc)

    tasks = [
        Task(
            id=10,
            user_id=u_id,
            area_id=1,
            title="Tugas Kedua",
            deadline=today,
            created_at=t2,
        ),
        Task(
            id=20,
            user_id=u_id,
            area_id=1,
            title="Tugas Pertama",
            deadline=today,
            created_at=t1,
        ),
    ]

    result = prioritize_tasks(tasks, [area1], today)
    assert [r.task.id for r in result] == [20, 10]
    print("Test 6 PASSED: Tie-breaker created_at (FIFO) terverifikasi.")


def test_brief_top_three_helper():
    """Skenario: get_top_tasks_for_brief mengembalikan maksimal 3 tugas dengan tugas pertama ditandai."""
    today = date(2026, 9, 25)
    u_id = uuid.uuid4()
    area1 = Area(id=1, user_id=u_id, name="Kuliah", position=1)

    tasks = [
        Task(id=i, user_id=u_id, area_id=1, title=f"Tugas {i}", deadline=today)
        for i in range(1, 6)
    ]

    result = prioritize_tasks(tasks, [area1], today)
    top_brief = get_top_tasks_for_brief(result, limit=3)

    assert len(top_brief) == 3
    # Elemen pertama ditandai True ('mulai dari sini')
    assert top_brief[0][1] is True
    assert top_brief[1][1] is False
    assert top_brief[2][1] is False
    print("Test 7 PASSED: Brief top 3 helper terverifikasi.")


if __name__ == "__main__":
    test_overdue_area2_vs_today_area1()
    test_all_tasks_without_deadline()
    test_multiple_overdue_same_area()
    test_friday_proximity_and_soon_window()
    test_tasks_without_area_last_in_tier()
    test_tie_breaker_created_at()
    test_brief_top_three_helper()
    print("\nALL PRIORITY UNIT TESTS PASSED SUCCESSFULLY!")
