from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Second Brain API", version="0.1.0")

# Setup CORS biar nanti frontend React bisa akses
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Nanti kita kunci ke domain frontend aja
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Second Brain API is running. Brain loaded."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}