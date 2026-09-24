# apps/desktop-agent/install_git_hook.py
"""Installer 1-Klik Git Hook untuk Second Brain Agent.

Memasang hook post-commit di repository target agar setiap git commit
otomatis menyelesaikan tugas dan menyinkronkan habit ke Second Brain.

Penggunaan:
  python apps/desktop-agent/install_git_hook.py [path_ke_repo]
  (Jika tanpa path, otomatis memasang ke repository saat ini)
"""

import os
from pathlib import Path
import stat
import sys

HOOK_SCRIPT = Path(__file__).resolve().parent / "post_commit_hook.py"


def install_hook(target_repo_path: Path):
    git_dir = target_repo_path / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print(
            f"[ERROR] '{target_repo_path}' bukan repository Git (.git tidak ditemukan)!"
        )
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    post_commit_file = hooks_dir / "post-commit"
    hook_script_posix = HOOK_SCRIPT.as_posix()

    content = f"""#!/bin/sh
# Second Brain Git Hook
python "{hook_script_posix}"
"""

    with open(post_commit_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    # Berikan izin execute (chmod +x)
    try:
        current_mode = os.stat(post_commit_file).st_mode
        os.chmod(
            post_commit_file, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )
    except Exception:
        pass

    print("=" * 60)
    print("[OK] Git Hook Second Brain Berhasil Dipasang!")
    print(f"Target Repo : {target_repo_path.resolve()}")
    print(f"Hook File   : {post_commit_file}")
    print("[INFO] Sekarang setiap 'git commit' di repo ini akan otomatis:")
    print("   1. Menyelesaikan tugas yang ID-nya disebut (misal: 'fix #3')")
    print("   2. Menyelesaikan tugas yang judulnya cocok dengan kata kunci commit")
    print("   3. Mencatat streak habit ngoding harianmu!")
    print("=" * 60)
    return True


def main():
    if len(sys.argv) > 1:
        target = Path(sys.argv[1]).resolve()
    else:
        # Default ke root repo saat ini
        target = Path(__file__).resolve().parent.parent.parent

    install_hook(target)


if __name__ == "__main__":
    main()
