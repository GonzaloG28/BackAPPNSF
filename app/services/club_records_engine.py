# app/services/club_records_engine.py
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.club_record import ClubRecord
from app.models.time_record import TimeRecord
from app.models.swimmer import Swimmer, SwimmerGender, CATEGORY_RULES
from app.services.standard_events import ensure_standard_events

ALL_CATEGORIES = [label for label, _ in CATEGORY_RULES]
ALL_GENDERS = [SwimmerGender.MALE, SwimmerGender.FEMALE]
ALL_POOL_LENGTHS = [25, 50]

# Categoria comodin para el record "general" (absoluto, sin distincion de
# categoria) — mismo patron que el "OPEN" ya usado en QualifyingTime/convocatoria_engine.
GENERAL_CATEGORY = "OPEN"


def _slot_query(db: Session, event_type_id: int, category: str, gender: SwimmerGender, pool_length: int):
    return db.query(ClubRecord).filter(
        ClubRecord.event_type_id == event_type_id,
        ClubRecord.category == category,
        ClubRecord.gender == gender,
        ClubRecord.pool_length == pool_length,
    )


def _upsert_best(
    db: Session, event_type_id: int, category: str, gender: SwimmerGender, pool_length: int, time_record: TimeRecord
) -> ClubRecord:
    existing = _slot_query(db, event_type_id, category, gender, pool_length).first()

    if existing and float(existing.time_seconds) <= float(time_record.time_seconds):
        return existing  # el vigente ya es igual o mejor, no hay novedad

    if existing:
        existing.time_seconds = time_record.time_seconds
        existing.swimmer_id = time_record.swimmer_id
        existing.time_record_id = time_record.id
        existing.achieved_date = time_record.recorded_date
        db.add(existing)
    else:
        existing = ClubRecord(
            event_type_id=event_type_id, category=category, gender=gender, pool_length=pool_length,
            time_seconds=time_record.time_seconds, swimmer_id=time_record.swimmer_id,
            time_record_id=time_record.id, achieved_date=time_record.recorded_date,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


def check_and_update_club_record(db: Session, time_record: TimeRecord) -> ClubRecord | None:
    """
    Camino rápido para la creación de un tiempo nuevo: compara solo contra
    el récord vigente cacheado en cada slot afectado, sin recalcular MIN()
    sobre toda la tabla. Actualiza SIEMPRE el slot general (GENERAL_CATEGORY,
    genero, pool_length — récord absoluto sin distinción de categoría) y,
    si el nadador tiene categoría asignada, también el slot de su categoría
    real. Si no tiene género o el tiempo no tiene pool_length, no hay slot
    posible y no hace nada (misma limitación que ya asume QualifyingTime).
    """
    swimmer = time_record.swimmer
    if swimmer is None or not swimmer.gender or not time_record.pool_length:
        return None

    general_result = _upsert_best(db, time_record.event_type_id, GENERAL_CATEGORY, swimmer.gender, time_record.pool_length, time_record)

    if not swimmer.category:
        return general_result

    return _upsert_best(db, time_record.event_type_id, swimmer.category, swimmer.gender, time_record.pool_length, time_record)


def resync_club_record_slot(
    db: Session, event_type_id: int, category: str, gender: SwimmerGender, pool_length: int
) -> ClubRecord | None:
    """
    Recalculo de verificacion/fallback para UN slot puntual: se usa en los
    caminos de edicion/borrado de TimeRecord (mas raros que la creacion),
    donde no alcanza con comparar contra el valor cacheado porque el propio
    registro editado/borrado pudo ser el que sostenia el record. Si category
    es GENERAL_CATEGORY, el mejor tiempo se busca entre TODAS las categorías
    (solo filtra por género + pool_length).
    """
    query = db.query(TimeRecord).join(Swimmer, TimeRecord.swimmer_id == Swimmer.id).filter(
        TimeRecord.event_type_id == event_type_id,
        Swimmer.gender == gender,
        TimeRecord.pool_length == pool_length,
    )
    if category != GENERAL_CATEGORY:
        query = query.filter(Swimmer.category == category)
    best = query.order_by(TimeRecord.time_seconds.asc()).first()

    existing = _slot_query(db, event_type_id, category, gender, pool_length).first()

    if not best:
        if existing:
            db.delete(existing)
            db.commit()
        return None

    if existing:
        existing.time_seconds = best.time_seconds
        existing.swimmer_id = best.swimmer_id
        existing.time_record_id = best.id
        existing.achieved_date = best.recorded_date
    else:
        existing = ClubRecord(
            event_type_id=event_type_id, category=category, gender=gender, pool_length=pool_length,
            time_seconds=best.time_seconds, swimmer_id=best.swimmer_id, time_record_id=best.id,
            achieved_date=best.recorded_date,
        )
    db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


def resync_slots_for_change(db: Session, event_type_id: int, swimmer: Swimmer, pool_length: int | None) -> None:
    """Resincroniza el slot general y (si el nadador tiene categoría) el de
    su categoría real, para un evento+pool_length puntual. Se usa tras
    editar/borrar un TimeRecord — cubre ambos slots que ese registro pudo
    haber sostenido."""
    if not swimmer.gender or pool_length is None:
        return
    resync_club_record_slot(db, event_type_id, GENERAL_CATEGORY, swimmer.gender, pool_length)
    if swimmer.category:
        resync_club_record_slot(db, event_type_id, swimmer.category, swimmer.gender, pool_length)


def recompute_all_club_records(db: Session) -> int:
    """
    Recalculo total bajo demanda (POST /club-records/recompute), no usado en
    el camino de lectura del panel. Dos queries DISTINCT ON traen el mejor
    tiempo por slot — una por categoría real, otra general (sin categoría) —
    y un solo reemplazo transaccional repuebla la tabla, evitando cientos de
    round-trips contra la base remota.
    """
    ensure_standard_events(db)

    per_category_rows = db.execute(text("""
        SELECT DISTINCT ON (tr.event_type_id, s.category, s.gender, tr.pool_length)
            tr.id AS time_record_id, tr.event_type_id, s.category AS category, s.gender AS gender,
            tr.pool_length AS pool_length, tr.time_seconds AS time_seconds,
            tr.swimmer_id AS swimmer_id, tr.recorded_date AS achieved_date
        FROM time_records tr
        JOIN swimmers s ON s.id = tr.swimmer_id
        WHERE s.category IS NOT NULL AND s.gender IS NOT NULL AND tr.pool_length IS NOT NULL
        ORDER BY tr.event_type_id, s.category, s.gender, tr.pool_length, tr.time_seconds ASC
    """)).fetchall()

    general_rows = db.execute(text("""
        SELECT DISTINCT ON (tr.event_type_id, s.gender, tr.pool_length)
            tr.id AS time_record_id, tr.event_type_id, s.gender AS gender,
            tr.pool_length AS pool_length, tr.time_seconds AS time_seconds,
            tr.swimmer_id AS swimmer_id, tr.recorded_date AS achieved_date
        FROM time_records tr
        JOIN swimmers s ON s.id = tr.swimmer_id
        WHERE s.gender IS NOT NULL AND tr.pool_length IS NOT NULL
        ORDER BY tr.event_type_id, s.gender, tr.pool_length, tr.time_seconds ASC
    """)).fetchall()

    db.query(ClubRecord).delete()

    for row in per_category_rows:
        db.add(ClubRecord(
            event_type_id=row.event_type_id,
            category=row.category,
            gender=SwimmerGender(row.gender),
            pool_length=row.pool_length,
            time_seconds=row.time_seconds,
            swimmer_id=row.swimmer_id,
            time_record_id=row.time_record_id,
            achieved_date=row.achieved_date,
        ))
    for row in general_rows:
        db.add(ClubRecord(
            event_type_id=row.event_type_id,
            category=GENERAL_CATEGORY,
            gender=SwimmerGender(row.gender),
            pool_length=row.pool_length,
            time_seconds=row.time_seconds,
            swimmer_id=row.swimmer_id,
            time_record_id=row.time_record_id,
            achieved_date=row.achieved_date,
        ))

    db.commit()
    return len(per_category_rows) + len(general_rows)


def build_club_records_matrix(
    db: Session,
    category: str | None = None,
    gender: SwimmerGender | None = None,
    event_type_id: int | None = None,
) -> list[dict]:
    """Lectura directa del panel de Mejores Marcas: cubre la matriz completa
    (evento x categoria x genero x piscina) aunque falten records, left-join
    contra la tabla ya materializada (sin agregacion en caliente). `category`
    puede ser GENERAL_CATEGORY ("OPEN") para el récord absoluto sin categoría."""
    events = ensure_standard_events(db)
    if event_type_id is not None:
        events = [et for et in events if et.id == event_type_id]
    categories = [category] if category else ALL_CATEGORIES
    genders = [gender] if gender else ALL_GENDERS

    existing_rows = db.query(ClubRecord).all()
    by_slot = {(r.event_type_id, r.category, r.gender, r.pool_length): r for r in existing_rows}

    matrix = []
    for et in events:
        for cat in categories:
            for gen in genders:
                for pool_length in ALL_POOL_LENGTHS:
                    row = by_slot.get((et.id, cat, gen, pool_length))
                    matrix.append({
                        "event_type_id": et.id,
                        "event_name": et.name,
                        "distance_m": et.distance_m,
                        "stroke": et.stroke.value,
                        "category": cat,
                        "gender": gen.value,
                        "pool_length": pool_length,
                        "time_seconds": float(row.time_seconds) if row else None,
                        "swimmer_id": row.swimmer_id if row else None,
                        "swimmer_name": row.swimmer.full_name if row else None,
                        "achieved_date": row.achieved_date.isoformat() if row else None,
                    })
    return matrix
