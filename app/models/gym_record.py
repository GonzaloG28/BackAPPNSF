# app/models/gym_record.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)


class GymRecord(Base):
    """
    Historial de RM: cada carga es un registro nuevo con su fecha,
    nunca se sobreescribe (igual que SwimmerMetric en biometría).
    """
    __tablename__ = "gym_records"

    id = Column(Integer, primary_key=True, index=True)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    one_rm_kg = Column(Numeric(6, 2), nullable=False)
    # Peso x reps que se usó para calcular el RM (fórmula de Brzycki) — null
    # en registros anteriores a este campo, donde solo se guardó el RM.
    weight_kg = Column(Numeric(6, 2), nullable=True)
    reps = Column(Integer, nullable=True)
    recorded_at = Column(DateTime, server_default=func.now())

    swimmer = relationship("Swimmer")
    exercise = relationship("Exercise")