# app/models/test_battery.py
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TestResultType(str, enum.Enum):
    TIME = "TIME"
    REPETITIONS = "REPETITIONS"


class TestBattery(Base):
    __tablename__ = "test_batteries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(String(300), nullable=True)
    structure_label = Column(String(50), nullable=True)  # "10x100", informativo
    result_type = Column(Enum(TestResultType), default=TestResultType.TIME, nullable=False)
    distance_m = Column(Integer, nullable=True)  # distancia nominal, habilita splits
    allows_splits = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    results = relationship(
        "TestBatteryResult", back_populates="battery",
        cascade="all, delete-orphan",
    )
