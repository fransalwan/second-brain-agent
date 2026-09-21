# Second Brain Ambient Desktop Watcher ⚡

Daemon pemantau latar belakang (*ambient watcher*) untuk Windows yang secara otomatis melacak sesi fokus (*deep work*) saat kamu membuka atau menutup project di **Visual Studio Code**, tanpa perlu mengirim perintah manual di Telegram.

---

## 🎯 Fitur Utama

1. **Auto-Start Timer:** Saat membuka folder project di VS Code (misal `second-brain-agent` atau `CV PELANGI EFRATA`), timer fokus langsung berjalan.
2. **Auto-Stop Timer:** Saat VS Code ditutup atau laptop dimatikan, timer otomatis dihentikan dan durasi tersimpan ke database Supabase.
3. **Auto-Check Habit Harian:** Jika durasi fokus mencapai $\ge 15$ menit, habit harian terkait coding/kerja (seperti *"Ngoding / Build Project"*, *"Fokus"* atau sesuai nama project) otomatis dicentang dan streak harian bertambah tanpa perlu manual `/check`!
4. **Cerdas (Graceful Context):** Kamu bebas berpindah ke browser (membaca dokumentasi, mencari di Google/StackOverflow) atau terminal tanpa memutus sesi timer, selama jendela VS Code masih berjalan.
5. **Deteksi Idle (Anti-False Tracking):** Jika kamu meninggalkan laptop lebih dari 10 menit (tidak ada ketikan/mouse), timer otomatis berhenti sementara dengan alasan `idle_timeout`.
6. **Context Switching:** Jika kamu berganti folder kerja di VS Code, timer sesi sebelumnya otomatis dihitung dan sesi project baru langsung dimulai.
7. **Zero External Dependencies:** Berjalan langsung dengan Python bawaan Windows tanpa perlu install library compiler C++ tambahan (`pip install` 0 MB).

---

## ⚙️ Konfigurasi (`config.json`)

Buka dan sesuaikan file `apps/desktop-agent/config.json`:

```json
{
  "backend_url": "http://localhost:8000",
  "api_key": "second-brain-ambient-key",
  "user_email": "fransalwan55@gmail.com",
  "poll_interval_seconds": 3,
  "idle_threshold_seconds": 600,
  "notify_telegram": true,
  "project_mappings": {
    "second-brain-agent": "Second Brain Agent",
    "scrap-yard-dashboard": "Usaha & Karir",
    "CV PELANGI EFRATA": "Usaha & Karir",
    "slp-iris": "Kuliah & Riset",
    "Matkul": "Kuliah & Riset",
    "default": "Usaha & Karir"
  }
}
```

- **`user_email`**: Email akun Second Brain kamu.
- **`idle_threshold_seconds`**: Batas toleransi tanpa aktivitas keyboard/mouse sebelum timer di-pause (default: 600 detik = 10 menit).
- **`notify_telegram`**: Set `true` agar bot Telegram mengirimkan notifikasi ringkas saat sesi fokus dimulai/selesai.
- **`project_mappings`**: Kata kunci nama folder di VS Code yang dipetakan ke nama Area / Project di Second Brain.

---

## 🚀 Cara Menjalankan

Cukup jalankan script dengan Python:

```powershell
cd apps/desktop-agent
python ambient_watcher.py
```

Output log akan muncul di terminal:
```text
19:15:00 [INFO] Second Brain Ambient Watcher aktif!
19:15:00 [INFO] Target User: fransalwan55@gmail.com
19:15:03 [INFO] [TIMER START] Fokus dimulai: 'Second Brain Agent' (Status: started)
...
19:45:00 [INFO] [TIMER STOP] Fokus dihentikan: 'Second Brain Agent' (Durasi: 30 menit, Alasan: window_closed)
```

Untuk menghentikan pemantauan, tekan `Ctrl + C`. Timer yang sedang berjalan akan disimpan dan dihentikan dengan aman.

---

## 🎯 Memasang Git Hook (Auto-Done Tasks & Habit Sync)

Kamu bisa menghubungkan repo Git lokal mana saja ke Second Brain dengan 1 perintah:

```powershell
# Pasang ke repository saat ini:
python apps/desktop-agent/install_git_hook.py

# Atau pasang ke repository lain:
python apps/desktop-agent/install_git_hook.py "C:\Path\Ke\Repo\Lain"
```

### Cara Kerja:
Saat kamu melakukan `git commit`:
- `git commit -m "feat(auth): fix login bug #3"` -> Tugas #3 otomatis berstatus `completed`.
- `git commit -m "revisi invoice klien selesai"` -> Tugas yang judulnya cocok otomatis diselesaikan.
- Commit pertama hari ini otomatis mencentang habit ngoding harianmu.
- Bot Telegram mengirim notifikasi konfirmasi bahwa tugas telah beres!

