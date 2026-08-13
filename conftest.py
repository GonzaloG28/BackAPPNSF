# conftest.py — fixtures reutilizables (necesarias para los tests de arriba)
import pytest
from app.database import SessionLocal
from app.models.swimmer import Swimmer, SwimmerStatus
from app.models.user import User
from app.core.security import hash_password, create_access_token

@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def active_swimmer(db_session):
    s = Swimmer(first_name="Test", last_name="Swimmer", status=SwimmerStatus.ACTIVE)
    db_session.add(s)
    db_session.commit()
    yield s
    db_session.delete(s)
    db_session.commit()

@pytest.fixture
def existing_swimmer(db_session):
    from datetime import date
    s = Swimmer(
        first_name="María", last_name="González",
        document_id="11111111-1", birth_date=date(2012, 3, 15),
        status=SwimmerStatus.ACTIVE
    )
    db_session.add(s)
    db_session.commit()
    yield s
    db_session.delete(s)
    db_session.commit()

@pytest.fixture
def auth_headers(db_session):
    user = db_session.query(User).first()
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}