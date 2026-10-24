# apps/desktop-agent/install_git_hook.py
"""Installer 1-Klik Git Hook untuk Second Brain Agent.

Memasang hook post-commit di repository target (khususnya materi-kuliah,
thesis-manuscripts, dan thesis-experiments) agar setiap git commit
otomatis menyinkronkan tugas kuliah, progres skripsi (Bab 1-5),
metrik eksperimen AI, log bimbingan, dan habit harian ke Second Brain.

Penggunaan:
  python apps/desktop-agent/install_git_hook.py [path_repo_1] [path_repo_2] ...
  python apps/desktop-agent/install_git_hook.py --academic
  (Jika tanpa argumen, otomatis memasang ke repository saat ini dan mendeteksi repo akademik)
"""

import argparse
import os
from pathlib import Path
import stat
import sys

HOOK_SCRIPT = Path(__file__).resolve().parent / "post_commit_hook.py"

ACADEMIC_REPO_NAMES = [
    "materi-kuliah",
    "thesis-manuscripts",
    "thesis-experiments",
]


def install_hook(target_repo_path: Path) -> bool:
    git_dir = target_repo_path / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print(f"[SKIP] '{target_repo_path.name}' bukan repository Git (.git tidak ditemukan)")
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    post_commit_file = hooks_dir / "post-commit"
    hook_script_posix = HOOK_SCRIPT.as_posix()

    content = f"""#!/bin/sh
# Second Brain Academic & Ambient Git Hook
if command -v python3 >/dev/null 2>&1; then
    python3 "{hook_script_posix}"
elif command -v python >/dev/null 2>&1; then
    python "{hook_script_posix}"
elif command -v py >/dev/null 2>&1; then
    py -3 "{hook_script_posix}"
fi
"""

    with open(post_commit_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    try:
        current_mode = os.stat(post_commit_file).st_mode
        os.chmod(
            post_commit_file, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )
    except Exception:
        pass

    repo_name = target_repo_path.name.lower()
    role_desc = "Umum (Task & Coding Streak)"
    if "manuscript" in repo_name or "skripsi" in repo_name:
        role_desc = "Riset Naskah (Bab 1-5 Skripsi & Bimbingan Dospem)"
    elif "experiment" in repo_name or "eksperimen" in repo_name:
        role_desc = "Riset Eksperimen (Model Metrics & Hyperparameters)"
    elif "kuliah" in repo_name or "matkul" in repo_name:
        role_desc = "Kuliah & Akademik (Tugas Matkul & Belajar Habit)"

    print(f"  [OK] Dipasang di: {target_repo_path.name}")
    print(f"       Peran     : {role_desc}")
    print(f"       Hook Path : {post_commit_file}")
    return True


def scan_for_academic_repos(start_dirs: list[Path]) -> list[Path]:
    found = []
    seen = set()
    for base in start_dirs:
        if not base.exists():
            continue
        # Cek apakah base sendiri adalah repo akademik
        if base.name.lower() in ACADEMIC_REPO_NAMES and base not in seen:
            if (base / ".git").is_dir():
                found.append(base)
                seen.add(base)
        # Scan subfolder / direct children
        try:
            for child in base.iterdir():
                if child.is_dir() and child.name.lower() in ACADEMIC_REPO_NAMES and child not in seen:
                    if (child / ".git").is_dir():
                        found.append(child)
                        seen.add(child)
        except Exception:
            pass
    return found


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Second Brain Git Hook Installer")
    parser.add_argument("paths", nargs="*", help="Path direktori repository target")
    parser.add_argument(
        "--academic",
        action="store_true",
        help="Otomatis cari dan pasang hook ke repositori materi-kuliah, thesis-manuscripts, dan thesis-experiments",
    )
    args = parser.parse_args()

    print("=" * 65)
    print("🧠 Second Brain - Academic Git Hook Installer")
    print("=" * 65)

    targets: list[Path] = []
    if args.paths:
        for p in args.paths:
            targets.append(Path(p).resolve())
    else:
        # Default: repo saat ini
        root_repo = Path(__file__).resolve().parent.parent.parent
        targets.append(root_repo)

    if args.academic or not args.paths:
        # Cari repo-repo tetangga (sibling atau parent workspace)
        search_roots = [
            Path(__file__).resolve().parent.parent.parent.parent,  # on queue / portfolio-opensource
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Projects",
        ]
        academic_found = scan_for_academic_repos(search_roots)
        for ar in academic_found:
            if ar not in targets:
                targets.append(ar)

    installed_count = 0
    for target in targets:
        if install_hook(target):
            installed_count += 1

    print("-" * 65)
    print(f"✨ Selesai! {installed_count} repository berhasil dipasangi hook.")
    print("Setiap kali Anda menjalankan 'git commit' di repo di atas:")
    print("  • Materi Kuliah    -> Menyelesaikan tugas matkul & habit belajar")
    print("  • Thesis Naskah    -> Update progres Bab 1-5 & notulensi dospem")
    print("  • Thesis Experiment-> Simpan metrik model AI & benchmark Bab 4")
    print("=" * 65)


if __name__ == "__main__":
    main()
