# app/models/day_note.py
from sqlalchemy import Column, Integer, Date, Text, String, UniqueConstraint
from app.database import Base

class DayNote(Base):
    __tablename__ = "day_notes"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False) # ¡IMPORTANTE! Se quita el unique=True de aquí
    profile = Column(String, nullable=False)  # COMPETITIVE | FORMATIVE
    category = Column(String, nullable=False) # Menores, Infantil, Juvenil A, etc.
    notes = Column(Text, nullable=True)

    # Restricción: No se puede repetir la misma categoría y perfil en el mismo día
    __table_args__ = (
        UniqueConstraint('date', 'profile', 'category', name='uix_day_note_profile_cat'),
    )