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
 
 
def build_convocatoria_matrix(db: Session, convocatoria: Convocatoria) -> list:
    """
    Devuelve TODOS los nadadores activos, con una entrada por cada prueba
    estándar. Cada entrada tiene un `status`:
 
    - "NT"     → el nadador nunca ha registrado un tiempo en esa prueba.
    - "NO_MM"  → tiene tiempos registrados, pero ninguno cumple la marca
                 mínima (Marca Mínima) configurada para esta competencia.
    - "OK"     → tiene al menos un tiempo igual o menor a la marca mínima.
                 `marks` trae TODAS esas marcas válidas (no solo la mejor),
                 ordenadas de más rápida a más lenta.
 
    Si la prueba no tiene marca mínima configurada, cualquier tiempo
    registrado cuenta como "OK" y se listan todas las marcas vigentes.
    """
    standard_events = ensure_standard_events(db)
 
    qualifying_times = db.query(QualifyingTime).filter(
        QualifyingTime.competition_id == convocatoria.competition_id
    ).all()
    qt_map = {}
    for qt in qualifying_times:
        qt_map[(qt.event_type_id, qt.gender, qt.category)] = qt
 
    all_swimmers = db.query(Swimmer).filter(
        Swimmer.status != SwimmerStatus.DELETED
    ).order_by(Swimmer.last_name_1).all()
 
    cutoff_date = date.today() - timedelta(days=VIGENCIA_DAYS)
 
    existing_entries = {
        (e.swimmer_id, e.event_type_id): e
        for e in db.query(ConvocatoriaEntry).filter(ConvocatoriaEntry.convocatoria_id == convocatoria.id).all()
    }
 
    # Traer TODOS los registros vigentes de una sola vez (no solo el mejor
    # por prueba) — se necesitan todos para poder listar todas las marcas
    # que cumplen la mínima, no solo una.
    all_records = db.query(TimeRecord).filter(TimeRecord.recorded_date >= cutoff_date).all()
    records_by_swimmer_event: dict[tuple, list] = {}
    for r in all_records:
        records_by_swimmer_event.setdefault((r.swimmer_id, r.event_type_id), []).append(r)
    for key in records_by_swimmer_event:
        records_by_swimmer_event[key].sort(key=lambda r: r.time_seconds)  # más rápida primero
 
    swimmers_out = []
 
    for swimmer in all_swimmers:
        entries_out = []
        swimmer_has_any_record = False
 
        for et in standard_events:
            records = records_by_swimmer_event.get((swimmer.id, et.id), [])
 
            qt = qt_map.get((et.id, swimmer.gender, swimmer.category)) or \
                 qt_map.get((et.id, swimmer.gender, "OPEN")) or \
                 qt_map.get((et.id, None, "OPEN"))
            min_time = float(qt.min_time_seconds) if qt and qt.min_time_seconds else None
 
            existing = existing_entries.get((swimmer.id, et.id))
            existing_selected = existing.selected if existing else False
 
            # ── Caso 1: nunca ha nadado esta prueba → NT ──────────────
            if not records:
                entries_out.append({
                    "event_type_id": et.id,
                    "event_name": et.name,
                    "status": "NT",
                    "marks": [],
                    "best_time": None,
                    "is_nt": True,
                    "meets_minimum": None,
                    "qualifying_time": min_time,
                    "qualifies": False,
                    "selected": existing_selected,
                    "time_record_id": None,
                })
                continue
 
            swimmer_has_any_record = True
 
            # ── Caso 2: hay marca mínima configurada ──────────────────
            if min_time is not None:
                qualifying_marks = [r for r in records if float(r.time_seconds) <= min_time]
 
                if not qualifying_marks:
                    # Tiene tiempos, pero ninguno cumple la mínima → NO_MM
                    entries_out.append({
                        "event_type_id": et.id,
                        "event_name": et.name,
                        "status": "NO_MM",
                        "marks": [],
                        "best_time": None,
                        "is_nt": False,
                        "meets_minimum": False,
                        "qualifying_time": min_time,
                        "qualifies": False,
                        "selected": existing_selected,
                        "time_record_id": None,
                    })
                    continue
 
                # Cumple la mínima → OK, listar TODAS las marcas válidas
                marks_out = [
                    {"time_record_id": r.id, "time_seconds": float(r.time_seconds), "date": r.recorded_date.isoformat()}
                    for r in qualifying_marks
                ]
                best = qualifying_marks[0]
                entries_out.append({
                    "event_type_id": et.id,
                    "event_name": et.name,
                    "status": "OK",
                    "marks": marks_out,
                    "best_time": float(best.time_seconds),
                    "is_nt": False,
                    "meets_minimum": True,
                    "qualifying_time": min_time,
                    "qualifies": True,
                    "selected": existing_selected,
                    "time_record_id": best.id,
                })
 
            # ── Caso 3: sin marca mínima configurada ──────────────────
            else:
                marks_out = [
                    {"time_record_id": r.id, "time_seconds": float(r.time_seconds), "date": r.recorded_date.isoformat()}
                    for r in records
                ]
                best = records[0]
                entries_out.append({
                    "event_type_id": et.id,
                    "event_name": et.name,
                    "status": "OK",
                    "marks": marks_out,
                    "best_time": float(best.time_seconds),
                    "is_nt": False,
                    "meets_minimum": None,
                    "qualifying_time": None,
                    "qualifies": True,
                    "selected": existing_selected,
                    "time_record_id": best.id,
                })
 
        swimmers_out.append({
            "swimmer_id": swimmer.id,
            "name": swimmer.full_name,
            "category": swimmer.category,
            "status": swimmer.status.value,
            "has_marks": swimmer_has_any_record,
            "events": entries_out,
        })
 
    return swimmers_out
 
 
def sync_convocatoria_entries(db: Session, convocatoria: Convocatoria, matrix_swimmers: list):
    existing = {
        (e.swimmer_id, e.event_type_id): e
        for e in db.query(ConvocatoriaEntry).filter(ConvocatoriaEntry.convocatoria_id == convocatoria.id).all()
    }
 
    for row in matrix_swimmers:
        for ev in row["events"]:
            key = (row["swimmer_id"], ev["event_type_id"])
            if key in existing:
                existing[key].best_time_seconds = ev["best_time"]
                existing[key].time_record_id = ev["time_record_id"]
                existing[key].is_nt_inscription = (ev["status"] == "NT")
                db.add(existing[key])
            else:
                db.add(ConvocatoriaEntry(
                    convocatoria_id=convocatoria.id,
                    swimmer_id=row["swimmer_id"],
                    event_type_id=ev["event_type_id"],
                    time_record_id=ev["time_record_id"],
                    best_time_seconds=ev["best_time"],
                    selected=ev["selected"],
                    is_nt_inscription=(ev["status"] == "NT"),
                ))
    db.commit()
 