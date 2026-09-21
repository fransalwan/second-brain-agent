# apps/desktop-agent/ambient_watcher.py
"""Second Brain Ambient OS Watcher.

Memantau aktivitas jendela VS Code di Windows secara otomatis:
- Memulai timer fokus saat membuka folder project tertentu
- Beralih project secara otomatis saat membuka repo lain di VS Code
- Menghentikan timer saat VS Code ditutup atau pengguna idle (> 10 menit)
- Sinkronisasi real-time ke backend Second Brain & database Supabase
- Zero external dependencies (hanya memakai modul bawaan Python & Win32 ctypes)
"""

import ctypes
from ctypes import wintypes
import json
import logging
import os
from pathlib import Path
import signal
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("AmbientWatcher")

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


# ==========================================
# WIN32 CTYPES HELPERS (ZERO EXTERNAL PIP)
# ==========================================
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def get_system_idle_seconds() -> float:
    """Mendapatkan durasi detik sejak aktivitas keyboard atau mouse terakhir di Windows."""
    try:
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            return max(0.0, millis / 1000.0)
    except Exception:
        pass
    return 0.0


def get_foreground_window_title() -> str:
    """Mendapatkan judul jendela yang sedang aktif di depan layar."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return ""
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return ""
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    except Exception:
        return ""


def get_all_open_vscode_window_titles() -> list[str]:
    """Mencari semua jendela VS Code yang sedang terbuka di layar."""
    titles = []
    try:
        user32 = ctypes.windll.user32

        def enum_proc(hwnd, _lparam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if "Visual Studio Code" in title:
                        titles.append(title)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
    except Exception:
        pass
    return titles


# ==========================================
# AMBIENT WATCHER CLIENT
# ==========================================
class AmbientWatcher:
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.config = self.load_config()
        self.current_project: str | None = None
        self.is_idle: bool = False
        self.away_start_time: float | None = None
        self.running = True

    def load_config(self) -> dict:
        if not self.config_file.exists():
            logger.error(f"File konfigurasi {self.config_file} tidak ditemukan!")
            sys.exit(1)
        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def send_api_request(self, endpoint: str, payload: dict) -> dict | None:
        """Kirim HTTP POST request ke backend Second Brain."""
        backend_url = self.config.get("backend_url", "http://localhost:8000").rstrip("/")
        url = f"{backend_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "X-Ambient-Key": self.config.get("api_key", ""),
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                resp_data = response.read().decode("utf-8")
                return json.loads(resp_data)
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                logger.error(f"API Error ({e.code}): {err_body}")
            except Exception:
                logger.error(f"API HTTPError: {e.code}")
        except Exception as e:
            logger.warning(f"Gagal menghubungi backend di {url}: {e}")
        return None

    def match_project_name(self, title: str) -> str | None:
        """Mencocokkan judul jendela VS Code dengan pemetaan project di config."""
        if "Visual Studio Code" not in title:
            return None

        mappings = self.config.get("project_mappings", {})
        title_lower = title.lower()

        for key, project_name in mappings.items():
            if key == "default":
                continue
            if key.lower() in title_lower:
                return project_name

        # Jika jendela adalah VS Code tapi folder tidak terdaftar khusus
        return mappings.get("default", None)

    def detect_active_vscode_project(self) -> str | None:
        """Deteksi project VS Code yang sedang dikerjakan.
        
        Prioritas 1: Foreground Window (sedang aktif diketik).
        Prioritas 2: Jika user sedang buka browser/terminal tapi VS Code tetap terbuka di latar,
                     pertahankan project yang sedang aktif agar timer tidak terputus-putus.
        """
        fg_title = get_foreground_window_title()
        fg_project = self.match_project_name(fg_title)

        if fg_project:
            return fg_project

        # Jika foreground bukan VS Code, cek apakah jendela VS Code masih ada yang terbuka
        open_vscode = get_all_open_vscode_window_titles()
        if not open_vscode:
            # VS Code benar-benar ditutup
            return None

        # Jika VS Code masih terbuka dan kita sedang melacak project, periksa apakah project tsb masih ada di daftar jendela
        if self.current_project:
            for title in open_vscode:
                if self.match_project_name(title) == self.current_project:
                    return self.current_project

        # Jika ada jendela VS Code terbuka lainnya
        for title in open_vscode:
            p = self.match_project_name(title)
            if p:
                return p

        return None

    def start_timer(self, project_name: str, context: str = ""):
        payload = {
            "email": self.config.get("user_email"),
            "project_name": project_name,
            "source": "vscode",
            "context": context,
            "notify_telegram": self.config.get("notify_telegram", True),
        }
        res = self.send_api_request("/api/v1/ambient/timer/start", payload)
        if res and res.get("status") in ("started", "already_running"):
            self.current_project = project_name
            self.is_idle = False
            logger.info(f"[TIMER START] Fokus dimulai: '{project_name}' (Status: {res.get('status')})")

    def stop_timer(self, reason: str = "window_closed"):
        if not self.current_project:
            return
        payload = {
            "email": self.config.get("user_email"),
            "project_name": self.current_project,
            "reason": reason,
            "notify_telegram": self.config.get("notify_telegram", True),
        }
        res = self.send_api_request("/api/v1/ambient/timer/stop", payload)
        if res:
            logger.info(
                f"[TIMER STOP] Fokus dihentikan: '{self.current_project}' "
                f"(Durasi: {res.get('duration_minutes', 0)} menit, Alasan: {reason})"
            )
        self.current_project = None

    def run(self):
        poll_interval = self.config.get("poll_interval_seconds", 3)
        idle_threshold = self.config.get("idle_threshold_seconds", 600)

        logger.info("=" * 60)
        logger.info("Second Brain Ambient Watcher aktif!")
        logger.info(f"Target User: {self.config.get('user_email')}")
        logger.info(f"Interval Pemantauan: {poll_interval}s | Batas Idle: {idle_threshold}s")
        logger.info("Tekan Ctrl+C untuk berhenti.")
        logger.info("=" * 60)

        while self.running:
            try:
                idle_sec = get_system_idle_seconds()

                # 1. Cek Apakah Pengguna Sedang Idle
                if idle_sec >= idle_threshold:
                    if self.current_project and not self.is_idle:
                        logger.info(f"[IDLE DETECTED] Pengguna tidak aktif selama {int(idle_sec)}s. Menghentikan timer.")
                        self.stop_timer(reason="idle_timeout")
                        self.is_idle = True
                    time.sleep(poll_interval)
                    continue
                else:
                    self.is_idle = False

                # 2. Deteksi Project VS Code
                detected_project = self.detect_active_vscode_project()

                if detected_project:
                    if self.current_project is None:
                        # Baru membuka VS Code
                        self.start_timer(detected_project)
                    elif self.current_project != detected_project:
                        # Beralih ke project lain di VS Code (Context Switching)
                        logger.info(f"[CONTEXT SWITCH] Beralih dari '{self.current_project}' ke '{detected_project}'")
                        self.start_timer(detected_project)
                else:
                    # VS Code ditutup
                    if self.current_project is not None:
                        logger.info("[VSCODE CLOSED] VS Code tidak terdeteksi terbuka. Menghentikan sesi fokus.")
                        self.stop_timer(reason="window_closed")

                time.sleep(poll_interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error di loop watcher: {e}")
                time.sleep(poll_interval)

        # Cleanup saat exit
        if self.current_project:
            logger.info("Menghentikan timer aktif sebelum keluar...")
            self.stop_timer(reason="watcher_shutdown")
        logger.info("Ambient Watcher dinonaktifkan.")


def main():
    watcher = AmbientWatcher(CONFIG_PATH)

    def handle_signal(_signum, _frame):
        watcher.running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    watcher.run()


if __name__ == "__main__":
    main()
