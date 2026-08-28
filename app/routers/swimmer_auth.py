# app/routers/swimmer_auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.core.security import hash_password, verify_password
from app.core.swimmer_security import create_swimmer_token
from app.models.swimmer import Swimmer
from app.schemas.swimmer_auth import SwimmerLoginRequest, SwimmerLoginResponse, SwimmerChangePasswordRequest
from app.utils.rut_auth import rut_username, rut_default_password

router = APIRouter(prefix="/swimmer-auth", tags=["swimmer-auth"])


@router.post("/login", response_model=SwimmerLoginResponse)
def swimmer_login(payload: SwimmerLoginRequest, db: Session = Depends(get_db)):
    normalized_username = rut_username(payload.username)

    swimmer = db.query(Swimmer).filter(Swimmer.document_id == normalized_username).first()
    if not swimmer:
        raise HTTPException(status_code=401, detail="RUT o contraseña incorrectos")

    # Primer login: la contraseña vigente es el RUT con puntos, incluso si aún
    # no se generó hashed_password en la base de datos.
    if swimmer.hashed_password is None:
        expected_default = rut_default_password(swimmer.document_id)
        if payload.password != expected_default:
            raise HTTPException(status_code=401, detail="RUT o contraseña incorrectos")

        swimmer.hashed_password = hash_password(expected_default)
        swimmer.must_change_password = True
        db.add(swimmer)
        db.commit()
    else:
        if not verify_password(payload.password, swimmer.hashed_password):
            raise HTTPException(status_code=401, detail="RUT o contraseña incorrectos")

    token = create_swimmer_token(swimmer.id)
    return SwimmerLoginResponse(access_token=token, must_change_password=swimmer.must_change_password)