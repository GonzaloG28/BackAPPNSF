from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.swimmer import Swimmer, SwimmerStatus
from app.models.qualifying_time import QualifyingTime
from app.models.time_record import TimeRecord
from app.models.convocatoria import Convocatoria
from app.models.convocatoria_entry import ConvocatoriaEntry
from app.services.standard_events import ensure_standard_events

VIGENCIA_DAYS = 365


def build_convocatoria_matrix(db: Session, convocatoria: Convocatoria) -> dict:
    standard_events = ensure_standard_events(db)

    qualifying_times = db.query(QualifyingTime).filter(
        QualifyingTime.competition_id == convocatoria.competition_id
    ).all()
    # min_time por (event_type_id, gender, category) para lookup rápido
    qt_map = {}
    for qt in qualifying_times:
        qt_map[(qt.event_type_id, qt.gender, qt.category)] = qt

    all_swimmers = db.query(Swimmer).filter(Swimmer.status != SwimmerStatus.DELETED).order_by(Swimmer.last_name_1).all()
    cutoff_date = date.today() - timedelta(days=VIGENCIA_DAYS)

    existing_entries = {
        (e.swimmer_id, e.event_type_id): e
        for e in db.query(ConvocatoriaEntry).filter(ConvocatoriaEntry.convocatoria_id == convocatoria.id).all()
    }

    with_marks, without_marks = [], []

    for swimmer in all_swimmers:
        events_out = []
        swimmer_has_any_mark = False

        for et in standard_events:
            best = db.query(TimeRecord).filter(
                TimeRecord.swimmer_id == swimmer.id,
                TimeRecord.event_type_id == et.id,
                TimeRecord.recorded_date >= cutoff_date,
            ).order_by(TimeRecord.time_seconds.asc()).first()

            qt = qt_map.get((et.id, swimmer.gender, swimmer.category)) or qt_map.get((et.id, swimmer.gender, "OPEN")) or qt_map.get((et.id, None, "OPEN"))
            min_time = float(qt.min_time_seconds) if qt and qt.min_time_seconds else None

            has_time = best is not None
            qualifies = has_time and (min_time is None or float(best.time_seconds) <= min_time)

            key = (swimmer.id, et.id)
            existing = existing_entries.get(key)
            selected = existing.selected if existing else False

            events_out.append({
                "event_type_id": et.id,
                "event_name": et.name,
                "best_time": float(best.time_seconds) if has_time else None,
                "is_nt": not has_time,
                "qualifying_time": min_time,
                "qualifies": qualifies if has_time else None,  # None = NT, no aplica cumple/no cumple
                "selected": selected,
                "time_record_id": best.id if has_time else None,
            })

            if has_time:
                swimmer_has_any_mark = True

        row = {
            "swimmer_id": swimmer.id, "name": swimmer.full_name,
            "category": swimmer.category, "status": swimmer.status.value,
            "events": events_out,
        }

        if swimmer_has_any_mark:
            with_marks.append(row)
        else:
            without_marks.append(row)

    return {"with_marks": with_marks, "without_marks": without_marks}


def sync_convocatoria_entries(db: Session, convocatoria: Convocatoria, matrix: dict):
    existing = {
        (e.swimmer_id, e.event_type_id): e
        for e in db.query(ConvocatoriaEntry).filter(ConvocatoriaEntry.convocatoria_id == convocatoria.id).all()
    }
    all_rows = matrix["with_marks"] + matrix["without_marks"]

    for row in all_rows:
        for ev in row["events"]:
            key = (row["swimmer_id"], ev["event_type_id"])
            if key in existing:
                existing[key].best_time_seconds = ev["best_time"]
                existing[key].time_record_id = ev["time_record_id"]
                db.add(existing[key])
            else:
                db.add(ConvocatoriaEntry(
                    convocatoria_id=convocatoria.id, swimmer_id=row["swimmer_id"],
                    event_type_id=ev["event_type_id"], time_record_id=ev["time_record_id"],
                    best_time_seconds=ev["best_time"], selected=ev["selected"],
                ))
    db.commit()