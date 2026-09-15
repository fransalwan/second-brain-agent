from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Variabel Wajib
    DATABASE_URL: str
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_SECRET: str
    GOOGLE_API_KEY: str

    # Variabel dengan Default Value (Aman kalau tidak ada di .env)
    GEMINI_MODEL: str = "gemini-3.6-flash"
    APP_TIMEZONE: str = "Asia/Jakarta"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    ADMIN_CHAT_ID: Optional[int] = None
    GOOGLE_GENAI_USE_VERTEXAI: str = "FALSE"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Izinkan variabel tambahan di .env tanpa membuat error (opsional, tapi lebih aman)
        extra = "ignore"


settings = Settings()
