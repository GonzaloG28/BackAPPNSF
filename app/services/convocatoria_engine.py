# app/services/convocatoria_engine.py
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.swimmer import Swimmer, SwimmerStatus
from app.models.qualifying_time import QualifyingTime
from app.models.time_record import TimeRecord
from app.models.convocatoria import Convocatoria
from app.models.convocatoria_entry import ConvocatoriaEntry
from app.services.standard_events import ensure_standard_events

VIGENCIA_DAYS = 365


def build_convocatoria_matrix(db: Session, convocatoria: Convocatoria) -> list[dict]:
    standard_events = ensure_standard_events(db)

    qualifying_times = db.query(QualifyingTime).filter(
        QualifyingTime.competition_id == convocatoria.competition_id
    ).all()
    qt_map = {}
    for qt in qualifying_times:
        qt_map[(qt.event_type_id, qt.gender, qt.category)] = qt

    all_swimmers = db.query(Swimmer).filter(Swimmer.status != SwimmerStatus.DELETED).order_by(Swimmer.last_name_1).all()
    cutoff_date = date.today() - timedelta(days=VIGENCIA_DAYS)

    existing_entries = {
        (e.swimmer_id, e.event_type_id, e.time_record_id): e
        for e in db.query(ConvocatoriaEntry).filter(ConvocatoriaEntry.convocatoria_id == convocatoria.id).all()
    }
    existing_nt = {
        (e.swimmer_id, e.event_type_id): e
        for e in db.query(ConvocatoriaEntry).filter(
            ConvocatoriaEntry.convocatoria_id == convocatoria.id,
            ConvocatoriaEntry.time_record_id.is_(None),
        ).all()
    }

    matrix = []

    for swimmer in all_swimmers:
        events_out = []

        for et in standard_events:
            qt = (
                qt_map.get((et.id, swimmer.gender, swimmer.category))
                or qt_map.get((et.id, swimmer.gender, "OPEN"))
                or qt_map.get((et.id, None, "OPEN"))
            )
            min_time = float(qt.min_time_seconds) if qt and qt.min_time_seconds else None

            all_records = db.query(TimeRecord).filter(
                TimeRecord.swimmer_id == swimmer.id,
                TimeRecord.event_type_id == et.id,
                TimeRecord.recorded_date >= cutoff_date,
            ).order_by(TimeRecord.time_seconds.asc()).all()

            if min_time is not None:
                # Hay marca mínima: solo se muestran los tiempos que la cumplen
                visible_records = [r for r in all_records if float(r.time_seconds) <= min_time]
            else:
                # Sin marca mínima configurada: se muestran TODOS los tiempos del nadador en esa prueba
                visible_records = all_records

            marks = []
            for r in visible_records:
                key = (swimmer.id, et.id, r.id)
                selected = existing_entries[key].selected if key in existing_entries else False
                marks.append({
                    "time_record_id": r.id, "time_seconds": float(r.time_seconds),
                    "date": r.recorded_date.isoformat(), "pool_length": r.pool_length,
                    "is_nt": False, "selected": selected,
                })

            # Opción NT: SIEMPRE presente, sin importar si ya hay marcas válidas
            nt_entry = existing_nt.get((swimmer.id, et.id))
            nt_selected = nt_entry.selected if nt_entry else False
            marks.append({
                "time_record_id": None, "time_seconds": None,
                "date": None, "pool_length": None,
                "is_nt": True, "selected": nt_selected,
            })

            events_out.append({
                "event_type_id": et.id,
                "event_name": et.name,
                "qualifying_time": min_time,
                "has_qualifying_time": min_time is not None,
                "marks": marks,
            })

        matrix.append({
            "swimmer_id": swimmer.id, "name": swimmer.full_name,
            "category": swimmer.category, "status": swimmer.status.value,
            "events": events_out,
        })

    return matrix


def sync_convocatoria_entries(db: Session, convocatoria: Convocatoria, matrix: list[dict]):
    existing = {
        (e.swimmer_id, e.event_type_id, e.time_record_id): e
        for e in db.query(ConvocatoriaEntry).filter(ConvocatoriaEntry.convocatoria_id == convocatoria.id).all()
    }

    for row in matrix:
        for ev in row["events"]:
            for mark in ev["marks"]:
                key = (row["swimmer_id"], ev["event_type_id"], mark["time_record_id"])
                if key in existing:
                    continue  # ya existe, no se toca (la selección la maneja PATCH /entries)
                db.add(ConvocatoriaEntry(
                    convocatoria_id=convocatoria.id, swimmer_id=row["swimmer_id"],
                    event_type_id=ev["event_type_id"], time_record_id=mark["time_record_id"],
                    best_time_seconds=mark["time_seconds"], selected=mark["selected"],
                    is_nt_inscription=mark["is_nt"],
                ))
    db.commit()