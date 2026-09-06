# app/models/test_battery_split.py
from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class TestBatterySplit(Base):
    __tablename__ = "test_battery_splits"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("test_battery_results.id", ondelete="CASCADE"), nullable=False)
    distance_mark = Column(Integer, nullable=False)
    segment_seconds = Column(Numeric(10, 2), nullable=False)
    cumulative_seconds = Column(Numeric(10, 2), nullable=False)

    result = relationship("TestBatteryResult", back_populates="splits")
