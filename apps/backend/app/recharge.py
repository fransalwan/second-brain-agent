# apps/backend/app/recharge.py
"""Modul Mode Jeda (Recharge & Mood Booster).

Menyediakan kurasi musik YouTube Music, preset pemesanan kopi ShopeeFood,
rekomendasi tontonan santai (feel-good watchlist), serta ide aktivitas offline untuk menyegarkan pikiran.
"""

import random
import urllib.parse
from typing import Dict, List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ---------------------------------------------------------------------------
# 1. YouTube Music Curated Playlists / Search Links
# ---------------------------------------------------------------------------
YOUTUBE_MUSIC_PLAYLISTS = [
    {
        "id": "lofi",
        "title": "🎧 Lofi & Chill Beats",
        "desc": "Beat santai penenang pikiran untuk istirahat atau kerja rileks.",
        "url": "https://music.youtube.com/search?q=lofi+chill+beats+relax",
    },
    {
        "id": "jazz",
        "title": "☕ Coffee Shop Jazz",
        "desc": "Alunan akustik dan piano jazz seperti di kedai kopi senja.",
        "url": "https://music.youtube.com/search?q=coffee+shop+jazz+instrumental",
    },
    {
        "id": "indie_indo",
        "title": "🎸 Indie Santai Indonesia",
        "desc": "Lagu-lagu hangat indie lokal pengembali mood.",
        "url": "https://music.youtube.com/search?q=indie+chill+indonesia+playlist",
    },
    {
        "id": "ambient",
        "title": "🌧️ Ambient Rain & Nature",
        "desc": "Suara hujan dan alam untuk meredakan ketegangan otak.",
        "url": "https://music.youtube.com/search?q=peaceful+rain+nature+ambient",
    },
    {
        "id": "upbeat",
        "title": "⚡ Upbeat Energy Boost",
        "desc": "Ritme berenergi untuk menaikkan mood dan mengatasi kantuk.",
        "url": "https://music.youtube.com/search?q=upbeat+energy+mood+booster",
    },
]

# ---------------------------------------------------------------------------
# 2. ShopeeFood Coffee Presets & Deep Links
# ---------------------------------------------------------------------------
SHOPEEFOOD_BASE_URL = "https://shopee.co.id/now-food/search?keyword="


def build_shopeefood_url(keyword: str) -> str:
    """Membuat tautan pencarian ShopeeFood yang membuka aplikasi Shopee di HP / browser."""
    encoded = urllib.parse.quote(keyword.strip())
    return f"{SHOPEEFOOD_BASE_URL}{encoded}"


COFFEE_PRESETS = [
    {
        "title": "☕ Kopi Susu Gula Aren",
        "keyword": "kopi susu gula aren",
        "desc": "Manis legit menyegarkan untuk mood booster cepat.",
    },
    {
        "title": "☕ Americano / Kopi Hitam",
        "keyword": "americano",
        "desc": "Segar, pekat, tanpa gula untuk mengusir kantuk dan fokus.",
    },
    {
        "title": "☕ Kopi Kenangan / Janji Jiwa",
        "keyword": "kopi kenangan",
        "desc": "Langganan favorit terdekat yang siap antar cepat.",
    },
    {
        "title": "☕ Cafe Latte / Cappuccino",
        "keyword": "cafe latte",
        "desc": "Lembut dan creamy dengan foam susu yang hangat.",
    },
]

# ---------------------------------------------------------------------------
# 3. Feel-Good Movies & Shows Watchlist
# ---------------------------------------------------------------------------
FEEL_GOOD_MOVIES = [
    {
        "title": "The Secret Life of Walter Mitty",
        "type": "Film",
        "genre": "Petualangan / Inspiratif",
        "platform": "Disney+ / Apple TV",
        "reason": "Visual pemandangan Islandia yang memukau dan kisah inspiratif keluar dari rutinitas yang membosankan.",
    },
    {
        "title": "My Neighbor Totoro (Studio Ghibli)",
        "type": "Film Animasi",
        "genre": "Family / Fantasy / Healing",
        "platform": "Netflix",
        "reason": "Sangat damai, tanpa villain, penuh kehangatan alam pedesaan yang menenangkan hati.",
    },
    {
        "title": "Soul (Pixar)",
        "type": "Film Animasi",
        "genre": "Makna Hidup / Musik",
        "platform": "Disney+",
        "reason": "Mengingatkan kita bahwa hidup bukan cuma tentang ambisi dan target, tapi menikmati percikan-percikan kecil setiap hari.",
    },
    {
        "title": "Ted Lasso",
        "type": "Serial",
        "genre": "Komedi / Heartwarming",
        "platform": "Apple TV+",
        "reason": "Optimisme murni yang menular dan humor ramah yang pasti menaikkan mood.",
    },
    {
        "title": "Midnight Diner: Tokyo Stories",
        "type": "Serial",
        "genre": "Slice of Life / Kuliner",
        "platform": "Netflix",
        "reason": "Tenang, hangat, ditemani cerita manusia sederhana di kedai malam Tokyo yang menyejukkan pikiran.",
    },
    {
        "title": "Our Planet / Planet Earth",
        "type": "Dokumenter",
        "genre": "Eksplorasi Alam",
        "platform": "Netflix",
        "reason": "Keindahan alam liar dan suara David Attenborough yang membuat pikiran rileks seketika.",
    },
]

