# app/services/convocatoria_engine.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta

from app.models.swimmer import Swimmer, SwimmerStatus
from app.models.qualifying_time import QualifyingTime
from app.models.time_record import TimeRecord
from app.models.convocatoria import Convocatoria
from app.models.convocatoria_entry import ConvocatoriaEntry


VIGENCIA_DAYS = 365

def build_convocatoria_matrix(db: Session, convocatoria: Convocatoria) -> list[dict]:
    qualifying_times = db.query(QualifyingTime).filter(
        QualifyingTime.competition_id == convocatoria.competition_id
    ).all()

    all_swimmers = db.query(Swimmer).filter(Swimmer.status != SwimmerStatus.DELETED).order_by(Swimmer.last_name_1).all()

    existing_entries = {
        (e.swimmer_id, e.event_type_id): e
        for e in db.query(ConvocatoriaEntry).filter(ConvocatoriaEntry.convocatoria_id == convocatoria.id).all()
    }

    cutoff_date = date.today() - timedelta(days=VIGENCIA_DAYS)
    matrix = []

    for swimmer in all_swimmers:
        entries = []

        for qt in qualifying_times:
            if qt.gender and swimmer.gender != qt.gender:
                continue
            if qt.category and qt.category != "OPEN" and swimmer.category != qt.category:
                continue

            best = db.query(TimeRecord).filter(
                TimeRecord.swimmer_id == swimmer.id,
                TimeRecord.event_type_id == qt.event_type_id,
                TimeRecord.recorded_date >= cutoff_date,  # solo tiempos vigentes (< 1 año)
            ).order_by(TimeRecord.time_seconds.asc()).first()
                               
            qualifies = best is not None and float(best.time_seconds) <= float(qt.min_time_seconds)

            existing = existing_entries.get((swimmer.id, qt.event_type_id))
            selected = existing.selected if existing else qualifies

            entries.append({
                "event_type_id": qt.event_type_id,
                "event_name": qt.event_type.name,
                "best_time": float(best.time_seconds) if best else None,
                "best_time_date": best.recorded_date.isoformat() if best else None,
                "qualifying_time": float(qt.min_time_seconds),
                "qualifies": qualifies,
                "selected": selected,
            })

        if entries:
            matrix.append({
                "swimmer_id": swimmer.id,
                "name": swimmer.full_name,
                "status": swimmer.status.value,
                "entries": entries,
            })

    return matrix


def sync_convocatoria_entries(db: Session, convocatoria: Convocatoria, matrix: list[dict]):
    """
    Persiste la matriz calculada como ConvocatoriaEntry. Crea las que faltan,
    y ACTUALIZA el best_time_seconds/time_record_date de las que ya existían
    (antes solo se creaban una vez y quedaban con el tiempo desactualizado).
    """
    existing = {
        (e.swimmer_id, e.event_type_id): e
        for e in db.query(ConvocatoriaEntry).filter(
            ConvocatoriaEntry.convocatoria_id == convocatoria.id
        ).all()
    }

    for row in matrix:
        for entry in row["entries"]:
            key = (row["swimmer_id"], entry["event_type_id"])
            existing_entry = existing.get(key)

            if existing_entry:
                existing_entry.best_time_seconds = entry["best_time"]
                existing_entry.time_record_date = entry["best_time_date"]
                db.add(existing_entry)
            else:
                db.add(ConvocatoriaEntry(
                    convocatoria_id=convocatoria.id,
                    swimmer_id=row["swimmer_id"],
                    event_type_id=entry["event_type_id"],
                    best_time_seconds=entry["best_time"],
                    time_record_date=entry["best_time_date"],
                    selected=entry["selected"],
                ))
    db.commit()