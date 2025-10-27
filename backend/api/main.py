# backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.routes import game, ml  # existing imports

app = FastAPI(title="Network Flow Defence API")

# ✅ Allow CORS for frontend (during Render deployment)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include routers
app.include_router(game.router, prefix="/game")
app.include_router(ml.router, prefix="/ml")

@app.get("/")
def root():
    return {"status": "Server is live on Render!"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port)
