# app/models/competition.py
from sqlalchemy import Column, Integer, String, Date, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    organizer = Column(String(150), nullable=True)
    date = Column(Date, nullable=True)          # se mantiene por compatibilidad, deja de usarse en el form
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    location = Column(String(150), nullable=True)
    pool_length = Column(Integer, nullable=True)  # 25 o 50
    categories = Column(JSON, nullable=True)       # ["Infantil", "Juvenil A", ...]
    max_events_per_swimmer = Column(Integer, nullable=False, default=3)

    qualifying_times = relationship("QualifyingTime", back_populates="competition", cascade="all, delete-orphan")
    convocatorias = relationship("Convocatoria", back_populates="competition")