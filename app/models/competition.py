from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship

from app.database import Base


class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    organizer = Column(String(150), nullable=True)
    date = Column(Date, nullable=False)
    location = Column(String(150), nullable=True)
    max_events_per_swimmer = Column(Integer, nullable=False, default=3)
    qualifying_times = relationship("QualifyingTime", back_populates="competition", cascade="all, delete-orphan")
    pool_length = Column(Integer, nullable=True)
    convocatorias = relationship("Convocatoria", back_populates="competition")