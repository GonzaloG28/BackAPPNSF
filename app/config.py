# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REPORTS_EMAIL_TO: str = "programingsystemgg@gmail.com"

    # ── Resend (envío de reportes por correo, vía HTTP) ───────
    RESEND_API_KEY: str
    RESEND_FROM: str  # cambia esto si verificas tu propio dominio

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)


settings = Settings()