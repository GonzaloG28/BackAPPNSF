# app/models/payment.py
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"), nullable=False)
    period = Column(String(20), nullable=False)  # ej. "2026-07"
    amount = Column(Numeric(10, 2), nullable=False)
    paid = Column(Boolean, default=False)
    paid_at = Column(DateTime, nullable=True)

    swimmer = relationship("Swimmer", back_populates="payments")