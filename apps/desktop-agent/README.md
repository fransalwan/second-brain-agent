# 🖥️ Second Brain Desktop Agent

Daemon otomatis untuk pelacakan ambient, timer fokus, dan quick capture ide/tugas dari desktop.

## ✨ Fitur

### 1. **🎯 Ambient Watcher (VS Code Focus Tracking)**
- Deteksi otomatis saat membuka folder project di VS Code
- Timer fokus otomatis dimulai/berhenti berdasarkan aktivitas
- Context switching: catat perpindahan project secara real-time
- Idle detection: hentikan timer jika tidak ada aktivitas > 10 menit

### 2. **💡 Global Quick Capture (NEW!)**
- Hotkey global: **Ctrl+Shift+Space** (di mana saja di desktop)
- Mini input bar muncul instan (< 1 detik)
- Ketik ide/tugas → Enter → window tutup otomatis
- Teks langsung diproses ke AI agent & Knowledge Graph
- Notifikasi Telegram untuk feedback real-time

### 3. **🔗 Git Commit Hook Integration**
- Auto-tag tugas yang selesai dari commit message
- Otomatis centang habit coding saat ada commit
- Sinkronisasi real-time ke Telegram

### 4. **🌙 Bedtime Guardian (NEW!)**
- Deteksi otomatis saat kamu masih ngoding melewati batas jam malam
- **Windows Native Toast Notification** muncul langsung di layar laptop
- Reminder berkala setiap 15 menit (konfigurabel) selama kamu masih aktif
- Zero external dependency — menggunakan PowerShell native Windows 10/11
- Konfigurasi via `config.json`:
  - `bedtime_cutoff`: Batas jam malam (default: `"22:30"`)
  - `bedtime_reminder_interval_minutes`: Interval reminder (default: `15`)
  - `enable_bedtime_toast`: Aktifkan/nonaktifkan fitur (default: `true`)

## 🚀 Setup

### Prerequisites
- Python 3.11+
- Backend Server berjalan (http://localhost:8000)
- Telegram Bot Token (opsional untuk notifikasi)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Atau manual:
```bash
pip install pynput>=1.7.6
```

### 2. Konfigurasi `config.json`

Sudah tersedia. Edit sesuai setting Anda.

### 3. Jalankan Daemon

**Windows:**
```bash
run.bat
```

**Manual:**
```bash
python ambient_watcher.py
```

## 📖 Penggunaan

### Global Quick Capture

**Hotkey:** Ctrl+Shift+Space

1. Tekan hotkey di mana saja
2. Mini input bar muncul
3. Ketik ide/tugas
4. Tekan Enter → window tutup → teks diproses
5. Notifikasi Telegram masuk

---

**Made with 💡 for capturing ideas at lightning speed**
