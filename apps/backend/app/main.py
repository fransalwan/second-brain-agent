# apps/backend/app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

# PENTING: Gunakan titik (.) di depan untuk relative import
from .database import get_session, engine
from .models import Note, Profile, TimeLog, Donation

app = FastAPI(title="Second Brain API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Second Brain API is running. Brain loaded."}


@app.get("/test-db")
async def test_db_connection(session: AsyncSession = Depends(get_session)):
    # TAMBAHKAN BARIS INI UNTUK MEMBUKTIKAN KODE BARU TERBACA
    print(">>> CEK NAMA TABEL:", Note.__tablename__)

    try:
        result = await session.execute(select(Note).limit(1))
        note = result.scalars().first()
        return {
            "status": "success",
            "message": "Connected to Supabase successfully!",
            "sample_data": str(note)
            if note
            else "No notes found (this is fine for a new DB)",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
