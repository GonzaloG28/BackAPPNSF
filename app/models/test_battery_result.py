# app/models/test_battery_result.py
from sqlalchemy import Column, Integer, Numeric, Date, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class TestBatteryResult(Base):
    __tablename__ = "test_battery_results"

    id = Column(Integer, primary_key=True, index=True)
    battery_id = Column(Integer, ForeignKey("test_batteries.id"), nullable=False)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"), nullable=False)
    recorded_date = Column(Date, nullable=False)
    value_seconds = Column(Numeric(10, 2), nullable=True)  # si battery.result_type == TIME
    value_reps = Column(Integer, nullable=True)  # si battery.result_type == REPETITIONS
    notes = Column(String(200), nullable=True)
    split_increment = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    battery = relationship("TestBattery", back_populates="results")
    swimmer = relationship("Swimmer")
    splits = relationship(
        "TestBatterySplit", back_populates="result",
        cascade="all, delete-orphan", order_by="TestBatterySplit.distance_mark",
    )
    # Repeticiones numeradas (batteries con reps_count>1, ej. 10x100m) —
    # cada una con su propio tiempo y, opcionalmente, sus propios parciales.
    reps = relationship(
        "TestBatteryRep", back_populates="result",
        cascade="all, delete-orphan", order_by="TestBatteryRep.rep_number",
    )
