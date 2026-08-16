# app/models/qualifying_time.py
from sqlalchemy import Column, Integer, Numeric, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.swimmer import SwimmerGender


class QualifyingTime(Base):
    __tablename__ = "qualifying_times"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    event_type_id = Column(Integer, ForeignKey("event_types.id"), nullable=False)
    category = Column(String(50), nullable=True)
    gender = Column(Enum(SwimmerGender), nullable=True)
    min_time_seconds = Column(Numeric(10, 2), nullable=True)
    pool_length = Column(Integer, nullable=True) 
    competition = relationship("Competition", back_populates="qualifying_times")
    event_type = relationship("EventType")