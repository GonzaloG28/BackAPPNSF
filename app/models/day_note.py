# app/models/day_note.py — nuevo
from sqlalchemy import Column, Integer, Date, Text
from app.database import Base

class DayNote(Base):
    __tablename__ = "day_notes"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False)
    notes = Column(Text, nullable=True)