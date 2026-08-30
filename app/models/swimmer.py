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


CATEGORY_RULES = [
    ("Infantil C",           lambda age: age <= 9),
    ("Infantil A",           lambda age: age == 10),
    ("Infantil B1",          lambda age: age == 11),
    ("Infantil B2",          lambda age: age == 12),
    ("Juvenil A",            lambda age: 13 <= age <= 14),
    ("Juvenil B",            lambda age: 15 <= age <= 17),
    ("Todo Competidor",      lambda age: age >= 18),
]
 
# Subcategoría oficial → categoría general (agrupador de la tabla)
GENERAL_CATEGORY_MAP = {
    "Infantil C":      "Menores",
    "Infantil A":      "Infantil",
    "Infantil B1":     "Infantil",
    "Infantil B2":     "Infantil",
    "Juvenil A":       "Juvenil",
    "Juvenil B":       "Juvenil",
    "Todo Competidor": "Todo Competidor",
}

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
    category = Column(String(50), nullable=True) 
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

    photo_base64 = Column(String, nullable=True)

    hashed_password = Column(String(255), nullable=True) 
    must_change_password = Column(Boolean, nullable=False, default=True)
    payment_active = Column(Boolean, nullable=False, default=False) 


    @property
    def full_name(self) -> str:
        names = " ".join(filter(None, [self.first_name_1, self.first_name_2]))
        surnames = " ".join(filter(None, [self.last_name_1, self.last_name_2]))
        return f"{names} {surnames}".strip()

    def compute_age(self) -> int | None:
        """Edad por AÑO CALENDARIO (no por fecha exacta de cumpleaños)."""
        if not self.birth_date:
            return None
            
        current_year = date.today().year
        birth_year = self.birth_date.year
        
        return current_year - birth_year - 1
 
    def compute_category(self) -> str | None:
        """Subcategoría oficial (Infantil C, Infantil A, Infantil B1, Infantil B2,
        Juvenil A, Juvenil B, Todo Competidor) según edad por año calendario."""
        age = self.compute_age()
        if age is None:
            return None
        for label, rule in CATEGORY_RULES:
            if rule(age):
                return label
        return None
 
    @property
    def general_category(self) -> str | None:
        """Categoría general agrupadora: Menores, Infantil, Juvenil, Todo Competidor."""
        if not self.category:
            return None
        return GENERAL_CATEGORY_MAP.get(self.category)
 