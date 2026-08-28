# app/routers/swimmer_auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_swimmer
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



@router.post("/change-password")
def change_password(
    payload: SwimmerChangePasswordRequest,
    swimmer: Swimmer = Depends(get_current_swimmer),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, swimmer.hashed_password):
        raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")

    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 8 caracteres")

    swimmer.hashed_password = hash_password(payload.new_password)
    swimmer.must_change_password = False
    db.add(swimmer)
    db.commit()
    return {"ok": True}



@router.get("/me")
def swimmer_me(swimmer: Swimmer = Depends(get_current_swimmer)):
    return {
        "id": swimmer.id, "full_name": swimmer.full_name, "document_id": swimmer.document_id,
        "must_change_password": swimmer.must_change_password, "payment_active": swimmer.payment_active,
    }