# ---------------------------------------------------------------------------
# 4. Offline Refresh & Hangout Ideas
# ---------------------------------------------------------------------------
OFFLINE_ACTIVITIES = [
    {
        "title": "🚶‍♂️ Jalan Santai 15 Menit Tanpa HP",
        "detail": "Tinggalkan ponsel di meja. Keluar jalan santai keliling komplek atau pekarangan sambil menghirup udara segar.",
    },
    {
        "title": "☕ Ngopi / Nongkrong Bareng Teman",
        "detail": "Kirim pesan ke teman atau sahabat lama: 'Lagi senggang gak? Ngopi santai yuk sore ini.' Interaksi sosial adalah peredam stres alami.",
    },
    {
        "title": "💦 Cuci Muka & Minum Air Es Segar",
        "detail": "Segarkan sensor wajah dengan air dingin, lalu minum satu gelas besar air mineral untuk rehidrasi sel otak.",
    },
    {
        "title": "🧘 5 Menit Peregangan Badan & Otot Mata",
        "detail": "Regangkan bahu, leher, dan putar pandangan mata melihat objek hijau yang jauh (aturan 20-20-20) untuk melemaskan otot mata lelah.",
    },
    {
        "title": "🗺️ Eksplor Spot Kafe Baru",
        "detail": "Buka Google Maps, cari 'coffee shop' dengan rating tinggi berjarak 1-3 km dari lokasimu, lalu datangi untuk suasana kerja baru.",
    },
    {
        "title": "🚿 Mandi Air Hangat / Dingin",
        "detail": "Mandi menyegarkan untuk 'mereset' tubuh seolah memulai babak baru yang segar.",
    },
]


def get_random_movie() -> dict:
    """Mengambil satu rekomendasi film santai secara acak."""
    return random.choice(FEEL_GOOD_MOVIES)


def get_random_activity() -> dict:
    """Mengambil satu ide aktivitas jeda secara acak."""
    return random.choice(OFFLINE_ACTIVITIES)


# ---------------------------------------------------------------------------
# 5. Telegram Inline Keyboards
# ---------------------------------------------------------------------------
def build_chill_menu_keyboard() -> InlineKeyboardMarkup:
    """Menu utama Mode Jeda."""
    keyboard = [
        [
            InlineKeyboardButton("🎵 YouTube Music", callback_data="chill:music"),
            InlineKeyboardButton("☕ Kopi ShopeeFood", callback_data="chill:coffee"),
        ],
        [
            InlineKeyboardButton("🎬 Saran Nonton", callback_data="chill:movie"),
            InlineKeyboardButton("🚶‍♂️ Ide Hangout", callback_data="chill:hangout"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_music_keyboard() -> InlineKeyboardMarkup:
    """Menu pilihan playlist YouTube Music."""
    buttons = []
    for p in YOUTUBE_MUSIC_PLAYLISTS:
        buttons.append([InlineKeyboardButton(p["title"], url=p["url"])])
    buttons.append(
        [InlineKeyboardButton("🔙 Kembali ke Menu Jeda", callback_data="chill:main")]
    )
    return InlineKeyboardMarkup(buttons)


def build_coffee_keyboard() -> InlineKeyboardMarkup:
    """Menu pilihan preset pemesanan kopi ShopeeFood."""
    buttons = []
    for c in COFFEE_PRESETS:
        url = build_shopeefood_url(c["keyword"])
        buttons.append([InlineKeyboardButton(c["title"], url=url)])
    buttons.append(
        [InlineKeyboardButton("🔙 Kembali ke Menu Jeda", callback_data="chill:main")]
    )
    return InlineKeyboardMarkup(buttons)


def build_movie_keyboard() -> InlineKeyboardMarkup:
    """Menu rekomendasi film dengan tombol saran lain."""
    keyboard = [
        [InlineKeyboardButton("🔄 Saran Film Lain", callback_data="chill:movie")],
        [InlineKeyboardButton("🔙 Kembali ke Menu Jeda", callback_data="chill:main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_hangout_keyboard() -> InlineKeyboardMarkup:
    """Menu ide hangout dengan tombol ide lain."""
    keyboard = [
        [InlineKeyboardButton("🔄 Ide Aktivitas Lain", callback_data="chill:hangout")],
        [InlineKeyboardButton("🔙 Kembali ke Menu Jeda", callback_data="chill:main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_break_reminder_keyboard() -> InlineKeyboardMarkup:
    """Tombol cepat saat notifikasi pengingat istirahat 90 menit muncul."""
    keyboard = [
        [
            InlineKeyboardButton(
                "☕ Pesan Kopi (ShopeeFood)",
                url=build_shopeefood_url("kopi susu"),
            ),
            InlineKeyboardButton(
                "🎵 Musik Santai",
                url="https://music.youtube.com/search?q=coffee+shop+jazz+instrumental",
            ),
        ],
        [
            InlineKeyboardButton(
                "🌿 Buka Mode Jeda Lengkap", callback_data="chill:main"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
