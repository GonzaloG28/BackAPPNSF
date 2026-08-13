# app/models/attendance_log.py
from sqlalchemy import Column, Integer, Date, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class AttendanceLog(Base):
    """
    Log simple: un registro por nadador por día. Solo Cumplió/No Cumplió.
    Reemplaza el modelo de turnos AM/PM para el flujo de asistencia diaria.
    """
    __tablename__ = "attendance_logs"
    __table_args__ = (UniqueConstraint("swimmer_id", "date", name="uq_swimmer_date"),)

    id = Column(Integer, primary_key=True, index=True)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"), nullable=False)
    date = Column(Date, nullable=False)
    complied = Column(Boolean, nullable=False)  # True=Cumplió, False=No Cumplió

    swimmer = relationship("Swimmer")