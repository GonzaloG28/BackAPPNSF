# app/models/club_record.py
from sqlalchemy import Column, Integer, Numeric, Date, String, Enum, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.swimmer import SwimmerGender


class ClubRecord(Base):
    """
    Récord VIGENTE por (event_type_id, category, gender, pool_length).
    Una sola fila por slot (upsert), no historial: evita recalcular
    la matriz completa en cada lectura del panel de Mejores Marcas.
    """
    __tablename__ = "club_records"

    id = Column(Integer, primary_key=True, index=True)
    event_type_id = Column(Integer, ForeignKey("event_types.id"), nullable=False)
    category = Column(String(50), nullable=False)
    gender = Column(Enum(SwimmerGender), nullable=False)
    pool_length = Column(Integer, nullable=False)  # 25 o 50
    time_seconds = Column(Numeric(10, 2), nullable=False)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"), nullable=False)
    time_record_id = Column(Integer, ForeignKey("time_records.id", ondelete="CASCADE"), nullable=False)
    achieved_date = Column(Date, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    event_type = relationship("EventType")
    swimmer = relationship("Swimmer")
    time_record = relationship("TimeRecord")

    __table_args__ = (
        UniqueConstraint("event_type_id", "category", "gender", "pool_length", name="uq_club_record_slot"),
    )
