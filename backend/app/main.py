"""FastAPI entrypoint. Routers thin; logic in services/inference."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app import inference
from app.config import settings
from app.routers import auth, complaints, data, forecast, gis, leakage as leakage_router, stress as stress_router, supply
from app.routers.auth import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    inference.startup()  # loads xgb models + scaler + active manifest once
    yield


app = FastAPI(title="WaterSphere AI", version="0.1.0-mvp", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(data.router)
app.include_router(forecast.router)
app.include_router(stress_router.router)
app.include_router(supply.router)
app.include_router(gis.router)
app.include_router(leakage_router.router)
app.include_router(complaints.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
