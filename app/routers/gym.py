# app/routers/gym.py — reemplaza completo
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.gym_record import Exercise, GymRecord

exercises_router = APIRouter(prefix="/exercises", tags=["gym"], dependencies=[Depends(get_current_user)])


@exercises_router.get("")
def list_exercises(db: Session = Depends(get_db)):
    return db.query(Exercise).all()


@exercises_router.post("", status_code=201)
def create_exercise(name: str, db: Session = Depends(get_db)):
    existing = db.query(Exercise).filter(Exercise.name.ilike(name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un ejercicio con ese nombre")
    exercise = Exercise(name=name)
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


@exercises_router.delete("/{exercise_id}", status_code=204)
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    """Elimina el ejercicio y TODO su historial de RM de todos los nadadores."""
    db.query(GymRecord).filter(GymRecord.exercise_id == exercise_id).delete()
    db.query(Exercise).filter(Exercise.id == exercise_id).delete()
    db.commit()