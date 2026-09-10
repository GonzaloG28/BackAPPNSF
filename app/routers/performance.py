# app/routers/performance.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.time_record import TimeRecord
from app.models.event_type import EventType
from app.models.swimmer import Swimmer, SwimmerStatus
from app.services.event_code_parser import parse_event_code, EventCodeParseError

router = APIRouter(tags=["performance"], dependencies=[Depends(get_current_user)])


@router.get("/performance/club/recent-marks")
def get_recent_marks_count(days: int = 7, db: Session = Depends(get_db)):
    """Pulso de actividad del club: cuántos tiempos se cargaron en los
    últimos N días, para el dashboard principal del profesor."""
    since = date.today() - timedelta(days=days)
    count = db.query(TimeRecord).filter(TimeRecord.recorded_date >= since).count()
    return {"count": count, "days": days}


MONTH_ABBR_ES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


def _last_n_months(n: int, today: date):
    months = []
    y, m = today.year, today.month
    for _ in range(n):
        months.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    months.reverse()
    return months


@router.get("/performance/club/progress")
def get_club_progress(months: int = 6, db: Session = Depends(get_db)):
    """Progreso de tiempos del club: para cada marca personal nueva (PB) —
    tiempo menor a la mejor marca previa del nadador en esa prueba, sin
    importar cuándo se registró esa marca previa — calcula cuánto mejoró (%)
    y la agrupa por mes, para graficar la tendencia de mejora de todo el
    plantel en el rango elegido (4/6/12 meses) en el dashboard del profesor."""
    if months not in (4, 6, 12):
        months = 6
    today = date.today()
    months_list = _last_n_months(months, today)
    window_start = date(months_list[0][0], months_list[0][1], 1)

    records = (
        db.query(TimeRecord)
        .order_by(TimeRecord.swimmer_id, TimeRecord.event_type_id, TimeRecord.recorded_date)
        .all()
    )

    buckets = {f"{y:04d}-{m:02d}": {"pb_count": 0, "improvement_sum": 0.0} for y, m in months_list}
    swimmers_improved = set()
    best_so_far: dict[tuple[int, int], float] = {}

    for r in records:
        key = (r.swimmer_id, r.event_type_id)
        t = float(r.time_seconds)
        prev_best = best_so_far.get(key)
        if prev_best is not None and t < prev_best and r.recorded_date >= window_start:
            improvement_pct = (prev_best - t) / prev_best * 100
            bucket_key = f"{r.recorded_date.year:04d}-{r.recorded_date.month:02d}"
            if bucket_key in buckets:
                buckets[bucket_key]["pb_count"] += 1
                buckets[bucket_key]["improvement_sum"] += improvement_pct
                swimmers_improved.add(r.swimmer_id)
        if prev_best is None or t < prev_best:
            best_so_far[key] = t

    series = []
    total_pb = 0
    total_improvement = 0.0
    for y, m in months_list:
        bucket_key = f"{y:04d}-{m:02d}"
        b = buckets[bucket_key]
        avg = round(b["improvement_sum"] / b["pb_count"], 1) if b["pb_count"] > 0 else 0.0
        series.append({"period": bucket_key, "label": MONTH_ABBR_ES[m - 1], "avg_improvement_pct": avg, "pb_count": b["pb_count"]})
        total_pb += b["pb_count"]
        total_improvement += b["improvement_sum"]

    swimmers_total = db.query(Swimmer).filter(Swimmer.status != SwimmerStatus.DELETED).count()

    return {
        "months": months,
        "series": series,
        "summary": {
            "avg_improvement_pct": round(total_improvement / total_pb, 1) if total_pb > 0 else 0.0,
            "pb_count": total_pb,
            "swimmers_improved": len(swimmers_improved),
            "swimmers_total": swimmers_total,
        },
    }


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
        stroke_name = {
            "FREE": "Libre", "BACK": "Espalda", "BREAST": "Pecho",
            "FLY": "Mariposa", "MEDLEY": "Combinado",
        }[stroke.value]
        event_type = EventType(name=f"{distance}m {stroke_name}", distance_m=distance, stroke=stroke)
        db.add(event_type)
        db.commit()
        db.refresh(event_type)

    return {"id": event_type.id, "name": event_type.name, "distance_m": event_type.distance_m}


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
    query = db.query(TimeRecord).filter(
        TimeRecord.swimmer_id == swimmer_id, TimeRecord.event_type_id == event_type_id
    )
    if pool_length:
        query = query.filter(TimeRecord.pool_length == pool_length)
    records = query.order_by(TimeRecord.recorded_date.asc()).all()

    return [{
        "id": r.id,
        "date": r.recorded_date.isoformat(),
        "time_seconds": float(r.time_seconds),
        "pool_length": r.pool_length,
        "label": r.competition.name if r.competition else (r.location_note or "Registro"),
        "split_increment": r.split_increment,
        "splits": [
            {
                "distance_mark": s.distance_mark,
                "segment_seconds": float(s.segment_seconds),
                "cumulative_seconds": float(s.cumulative_seconds),
            }
            for s in r.splits
        ],
    } for r in records]