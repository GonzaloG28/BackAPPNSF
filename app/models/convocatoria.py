# app/models/convocatoria.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ConvocatoriaStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    EXPORTED = "EXPORTED"


class Convocatoria(Base):
    __tablename__ = "convocatorias"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(ConvocatoriaStatus), default=ConvocatoriaStatus.DRAFT, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    competition = relationship("Competition", back_populates="convocatorias")
    entries = relationship("ConvocatoriaEntry", back_populates="convocatoria", cascade="all, delete-orphan")