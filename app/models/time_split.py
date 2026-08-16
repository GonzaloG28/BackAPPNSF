# app/models/time_split.py
from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class TimeSplit(Base):
    __tablename__ = "time_splits"

    id = Column(Integer, primary_key=True, index=True)
    time_record_id = Column(Integer, ForeignKey("time_records.id", ondelete="CASCADE"), nullable=False)
    distance_mark = Column(Integer, nullable=False)
    segment_seconds = Column(Numeric(10, 2), nullable=False)
    cumulative_seconds = Column(Numeric(10, 2), nullable=False)

    time_record = relationship("TimeRecord", back_populates="splits")