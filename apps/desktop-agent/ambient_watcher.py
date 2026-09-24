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
from datetime import datetime, time as dt_time
import json
import logging
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
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

        WNDENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
        )
        user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
    except Exception:
        pass
    return titles


# ==========================================
# 🌙 BEDTIME GUARDIAN — TOAST NOTIFICATION
# ==========================================
def show_bedtime_toast(cutoff_str: str, current_str: str) -> bool:
    """Menampilkan Windows Native Toast Notification untuk pengingat jam tidur.

    Strategi:
    1. Primary: PowerShell [Windows.UI.Notifications] — native Windows 10/11
    2. Fallback: Win32 MessageBoxW via ctypes
    """
    title = "🌙 Bedtime Guardian"
    body = (
        f"Sudah pukul {current_str} (batas jam malam {cutoff_str}). "
        f"Waktunya istirahat dan simpan pekerjaanmu!"
    )

    # Primary: PowerShell Toast Notification (non-blocking)
    try:
        ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast duration="long">
    <visual>
        <binding template="ToastGeneric">
            <text>{title}</text>
            <text>{body}</text>
        </binding>
    </visual>
    <audio src="ms-winsoundevent:Notification.Reminder"/>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Second Brain Agent").Show($toast)
"""
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        logger.info(f"[BEDTIME TOAST] Notifikasi dikirim via PowerShell: {body}")
        return True
    except Exception as e:
        logger.warning(f"PowerShell toast gagal ({e}), mencoba fallback MessageBox...")

    # Fallback: Win32 MessageBox (blocking, tapi di thread terpisah)
    try:

        def _show_msgbox():
            MB_OK = 0x00000000
            MB_ICONINFORMATION = 0x00000040
            MB_TOPMOST = 0x00040000
            ctypes.windll.user32.MessageBoxW(
                0, body, title, MB_OK | MB_ICONINFORMATION | MB_TOPMOST
            )

        threading.Thread(target=_show_msgbox, daemon=True).start()
        logger.info(f"[BEDTIME TOAST] Notifikasi dikirim via MessageBox fallback")
        return True
    except Exception as e:
        logger.error(f"Semua metode notifikasi gagal: {e}")
        return False


def is_past_bedtime(
    current_time: dt_time, cutoff: dt_time, morning_end: dt_time = dt_time(4, 0)
) -> bool:
    """Mengecek apakah current_time berada di rentang batas jam malam hingga pagi.

    Logika sama dengan is_past_night_cutoff di backend, tapi standalone
    agar watcher tidak bergantung pada backend untuk pengecekan waktu.
    """
    if cutoff >= morning_end:
        # Cutoff normal (misal 22:30): larut malam = >= 22:30 ATAU < 04:00
        return current_time >= cutoff or current_time < morning_end
    else:
        # Cutoff di dini hari (misal 01:00): larut malam = >= 01:00 DAN < 04:00
        return cutoff <= current_time < morning_end


def parse_cutoff_time(cutoff_str: str) -> dt_time:
    """Parse string waktu HH:MM menjadi objek time."""
    try:
        parts = cutoff_str.strip().split(":")
        return dt_time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        logger.warning(
            f"Format bedtime_cutoff tidak valid: '{cutoff_str}', menggunakan default 23:00"
        )
        return dt_time(23, 0)


def extract_activity_context(title: str, project_name: str) -> str:
    """Ekstraksi detail aktivitas/file dari judul jendela VS Code secara cerdas."""
    if "Visual Studio Code" not in title:
        return ""

    # Bersihkan sufiks " - Visual Studio Code"
    clean_title = title.split(" - Visual Studio Code")[0].strip()
    parts = [p.strip().lstrip("● ") for p in clean_title.split(" - ") if p.strip()]

    file_name = ""
    if len(parts) > 1:
        file_name = parts[0]
    elif len(parts) == 1 and "." in parts[0]:
        file_name = parts[0]

    title_lower = title.lower()

    # 1. Deteksi Naskah Thesis
    if "thesis-manuscript" in title_lower or "penulisan" in project_name.lower():
        if any(
            file_name.lower().endswith(ext)
            for ext in [".md", ".tex", ".docx", ".txt", ".typ"]
        ):
            return (
                f"Perbaikan Penulisan & Draft ({file_name})"
                if file_name
                else "Perbaikan Penulisan & Draft Naskah"
            )
        elif file_name.lower().endswith(".bib"):
            return f"Manajemen Sitasi & Pustaka ({file_name})"
        elif any(
            file_name.lower().endswith(ext) for ext in [".png", ".jpg", ".svg", ".pdf"]
        ):
            return f"Penyusunan Grafik / Gambar ({file_name})"
        return (
            f"Pengerjaan Naskah ({file_name})"
            if file_name
            else "Pengerjaan Naskah Thesis"
        )

    # 2. Deteksi Eksperimen Thesis
    if "thesis-experiment" in title_lower or "eksperimen" in project_name.lower():
        if file_name.lower().endswith(".py"):
            return f"Pengembangan Model & Coding ({file_name})"
        elif file_name.lower().endswith(".ipynb"):
            return f"Eksplorasi Notebook & Analisis Data ({file_name})"
        elif any(file_name.lower().endswith(ext) for ext in [".yaml", ".yml", ".json"]):
            return f"Konfigurasi Parameter Eksperimen ({file_name})"
        return f"Eksperimen Thesis ({file_name})" if file_name else "Eksperimen Thesis"

    if file_name:
        return f"Menyunting {file_name}"
    return ""


# ==========================================
# AMBIENT WATCHER CLIENT
# ==========================================
class AmbientWatcher:
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.config = self.load_config()
        self.current_project: str | None = None
        self.current_context: str = ""
        self.is_idle: bool = False
        self.away_start_time: float | None = None
        self.running = True
        self.quick_capture_thread: threading.Thread | None = None
        self.quick_capture_enabled = self.config.get("enable_quick_capture", True)

        # 🌙 Bedtime Guardian state
        self.bedtime_enabled = self.config.get("enable_bedtime_toast", True)
        self.bedtime_cutoff = parse_cutoff_time(
            self.config.get("bedtime_cutoff", "22:30")
        )
        self.bedtime_reminder_interval = self.config.get(
            "bedtime_reminder_interval_minutes", 15
        )
        self.bedtime_notified: bool = False  # Guard: sudah kirim toast hari ini?
        self.bedtime_last_reminder: float = 0.0  # Timestamp reminder terakhir

    def load_config(self) -> dict:
        if not self.config_file.exists():
            logger.error(f"File konfigurasi {self.config_file} tidak ditemukan!")
            sys.exit(1)
        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def send_api_request(self, endpoint: str, payload: dict) -> dict | None:
        """Kirim HTTP POST request ke backend Second Brain."""
        backend_url = self.config.get("backend_url", "http://localhost:8000").rstrip(
            "/"
        )
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

    def start_quick_capture_listener(self):
        """Start quick capture hotkey listener di background thread."""
        if not self.quick_capture_enabled:
            return

        try:
            from quick_capture_ui import QuickCaptureUI

            ui = QuickCaptureUI(self.config)
            listener = ui.start_hotkey_listener()

            if listener:
                logger.info("✅ Global Quick Capture aktif (Ctrl+Shift+Space)")
            else:
                logger.warning("⚠️ Quick Capture hotkey listener gagal distart")
        except ImportError:
            logger.warning("Quick Capture module tidak ditemukan, skip initialization")
        except Exception as e:
            logger.error(f"Error starting Quick Capture: {e}")

    def detect_active_vscode_project(self) -> tuple[str | None, str]:
        """Deteksi project VS Code dan sub-aktivitas file yang sedang dikerjakan.

        Prioritas 1: Foreground Window (sedang aktif diketik).
        Prioritas 2: Jika user sedang buka browser/terminal tapi VS Code tetap terbuka di latar,
                     pertahankan project yang sedang aktif agar timer tidak terputus-putus.
        """
        fg_title = get_foreground_window_title()
        fg_project = self.match_project_name(fg_title)

        if fg_project:
            context = extract_activity_context(fg_title, fg_project)
            return fg_project, context

        # Jika foreground bukan VS Code, cek apakah jendela VS Code masih ada yang terbuka
        open_vscode = get_all_open_vscode_window_titles()
        if not open_vscode:
            # VS Code benar-benar ditutup
            return None, ""

        # Jika VS Code masih terbuka dan kita sedang melacak project, periksa apakah project tsb masih ada di daftar jendela
        if self.current_project:
            for title in open_vscode:
                if self.match_project_name(title) == self.current_project:
                    context = extract_activity_context(title, self.current_project)
                    return self.current_project, context

        # Jika ada jendela VS Code terbuka lainnya
        for title in open_vscode:
            p = self.match_project_name(title)
            if p:
                context = extract_activity_context(title, p)
                return p, context

        return None, ""

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
            self.current_context = context
            self.is_idle = False
            ctx_msg = f" | Aktivitas: {context}" if context else ""
            logger.info(
                f"[TIMER START] Fokus dimulai: '{project_name}' (Status: {res.get('status')}){ctx_msg}"
            )

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
            auto_habits = res.get("auto_checked_habits", [])
            for ah in auto_habits:
                logger.info(
                    f"[HABIT COMPLETED] Habit '{ah.get('name')}' otomatis dicentang! (Streak: {ah.get('streak')} hari)"
                )
        self.current_project = None

    def check_bedtime_and_notify(self):
        """🌙 Bedtime Guardian: cek waktu malam dan tampilkan toast notification.

        Logika:
        - Jika waktu lokal >= bedtime_cutoff DAN ada project aktif → kirim toast
        - Toast pertama langsung dikirim saat crossing cutoff
        - Toast reminder dikirim setiap bedtime_reminder_interval menit
        - Reset flag saat hari berganti (setelah pukul 04:00 pagi)
        """
        if not self.bedtime_enabled:
            return

        now = datetime.now()
        current_t = now.time()

        # Reset flag bedtime saat pagi (setelah 04:00) agar besok malam bisa kirim lagi
        if dt_time(4, 0) <= current_t < dt_time(5, 0) and self.bedtime_notified:
            self.bedtime_notified = False
            self.bedtime_last_reminder = 0.0
            logger.info("[BEDTIME] Flag direset untuk hari baru.")
            return

        # Cek apakah sudah melewati batas jam malam
        if not is_past_bedtime(current_t, self.bedtime_cutoff):
            return

        # Sudah lewat cutoff — cek apakah perlu kirim toast
        now_ts = time.time()
        cutoff_str = self.bedtime_cutoff.strftime("%H:%M")
        current_str = now.strftime("%H:%M")

        if not self.bedtime_notified:
            # Toast pertama kali melewati cutoff
            show_bedtime_toast(cutoff_str, current_str)
            self.bedtime_notified = True
            self.bedtime_last_reminder = now_ts
            logger.info(
                f"[BEDTIME] ⚠️ Peringatan pertama dikirim: {current_str} (cutoff: {cutoff_str})"
            )
        else:
            # Reminder berkala setiap N menit
            elapsed_since_last = (now_ts - self.bedtime_last_reminder) / 60.0
            if elapsed_since_last >= self.bedtime_reminder_interval:
                show_bedtime_toast(cutoff_str, current_str)
                self.bedtime_last_reminder = now_ts
                logger.info(
                    f"[BEDTIME] 🔁 Reminder dikirim ulang: {current_str} "
                    f"(interval: {self.bedtime_reminder_interval} menit)"
                )

    def run(self):
        poll_interval = self.config.get("poll_interval_seconds", 3)
        idle_threshold = self.config.get("idle_threshold_seconds", 600)

        logger.info("=" * 60)
        logger.info("Second Brain Ambient Watcher aktif!")
        logger.info(f"Target User: {self.config.get('user_email')}")
        logger.info(
            f"Interval Pemantauan: {poll_interval}s | Batas Idle: {idle_threshold}s"
        )
        if self.bedtime_enabled:
            logger.info(
                f"🌙 Bedtime Guardian: aktif (cutoff: {self.bedtime_cutoff.strftime('%H:%M')}, "
                f"reminder: setiap {self.bedtime_reminder_interval} menit)"
            )
        logger.info("Tekan Ctrl+C untuk berhenti.")
        logger.info("=" * 60)

        # Start Global Quick Capture listener
        self.start_quick_capture_listener()

        while self.running:
            try:
                idle_sec = get_system_idle_seconds()

                # 1. Cek Apakah Pengguna Sedang Idle
                if idle_sec >= idle_threshold:
                    if self.current_project and not self.is_idle:
                        logger.info(
                            f"[IDLE DETECTED] Pengguna tidak aktif selama {int(idle_sec)}s. Menghentikan timer."
                        )
                        self.stop_timer(reason="idle_timeout")
                        self.is_idle = True
                    time.sleep(poll_interval)
                    continue
                else:
                    self.is_idle = False

                # 2. Deteksi Project VS Code
                detected_project, detected_context = self.detect_active_vscode_project()

                if detected_project:
                    if self.current_project is None:
                        # Baru membuka VS Code
                        self.start_timer(detected_project, context=detected_context)
                    elif self.current_project != detected_project:
                        # Beralih ke project lain di VS Code (Context Switching)
                        logger.info(
                            f"[CONTEXT SWITCH] Beralih dari '{self.current_project}' ke '{detected_project}'"
                        )
                        self.start_timer(detected_project, context=detected_context)
                    elif detected_context and detected_context != self.current_context:
                        # Tetap di project yang sama tapi berganti file/sub-aktivitas
                        self.current_context = detected_context
                        logger.info(
                            f"[{detected_project}] 📌 Aktivitas: {detected_context}"
                        )
                else:
                    # VS Code ditutup
                    if self.current_project is not None:
                        logger.info(
                            "[VSCODE CLOSED] VS Code tidak terdeteksi terbuka. Menghentikan sesi fokus."
                        )
                        self.stop_timer(reason="window_closed")

                # 3. 🌙 Bedtime Guardian: cek jam malam saat user masih aktif ngoding
                if self.current_project:
                    self.check_bedtime_and_notify()

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
