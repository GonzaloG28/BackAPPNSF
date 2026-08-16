# app/routers/competitions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional


from app.schemas.competition import CompetitionCreate
from app.core.deps import get_db
from app.models.competition import Competition
from app.models.qualifying_time import QualifyingTime
from app.core.deps import get_current_user
from app.schemas.competition import QualifyingTimeUpdate
from app.schemas.competition import CompetitionUpdate



router = APIRouter(prefix="/competitions", tags=["competitions"], dependencies=[Depends(get_current_user)])


@router.get("")
def list_competitions(db: Session = Depends(get_db)):
    return db.query(Competition).order_by(Competition.date.desc()).all()


@router.post("", status_code=201)
def create_competition(payload: CompetitionCreate, db: Session = Depends(get_db)):
    competition = Competition(**payload.model_dump())
    db.add(competition)
    db.commit()
    db.refresh(competition)
    return competition


@router.get("/{competition_id}")
def get_competition(competition_id: int, db: Session = Depends(get_db)):
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competencia no encontrada")
    return competition


@router.get("/{competition_id}/qualifying-times")
def get_qualifying_times(competition_id: int, db: Session = Depends(get_db)):
    return db.query(QualifyingTime).filter(
        QualifyingTime.competition_id == competition_id
    ).all()


@router.post("/{competition_id}/qualifying-times", status_code=201)
def create_qualifying_time(
    competition_id: int, event_type_id: int, min_time_seconds: float,
    gender: str, category: str = "OPEN", pool_length: Optional[int] = None,
    db: Session = Depends(get_db),
):
    qt = QualifyingTime(competition_id=competition_id, event_type_id=event_type_id,
                         gender=gender, category=category, min_time_seconds=min_time_seconds, pool_length=pool_length)
    db.add(qt)
    db.commit()
    db.refresh(qt)
    return qt

@router.patch("/{competition_id}")
def update_competition(competition_id: int, payload: CompetitionUpdate, db: Session = Depends(get_db)):
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competencia no encontrada")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(competition, field, value)

    db.add(competition)
    db.commit()
    db.refresh(competition)
    return competition

@router.patch("/{competition_id}/qualifying-times/{qualifying_time_id}")
def update_qualifying_time(
    competition_id: int,
    qualifying_time_id: int,
    payload: QualifyingTimeUpdate,
    db: Session = Depends(get_db),
):
    qt = db.query(QualifyingTime).filter(
        QualifyingTime.id == qualifying_time_id,
        QualifyingTime.competition_id == competition_id,
    ).first()
    if not qt:
        raise HTTPException(status_code=404, detail="Marca no encontrada")

    if payload.min_time_seconds is not None:
        qt.min_time_seconds = payload.min_time_seconds
    if payload.gender is not None:
        qt.gender = payload.gender
    if payload.category is not None:
        qt.category = payload.category
    if payload.event_type_id is not None:
        qt.event_type_id = payload.event_type_id

    db.add(qt)
    db.commit()
    db.refresh(qt)
    return qt


@router.delete("/{competition_id}/qualifying-times/{qualifying_time_id}", status_code=204)
def delete_qualifying_time(competition_id: int, qualifying_time_id: int, db: Session = Depends(get_db)):
    qt = db.query(QualifyingTime).filter(
        QualifyingTime.id == qualifying_time_id,
        QualifyingTime.competition_id == competition_id,
    ).first()
    if not qt:
        raise HTTPException(status_code=404, detail="Marca no encontrada")

    db.delete(qt)
    db.commit()
    return None