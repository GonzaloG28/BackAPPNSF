# app/routers/swimmer_self.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_swimmer
from app.models.swimmer import Swimmer
from app.models.time_record import TimeRecord
from app.models.swimmer_metric import SwimmerMetric

router = APIRouter(prefix="/swimmer-self", tags=["swimmer-self"])


@router.get("/profile")
def get_own_profile(swimmer: Swimmer = Depends(get_current_swimmer), db: Session = Depends(get_db)):
    base = {
        "full_name": swimmer.full_name, "category": swimmer.category,
        "status": swimmer.status.value, "payment_active": swimmer.payment_active,
    }

    if not swimmer.payment_active:
        # Paywall: la estructura de la respuesta es IDÉNTICA, pero los datos numéricos van en 0
        # — así el frontend renderiza la misma UI sin ramas especiales de "no hay datos".
        return {
            **base,
            "total_times": 0,
            "best_times_by_event": [],
            "latest_metric": None,
            "attendance_rate_30d": 0,
        }

    times = db.query(TimeRecord).filter(TimeRecord.swimmer_id == swimmer.id).all()
    latest_metric = db.query(SwimmerMetric).filter(
        SwimmerMetric.swimmer_id == swimmer.id
    ).order_by(SwimmerMetric.recorded_at.desc()).first()

    return {
        **base,
        "total_times": len(times),
        "best_times_by_event": [
            {"event_name": t.event_type.name, "time_seconds": float(t.time_seconds)} for t in times[:10]
        ],
        "latest_metric": {
            "weight_kg": float(latest_metric.weight_kg) if latest_metric and latest_metric.weight_kg else None,
            "height_cm": float(latest_metric.height_cm) if latest_metric and latest_metric.height_cm else None,
        } if latest_metric else None,
        "attendance_rate_30d": 0,  # conecta aquí tu cálculo real si ya lo tienes en attendance_v2
    }