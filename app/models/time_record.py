# app/models/time_record.py
from sqlalchemy import Column, Integer, Numeric, Date, Boolean, ForeignKey, Enum, String
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TimeSource(str, enum.Enum):
    TRAINING = "TRAINING"
    COMPETITION = "COMPETITION"
    IMPORT = "IMPORT"


class TimeRecord(Base):
    __tablename__ = "time_records"

    id = Column(Integer, primary_key=True, index=True)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"), nullable=False)
    event_type_id = Column(Integer, ForeignKey("event_types.id"), nullable=False)
    time_seconds = Column(Numeric(10, 2), nullable=False)
    recorded_date = Column(Date, nullable=False)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=True)
    source = Column(Enum(TimeSource), default=TimeSource.TRAINING, nullable=False)
    location_note = Column(String(150), nullable=True)
    is_official = Column(Boolean, default=False)
    pool_length = Column(Integer, nullable=True)  # 25 o 50
    split_increment = Column(Integer, nullable=True)  # 50 o 100, null = sin parciales

    swimmer = relationship("Swimmer", back_populates="time_records")
    event_type = relationship("EventType")
    competition = relationship("Competition")
    splits = relationship(
        "TimeSplit", back_populates="time_record",
        cascade="all, delete-orphan", order_by="TimeSplit.distance_mark",
    )