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


def get_git_info() -> tuple[str, str, str]:
    """Mengambil pesan commit terakhir, nama branch, dan nama repository."""
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

    return msg, branch, repo_name


def main():
    commit_msg, branch, repo_name = get_git_info()
    if not commit_msg:
        sys.exit(0)

    # Baca config
    backend_url = "http://localhost:8000"
    api_key = "second-brain-ambient-key"
    email = "fransalwan55@gmail.com"
    notify_telegram = True

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                backend_url = cfg.get("backend_url", backend_url).rstrip("/")
                api_key = cfg.get("api_key", api_key)
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
        with urllib.request.urlopen(req, timeout=3) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            completed_tasks = resp_data.get("completed_tasks", [])
            auto_habits = resp_data.get("auto_checked_habits", [])

            if completed_tasks:
                print(
                    f"[Second Brain] [DONE] {len(completed_tasks)} tugas otomatis diselesaikan via commit:"
                )
                for t in completed_tasks:
                    print(f"  - #{t['id']} {t['title']}")
            if auto_habits:
                for h in auto_habits:
                    print(
                        f"[Second Brain] [HABIT] '{h['name']}' dicentang! (Streak: {h['streak']} hari)"
                    )
    except urllib.error.URLError:
        # Backend offline atau tidak terjangkau -> lewati tanpa error agar git commit tetap sukses
        pass
    except Exception:
        pass


if __name__ == "__main__":
    main()
