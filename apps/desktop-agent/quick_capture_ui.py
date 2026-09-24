# apps/desktop-agent/quick_capture_ui.py
"""Global Quick Capture Desktop UI.

Mini input bar yang muncul di layar dengan hotkey global (Ctrl+Shift+Space).
Tangkap ide/tugas instan → kirim ke backend → Knowledge Graph.
"""

import json
import logging
import threading
import tkinter as tk
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger("QuickCapture")


class QuickCaptureUI:
    """Lightweight desktop quick capture UI dengan global hotkey."""

    def __init__(self, config: dict):
        self.config = config
        self.window: Optional[tk.Tk] = None
        self.input_field: Optional[tk.Entry] = None
        self.running = False
        self.hotkey_listener = None

    def send_capture_to_backend(self, text: str) -> dict | None:
        """Kirim tangkapan teks ke backend Quick Capture API."""
        backend_url = self.config.get("backend_url", "http://localhost:8000").rstrip("/")
        url = f"{backend_url}/api/v1/ambient/quick-capture"

        payload = {
            "email": self.config.get("user_email"),
            "text": text,
            "source": "global_hotkey",
            "notify_telegram": self.config.get("notify_telegram", True),
        }

        headers = {
            "Content-Type": "application/json",
            "X-Ambient-Key": self.config.get("api_key", ""),
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                resp_data = response.read().decode("utf-8")
                result = json.loads(resp_data)
                logger.info(f"✅ Quick Capture sent: '{text[:50]}...'")
                return result
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                logger.error(f"API Error ({e.code}): {err_body}")
            except Exception:
                logger.error(f"API HTTPError: {e.code}")
        except Exception as e:
            logger.warning(f"Gagal mengirim ke backend: {e}")
        return None

    def show_capture_window(self):
        """Tampilkan window input quick capture."""
        if self.window:
            self.window.lift()
            self.window.focus()
            return

        self.window = tk.Tk()
        self.window.title("💡 Quick Capture")
        self.window.geometry("500x80")
        self.window.attributes("-topmost", True)
        self.window.attributes("-toolwindow", True)

        # Frame utama
        frame = tk.Frame(self.window, bg="#2e2e2e", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Label
        label = tk.Label(
            frame,
            text="💡 Ide/Tugas:",
            fg="#00ff88",
            bg="#2e2e2e",
            font=("Courier", 11, "bold"),
        )
        label.pack(side=tk.LEFT, padx=(0, 10))

        # Input field
        self.input_field = tk.Entry(
            frame,
            font=("Courier", 11),
            fg="#ffffff",
            bg="#1a1a1a",
            insertbackground="#00ff88",
            relief=tk.FLAT,
            bd=2,
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input_field.focus()

        # Bind events
        self.input_field.bind("<Return>", self._on_submit)
        self.input_field.bind("<Escape>", self._on_cancel)
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Center window on screen
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 80) // 3
        self.window.geometry(f"500x80+{x}+{y}")

        try:
            self.window.mainloop()
        except Exception as e:
            logger.error(f"Error di UI loop: {e}")

    def _on_submit(self, event=None):
        """Handle submit (Enter key)."""
        if not self.input_field:
            return

        text = self.input_field.get().strip()
        if text:
            # Kirim ke backend di thread terpisah agar UI tidak freeze
            thread = threading.Thread(target=self.send_capture_to_backend, args=(text,))
            thread.daemon = True
            thread.start()

            # Close window immediately
            self._close_window()
        else:
            self._close_window()

    def _on_cancel(self, event=None):
        """Handle cancel (Escape key atau close button)."""
        self._close_window()

    def _close_window(self):
        """Tutup window dengan graceful."""
        if self.window:
            try:
                self.window.quit()
                self.window.destroy()
            except Exception:
                pass
            self.window = None
            self.input_field = None

    def start_hotkey_listener(self):
        """Mulai mendengarkan global hotkey Ctrl+Shift+Space."""
        try:
            from pynput import keyboard

            pressed_keys = set()

            def on_press(key):
                try:
                    if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        pressed_keys.add("ctrl")
                    elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                        pressed_keys.add("shift")
                    elif key == keyboard.Key.space:
                        pressed_keys.add("space")
                        # Deteksi: Ctrl+Shift+Space
                        if pressed_keys == {"ctrl", "shift", "space"}:
                            logger.info("🚀 Global hotkey triggered (Ctrl+Shift+Space)")
                            # Spawn window di thread terpisah (non-blocking)
                            t = threading.Thread(target=self.show_capture_window)
                            t.daemon = True
                            t.start()
                except Exception as e:
                    logger.debug(f"on_press error: {e}")

            def on_release(key):
                try:
                    if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        pressed_keys.discard("ctrl")
                    elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                        pressed_keys.discard("shift")
                    elif key == keyboard.Key.space:
                        pressed_keys.discard("space")
                except Exception:
                    pass

            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.start()
            self.hotkey_listener = listener
            logger.info("✅ Global hotkey listener aktif (Ctrl+Shift+Space)")
            return listener

        except ImportError:
            logger.error(
                "❌ pynput tidak terinstall. Jalankan: pip install pynput"
            )
            return None
        except Exception as e:
            logger.error(f"Gagal setup hotkey listener: {e}")
            return None


def main():
    """Test quick capture UI standalone."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config_path = Path(__file__).resolve().parent / "config.json"
    if not config_path.exists():
        logger.error(f"Config tidak ditemukan: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    ui = QuickCaptureUI(config)
    listener = ui.start_hotkey_listener()

    if listener:
        try:
            logger.info("Tekan Ctrl+Shift+Space untuk membuka Quick Capture. Ctrl+C untuk keluar.")
            # Keep the listener running
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Quick Capture UI shutdown.")
            if ui.hotkey_listener:
                ui.hotkey_listener.stop()


if __name__ == "__main__":
    main()
