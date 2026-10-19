"""Central configuration. Secrets/URLs come from env only — never hardcoded."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg2://watersphere:devpass@localhost:5433/watersphere"
    )
    jwt_secret: str = "dev-only-secret-change-in-prod"
    jwt_expire_min: int = 60
    jwt_algorithm: str = "HS256"
    supply_reserve_pct: float = 0.05
    # Allocator engine: "rule" (default, heuristic) or "lp" (PuLP/CBC optimal).
    supply_optimizer: str = "rule"
    cors_origins: str = ("http://localhost:5173,http://127.0.0.1:5173,"
                         "http://localhost:3000,http://127.0.0.1:3000")
    # Provisional WAR bands (env-overridable, never hardcoded in logic).
    # Recalibrate with municipal stakeholders before any production use.
    war_safe: float = 1.0
    war_moderate: float = 0.85
    war_high: float = 0.70


settings = Settings()
