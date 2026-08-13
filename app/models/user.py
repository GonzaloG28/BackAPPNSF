from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy import Boolean

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)  # 1 = activo, 0 = inactivo

    created_at = Column(DateTime, server_default=func.now())

    training_sessions = relationship("TrainingSession", backref="coach")
    convocatorias = relationship("Convocatoria", backref="created_by_user")
    import_logs = relationship("ImportLog", backref="uploaded_by_user")

    def __repr__(self):
        return f"<User {self.email}>"