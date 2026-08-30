# app/models/convocatoria_entry.py
from sqlalchemy import Column, Integer, Numeric, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship

from app.database import Base


class ConvocatoriaEntry(Base):
    __tablename__ = "convocatoria_entries"

    id = Column(Integer, primary_key=True, index=True)
    convocatoria_id = Column(Integer, ForeignKey("convocatorias.id"), nullable=False)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"), nullable=False)
    event_type_id = Column(Integer, ForeignKey("event_types.id"), nullable=False)
    qualifying_time_id = Column(Integer, ForeignKey("qualifying_times.id"), nullable=True)
    best_time_seconds = Column(Numeric(10, 2), nullable=True)
    selected = Column(Boolean, default=False)
    time_record_date = Column(Date, nullable=True)
    time_record_id = Column(Integer, ForeignKey("time_records.id"), nullable=True)
    convocatoria = relationship("Convocatoria", back_populates="entries")
    swimmer = relationship("Swimmer")
    event_type = relationship("EventType")
    qualifying_time = relationship("QualifyingTime")
    is_nt_inscription = Column(Boolean, default=False)