# app/models/swimmer_metric.py
from sqlalchemy import Column, Integer, Float, Date, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class SwimmerMetric(Base):
    __tablename__ = "swimmer_metrics"

    id = Column(Integer, primary_key=True, index=True)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"), nullable=False)
    recorded_at = Column(Date, nullable=False)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    wingspan_cm = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    swimmer = relationship("Swimmer", back_populates="metrics")