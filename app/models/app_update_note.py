# app/models/app_update_note.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func

from app.database import Base


class AppUpdateNote(Base):
    __tablename__ = "app_update_notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    body = Column(Text, nullable=False)
    # A quién se le muestra: "SWIMMERS", "COACHES" o "ALL".
    audience = Column(String(20), nullable=False, default="ALL")
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
