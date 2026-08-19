# app/services/import_service.py
from sqlalchemy.orm import Session
from app.models.swimmer import Swimmer, SwimmerStatus
from app.services.matching_service import find_swimmer_match


def update_swimmer_from_row(db: Session, swimmer: Swimmer, row: dict):
    if row.get("first_name"):
        swimmer.first_name_1 = row["first_name"]
    if row.get("last_name"):
        swimmer.last_name_1 = row["last_name"]
    if row.get("birth_date"):
        swimmer.birth_date = row["birth_date"]
    if row.get("document_id"):
        swimmer.document_id = row["document_id"]

    if swimmer.birth_date:
        swimmer.category = swimmer.compute_category()

    db.add(swimmer)
    db.commit()
    db.refresh(swimmer)
    return swimmer


def create_swimmer_from_row(db, row: dict):
    new_swimmer = Swimmer(
        first_name_1=row.get("first_name") or "Sin nombre",
        last_name_1=row.get("last_name") or "Sin apellido",
        first_name_2=row.get("first_name_2"),
        last_name_2=row.get("last_name_2"),
        birth_date=row.get("birth_date"),
        document_id=row.get("document_id"),
        gender=row.get("gender"),
        comuna=row.get("comuna"),
        institution=row.get("institution"),
        phone=row.get("phone"),
        email=row.get("email"),
        status=SwimmerStatus.ACTIVE,
    )
    if new_swimmer.birth_date:
        new_swimmer.category = new_swimmer.compute_category()

    db.add(new_swimmer)
    db.commit()
    db.refresh(new_swimmer)
    return new_swimmer


def process_roster_import(db: Session, rows: list[dict], import_log_id: int):
    matched, unmatched = 0, []
    created = 0
    swimmer_ids = []

    for idx, row in enumerate(rows):
        result = find_swimmer_match(db, row)

        if result.method in ("document_id", "fuzzy+dob", "fuzzy_name"):
            update_swimmer_from_row(db, result.swimmer, row)
            matched += 1
            swimmer_ids.append(result.swimmer.id)
        elif result.method == "ambiguous":
            unmatched.append({
                "row": idx, "raw_data": row, "reason": "ambiguous_match",
                "candidates": [c.id for c in result.candidates]
            })
            swimmer_ids.append(None)
        else:
            new_swimmer = create_swimmer_from_row(db, row)
            created += 1
            swimmer_ids.append(new_swimmer.id)

    return matched, created, unmatched, swimmer_ids


def register_time_record(db: Session, swimmer_id: int, distance_m: int, stroke, seconds: float):
    from app.models.event_type import EventType, StrokeType
    from app.models.time_record import TimeRecord, TimeSource
    from datetime import date

    event_type = db.query(EventType).filter(
        EventType.distance_m == distance_m, EventType.stroke == stroke
    ).first()

    if not event_type:
        stroke_name = {
            StrokeType.FREE: "Libre", StrokeType.BACK: "Espalda", StrokeType.BREAST: "Pecho",
            StrokeType.FLY: "Mariposa", StrokeType.MEDLEY: "Combinado",
        }[stroke]
        event_type = EventType(name=f"{distance_m}m {stroke_name}", distance_m=distance_m, stroke=stroke)
        db.add(event_type)
        db.commit()
        db.refresh(event_type)

    time_record = TimeRecord(
        swimmer_id=swimmer_id, event_type_id=event_type.id, time_seconds=seconds,
        recorded_date=date.today(), source=TimeSource.IMPORT, is_official=False,
    )
    db.add(time_record)
    db.commit()
    return time_record


def upsert_swimmer_fill_missing(db, swimmer, row: dict) -> bool:
    changed = False
    field_map = {
        "first_name": "first_name_1", "last_name": "last_name_1",
        "first_name_2": "first_name_2", "last_name_2": "last_name_2",
        "document_id": "document_id", "birth_date": "birth_date",
        "gender": "gender", "comuna": "comuna", "institution": "institution",
        "phone": "phone", "email": "email",
    }
    for row_key, model_field in field_map.items():
        current = getattr(swimmer, model_field, None)
        new_value = row.get(row_key)
        is_empty = current is None or (isinstance(current, str) and current.strip() == "") or current in ("Sin nombre", "Sin apellido")
        if is_empty and new_value:
            setattr(swimmer, model_field, new_value)
            changed = True

    if changed:
        db.add(swimmer)
        db.commit()
        db.refresh(swimmer)
    return changed

def process_roster_import_upsert(db, rows: list[dict], import_log_id):
    """
    Igual que process_roster_import, pero: si el nadador ya existe y tiene TODOS
    los campos de la fila llenos, se omite (no se toca). Si le faltan datos,
    se rellenan sin sobreescribir lo existente.
    """
    matched, created, filled = 0, 0, 0
    unmatched = []
    swimmer_ids = []

    for idx, row in enumerate(rows):
        result = find_swimmer_match(db, row)  # ya usa RUT + nombre con fuzzy matching (Fase 1)

        if result.method in ("document_id", "fuzzy+dob", "fuzzy_name"):
            changed = upsert_swimmer_fill_missing(db, result.swimmer, row)
            matched += 1
            if changed:
                filled += 1
            swimmer_ids.append(result.swimmer.id)

        elif result.method == "ambiguous":
            unmatched.append({
                "row": idx, "raw_data": row, "reason": "ambiguous_match",
                "candidates": [c.id for c in result.candidates]
            })
            swimmer_ids.append(None)

        else:
            from app.services.import_service import create_swimmer_from_row
            new_swimmer = create_swimmer_from_row(db, row)
            created += 1
            swimmer_ids.append(new_swimmer.id)

    return matched, created, unmatched, swimmer_ids