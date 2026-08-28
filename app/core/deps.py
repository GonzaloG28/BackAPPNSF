# app/core/deps.py — agregar get_current_user a lo que ya tienes
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.swimmer_security import create_swimmer_token
from jose import JWTError, jwt

from app.database import SessionLocal
from app.core.security import decode_access_token
from app.models.swimmer import Swimmer
from app.config import settings
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la credencial",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_swimmer(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Swimmer:
    from app.models.swimmer import Swimmer
    credentials_exception = HTTPException(status_code=401, detail="Credencial inválida")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "swimmer":
            raise credentials_exception
        swimmer_id = payload.get("sub")
    except JWTError:
        raise credentials_exception

    swimmer = db.query(Swimmer).filter(Swimmer.id == int(swimmer_id)).first()
    if swimmer is None:
        raise credentials_exception
    return swimmer