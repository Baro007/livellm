"""
LiveLLM - Main Application Entry Point
FastAPI web server serving the REST API and the Observability Dashboard.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import livellm.core.config  # Loads .env into os.environ
from livellm.storage.database import init_db
from livellm.storage.seed_data import generate_seed_data
from livellm.api.routes import router as api_router

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "livellm.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.path.exists(DB_PATH):
        generate_seed_data(DB_PATH)
    else:
        init_db(DB_PATH)
    yield


app = FastAPI(
    title="LiveLLM",
    description="Continuous Benchmarking Platform for LLM Degradation, Diurnal Peak Fluctuations & Nerf Detection",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "platform": "LiveLLM", "version": "1.0.0"}


if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.api_route("/", methods=["GET", "HEAD"])
    def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("livellm.api.main:app", host="0.0.0.0", port=8000, reload=True)
