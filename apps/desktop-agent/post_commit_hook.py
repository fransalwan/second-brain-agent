# apps/desktop-agent/post_commit_hook.py
"""Git post-commit hook untuk Second Brain Agent.

Secara otomatis mengirimkan data commit terbaru ke backend Second Brain:
- Menyelesaikan task yang ID atau kata kuncinya cocok dengan pesan commit
- Mencatat habit coding harian (streak)
- Berjalan senyap dan tidak mengganggu alur kerja git jika backend sedang offline.
"""

import json
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

# Cari config.json di folder yang sama
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


def get_git_info() -> tuple[str, str, str, str]:
    """Mengambil pesan commit terakhir, nama branch, nama repository, dan author email."""
    try:
        msg = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B"],
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        msg = ""

    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        branch = ""

    try:
        root_dir = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
        repo_name = Path(root_dir).name
    except Exception:
        repo_name = "unknown-repo"

    try:
        author_email = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%ae"],
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
        if not author_email:
            author_email = subprocess.check_output(
                ["git", "config", "user.email"],
                text=True,
                encoding="utf-8",
                stderr=subprocess.DEVNULL,
            ).strip()
    except Exception:
        author_email = ""

    return msg, branch, repo_name, author_email


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    commit_msg, branch, repo_name, git_email = get_git_info()
    if not commit_msg:
        sys.exit(0)

    # Baca config
    backend_url = "http://localhost:8000"
    api_key = "second-brain-ambient-key"
    email = git_email or "fransalwanpurba@mail.ugm.ac.id"
    notify_telegram = True

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                backend_url = cfg.get("backend_url", backend_url).rstrip("/")
                api_key = cfg.get("api_key", api_key)
                if not git_email:
                    email = cfg.get("user_email", email)
                notify_telegram = cfg.get("notify_telegram", True)
        except Exception:
            pass

    payload = {
        "email": email,
        "commit_message": commit_msg,
        "repo_name": repo_name,
        "branch": branch,
        "notify_telegram": notify_telegram,
    }

    url = f"{backend_url}/api/v1/ambient/git/commit"
    headers = {
        "Content-Type": "application/json",
        "X-Ambient-Key": api_key,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            completed_tasks = resp_data.get("completed_tasks", [])
            auto_habits = resp_data.get("auto_checked_habits", [])
            academic_sync = resp_data.get("academic_sync", {})

            print("=" * 60)
            print(f"[Second Brain] ⚡ Terhubung: {repo_name} ({branch})")

            # Academic Sync outputs
            if academic_sync.get("chapter_updated"):
                cu = academic_sync["chapter_updated"]
                print(f"[Second Brain] 📚 Bab {cu['chapter_num']}: {cu['title']} -> {cu['progress']}% ({cu['status']})")
            if academic_sync.get("supervision_logged"):
                print("[Second Brain] 👨‍🏫 Catatan bimbingan dospem berhasil dicatat ke riset!")
            if academic_sync.get("metric_recorded"):
                mr = academic_sync["metric_recorded"]
                print(f"[Second Brain] 🧪 Evaluasi Model: {mr['model_name']} ({mr['metrics_summary']})")
            if academic_sync.get("assignment_completed"):
                ac = academic_sync["assignment_completed"]
                print(f"[Second Brain] 🎓 Tugas Kuliah Selesai: {ac['title']} ({ac['course_name']})")

            if completed_tasks:
                print(f"[Second Brain] ✅ {len(completed_tasks)} tugas selesai:")
                for t in completed_tasks:
                    print(f"  - #{t['id']} {t['title']}")
            if auto_habits:
                for h in auto_habits:
                    print(f"[Second Brain] 🔥 Habit '{h['name']}' tercentang! (Streak: {h['streak']} hari)")
            print("=" * 60)
    except urllib.error.URLError:
        # Backend offline atau tidak terjangkau -> lewati tanpa error agar git commit tetap sukses
        pass
    except Exception:
        pass


if __name__ == "__main__":
    main()
