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

    no_minimums = len(qualifying_times) == 0  # "Continuar sin marcas mínimas"

    all_swimmers = db.query(Swimmer).filter(Swimmer.status != SwimmerStatus.DELETED).order_by(Swimmer.last_name_1).all()
    cutoff_date = date.today() - timedelta(days=VIGENCIA_DAYS)

    existing_entries = {
        (e.swimmer_id, e.event_type_id, e.time_record_id): e
        for e in db.query(ConvocatoriaEntry).filter(ConvocatoriaEntry.convocatoria_id == convocatoria.id).all()
    }

    matrix = []
    for swimmer in all_swimmers:
        event_groups: dict[int, dict] = {}  # event_type_id -> { event_name, marks: [...] }
        competition = convocatoria.competition
        if competition.categories and swimmer.category not in competition.categories:
            continue
        if no_minimums:
            # Sin restricción: todo el historial vigente del nadador, agrupado por prueba
            records = db.query(TimeRecord).filter(
                TimeRecord.swimmer_id == swimmer.id, TimeRecord.recorded_date >= cutoff_date
            ).order_by(TimeRecord.time_seconds.asc()).all()
            for r in records:
                grp = event_groups.setdefault(r.event_type_id, {"event_name": r.event_type.name, "marks": []})
                key = (swimmer.id, r.event_type_id, r.id)
                selected = existing_entries[key].selected if key in existing_entries else False
                grp["marks"].append({
                    "time_record_id": r.id, "time_seconds": float(r.time_seconds),
                    "date": r.recorded_date.isoformat(), "pool_length": r.pool_length,
                    "selected": selected,
                })
        else:
            for qt in qualifying_times:
                if qt.gender and swimmer.gender != qt.gender:
                    continue
                if qt.category and qt.category != "OPEN" and swimmer.category != qt.category:
                    continue

                q = db.query(TimeRecord).filter(
                    TimeRecord.swimmer_id == swimmer.id,
                    TimeRecord.event_type_id == qt.event_type_id,
                    TimeRecord.recorded_date >= cutoff_date,
                    TimeRecord.time_seconds <= qt.min_time_seconds,  # TODAS las que cumplen, no solo la mejor
                )
                if qt.pool_length:
                    q = q.filter(TimeRecord.pool_length == qt.pool_length)
                qualifying_records = q.order_by(TimeRecord.time_seconds.asc()).all()

                has_any_record = db.query(TimeRecord).filter(
                TimeRecord.swimmer_id == swimmer.id, TimeRecord.event_type_id == qt.event_type_id
                    ).first() is not None

                if not qualifying_records or not has_any_record:
                    grp = event_groups.setdefault(qt.event_type_id, {"event_name": qt.event_type.name, "marks": [], "qualifying_time": float(qt.min_time_seconds) if qt.min_time_seconds else None})
                    key = (swimmer.id, qt.event_type_id, None)  # sin time_record_id real
                    existing_nt = existing_entries.get(key)
                    selected = existing_nt.selected if existing_nt else False
                    grp["marks"].append({
                        "time_record_id": None,
                        "time_seconds": None,
                        "is_nt": True,  # ← flag clave para el frontend
                        "date": None, "pool_length": None,
                        "selected": selected,
                    })
                    continue


                grp = event_groups.setdefault(qt.event_type_id, {"event_name": qt.event_type.name, "marks": [], "qualifying_time": float(qt.min_time_seconds)})
                for r in qualifying_records:
                    key = (swimmer.id, qt.event_type_id, r.id)
                    default_selected = r.id == qualifying_records[0].id  # preselecciona la mejor de las válidas
                    selected = existing_entries[key].selected if key in existing_entries else default_selected
                    grp["marks"].append({
                        "time_record_id": r.id, "time_seconds": float(r.time_seconds),
                        "date": r.recorded_date.isoformat(), "pool_length": r.pool_length,
                        "selected": selected,
                    })

        if event_groups:
            matrix.append({
                "swimmer_id": swimmer.id, "name": swimmer.full_name, "status": swimmer.status.value,
                "category": swimmer.category,
                "events": [{"event_type_id": eid, **data} for eid, data in event_groups.items()],
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
                    existing[key].selected = mark["selected"]
                    db.add(existing[key])
                else:
                    db.add(ConvocatoriaEntry(
                        convocatoria_id=convocatoria.id, swimmer_id=row["swimmer_id"],
                        event_type_id=ev["event_type_id"], time_record_id=mark["time_record_id"],
                        best_time_seconds=mark["time_seconds"], time_record_date=mark["date"],
                        selected=mark["selected"],
                    ))
    db.commit()