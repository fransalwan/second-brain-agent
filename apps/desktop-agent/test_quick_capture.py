#!/usr/bin/env python3
# apps/desktop-agent/test_quick_capture.py
"""Test script untuk Quick Capture dan Ambient Watcher integration."""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def test_config():
    """Verifikasi config.json ada dan valid."""
    config_path = Path(__file__).resolve().parent / "config.json"
    if not config_path.exists():
        print("❌ config.json tidak ditemukan!")
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print("✅ config.json valid")
        print(f"   User: {config.get('user_email')}")
        print(f"   Backend: {config.get('backend_url')}")
        print(f"   Quick Capture: {config.get('enable_quick_capture')}")
        return config
    except json.JSONDecodeError as e:
        print(f"❌ config.json parsing error: {e}")
        return None


def test_backend_connection(config):
    """Test koneksi ke backend."""
    backend_url = config.get("backend_url", "http://localhost:8000").rstrip("/")
    url = f"{backend_url}/"

    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            data = response.read().decode("utf-8")
            print("✅ Backend tersambung")
            print(f"   Response: {data[:50]}...")
            return True
    except Exception as e:
        print(f"❌ Gagal koneksi backend: {e}")
        return False


def test_quick_capture_api(config):
    """Test Quick Capture API endpoint."""
    backend_url = config.get("backend_url", "http://localhost:8000").rstrip("/")
    url = f"{backend_url}/api/v1/ambient/quick-capture"

    payload = {
        "email": config.get("user_email"),
        "text": "[TEST] Quick Capture API test dari test script",
        "source": "test_script",
        "notify_telegram": False,
    }

    headers = {
        "Content-Type": "application/json",
        "X-Ambient-Key": config.get("api_key", ""),
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            resp_data = response.read().decode("utf-8")
            result = json.loads(resp_data)
            if result.get("status") == "success":
                print("✅ Quick Capture API berfungsi")
                print(f"   Result: {result}")
                return True
            else:
                print(f"⚠️  API returned: {result}")
                return False
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            print(f"❌ API Error ({e.code}): {err_body}")
        except Exception:
            print(f"❌ API Error: {e.code}")
        return False
    except Exception as e:
        print(f"❌ Gagal test Quick Capture API: {e}")
        return False


def test_pynput():
    """Test pynput installation."""
    try:
        from pynput import keyboard
        print("✅ pynput terinstall")
        return True
    except ImportError:
        print("❌ pynput tidak terinstall")
        print("   Install: pip install pynput")
        return False


def main():
    print("=" * 60)
    print("  Second Brain Quick Capture & Ambient Watcher Test")
    print("=" * 60)
    print()

    # 1. Test config
    print("1️⃣  Checking config.json...")
    config = test_config()
    if not config:
        sys.exit(1)
    print()

    # 2. Test pynput
    print("2️⃣  Checking pynput...")
    has_pynput = test_pynput()
    if not has_pynput:
        print("   ⚠️  Quick Capture won't work without pynput")
    print()

    # 3. Test backend connection
    print("3️⃣  Testing backend connection...")
    has_backend = test_backend_connection(config)
    if not has_backend:
        sys.exit(1)
    print()

    # 4. Test Quick Capture API
    print("4️⃣  Testing Quick Capture API...")
    api_ok = test_quick_capture_api(config)
    print()

    # Summary
    print("=" * 60)
    if api_ok:
        print("✅ Semua test passed! Siap untuk menjalankan daemon.")
        print()
        print("Setup berikutnya:")
        print("1. Pastikan backend server running")
        print("2. Install pynput: pip install pynput")
        print("3. Jalankan: python ambient_watcher.py")
        print("4. Tekan Ctrl+Shift+Space untuk test Quick Capture")
    else:
        print("⚠️  Beberapa test gagal. Lihat error di atas.")
        if not has_pynput:
            print("   Install pynput: pip install pynput")
        if not has_backend:
            print("   Pastikan backend server berjalan")
    print("=" * 60)


if __name__ == "__main__":
    main()
