# app/models/day_note.py — actualiza el modelo si aún tiene solo (date, notes)
from sqlalchemy import Column, Integer, Date, Text, String, UniqueConstraint
from app.database import Base

class DayNote(Base):
    __tablename__ = "day_notes"
    __table_args__ = (UniqueConstraint("date", "profile", "category", name="uq_day_profile_category"),)

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    profile = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)