# app/models/swimmer.py — reemplaza first_name/last_name por 2+2, agrega cálculo de categoría
from sqlalchemy import Column, Integer, String, Date, Enum, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from datetime import date
import enum

from app.database import Base


class SwimmerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    DELETED = "DELETED"


class SwimmerGender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class SwimmerProfile(str, enum.Enum):
    COMPETITIVE = "COMPETITIVE"
    FORMATIVE = "FORMATIVE"

class Swimmer(Base):
    __tablename__ = "swimmers"

    id = Column(Integer, primary_key=True, index=True)
    first_name_1 = Column(String(50), nullable=False)
    first_name_2 = Column(String(50), nullable=True)
    last_name_1 = Column(String(50), nullable=False)
    last_name_2 = Column(String(50), nullable=True)
    birth_date = Column(Date, nullable=True)
    document_id = Column(String(50), unique=True, nullable=True, index=True)
    gender = Column(Enum(SwimmerGender), nullable=True)
    category = Column(String(50), nullable=True)  # se recalcula, no se edita a mano
    comuna = Column(String(100), nullable=True)
    institution = Column(String(150), nullable=True)  # colegio/universidad/club, opcional
    phone = Column(String(30), nullable=True)
    email = Column(String(150), nullable=True)

    profile = Column(Enum(SwimmerProfile), nullable=True)
    is_federated = Column(Boolean, nullable=True, default=False)

    status = Column(Enum(SwimmerStatus), default=SwimmerStatus.ACTIVE, nullable=False)
    status_reason = Column(String(255), nullable=True)
    status_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    metrics = relationship("SwimmerMetric", back_populates="swimmer", cascade="all, delete-orphan")
    time_records = relationship("TimeRecord", back_populates="swimmer", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="swimmer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="swimmer", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        names = " ".join(filter(None, [self.first_name_1, self.first_name_2]))
        surnames = " ".join(filter(None, [self.last_name_1, self.last_name_2]))
        return f"{names} {surnames}".strip()

    def compute_category(self) -> str:
        if not self.birth_date:
            return None
        today = date.today()
        age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        if age < 13:
            return "Infantil"
        elif 13 <= age <= 14:
            return "Juvenil A"
        elif 15 <= age <= 17:
            return "Juvenil B"
        else:
            return "Todo Competidor"