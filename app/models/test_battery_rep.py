# app/models/test_battery_rep.py
#
# Una repetición individual dentro de una sesión de batería (TestBatteryResult).
# Antes TestBatteryResult guardaba UN solo tiempo por sesión; con baterías
# tipo "10x100m" se necesitan 10 tiempos numerados por sesión — cada uno es
# una fila acá. Aditivo: no toca TestBatteryResult.value_seconds (baterías
# de una sola marca siguen funcionando igual, sin filas en esta tabla).
from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class TestBatteryRep(Base):
    __tablename__ = "test_battery_reps"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("test_battery_results.id", ondelete="CASCADE"), nullable=False)
    rep_number = Column(Integer, nullable=False)  # 1..N, N = battery.reps_count
    time_seconds = Column(Numeric(10, 2), nullable=False)
    notes = Column(String(200), nullable=True)

    result = relationship("TestBatteryResult", back_populates="reps")
    splits = relationship(
        "TestBatteryRepSplit", back_populates="rep",
        cascade="all, delete-orphan", order_by="TestBatteryRepSplit.distance_mark",
    )

    __table_args__ = (UniqueConstraint("result_id", "rep_number", name="uq_result_rep_number"),)


class TestBatteryRepSplit(Base):
    """Parcial opcional DENTRO de una repetición (ej. el 50m de un 100m de la serie)."""
    __tablename__ = "test_battery_rep_splits"

    id = Column(Integer, primary_key=True, index=True)
    rep_id = Column(Integer, ForeignKey("test_battery_reps.id", ondelete="CASCADE"), nullable=False)
    distance_mark = Column(Integer, nullable=False)
    segment_seconds = Column(Numeric(10, 2), nullable=False)
    cumulative_seconds = Column(Numeric(10, 2), nullable=False)

    rep = relationship("TestBatteryRep", back_populates="splits")
