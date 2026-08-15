# app/routers/performance.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.time_record import TimeRecord
from app.models.event_type import EventType
from app.services.event_code_parser import parse_event_code, EventCodeParseError
from app.models.event_type import EventType

router = APIRouter(tags=["performance"], dependencies=[Depends(get_current_user)])


@router.post("/event-types/resolve")
def resolve_event_type(code: str, db: Session = Depends(get_db)):
    """Recibe un código como '50L' o '100P' y devuelve (o crea) el EventType correspondiente."""
    try:
        distance, stroke = parse_event_code(code)
    except EventCodeParseError:
        raise HTTPException(status_code=400, detail="Código no reconocido. Usa formato como 50L, 100P, 200E")

    event_type = db.query(EventType).filter(
        EventType.distance_m == distance, EventType.stroke == stroke
    ).first()

    if not event_type:
        stroke_name = {"FREE": "Libre", "BACK": "Espalda", "BREAST": "Pecho", "FLY": "Mariposa", "MEDLEY": "Combinado"}[stroke.value]
        event_type = EventType(name=f"{distance}m {stroke_name}", distance_m=distance, stroke=stroke)
        db.add(event_type)
        db.commit()
        db.refresh(event_type)

    return {"id": event_type.id, "name": event_type.name}

@router.get("/performance/{swimmer_id}/timeline")
def get_swimmer_timeline(swimmer_id: int, event_type_id: int = None, db: Session = Depends(get_db)):
    query = db.query(TimeRecord).filter(TimeRecord.swimmer_id == swimmer_id)
    if event_type_id:
        query = query.filter(TimeRecord.event_type_id == event_type_id)

    records = query.order_by(TimeRecord.recorded_date.asc()).all()

    return [
        {
            "date": r.recorded_date,
            "time_seconds": float(r.time_seconds),
            "event_type_id": r.event_type_id,
        }
        for r in records
    ]


@router.get("/event-types")
def list_event_types(db: Session = Depends(get_db)):
    return db.query(EventType).all()



@router.get("/swimmers/{swimmer_id}/evolution")
def get_evolution(swimmer_id: int, event_type_id: int, pool_length: Optional[int] = None, db: Session = Depends(get_db)):
    from app.models.time_record import TimeRecord
    query = db.query(TimeRecord).filter(
        TimeRecord.swimmer_id == swimmer_id, TimeRecord.event_type_id == event_type_id
    )
    if pool_length:
        query = query.filter(TimeRecord.pool_length == pool_length)
    records = query.order_by(TimeRecord.recorded_date.asc()).all()

    return [{
        "id": r.id, "date": r.recorded_date.isoformat(), "time_seconds": float(r.time_seconds),
        "pool_length": r.pool_length,
        "label": r.competition.name if r.competition else (r.location_note or "Registro"),
    } for r in records]