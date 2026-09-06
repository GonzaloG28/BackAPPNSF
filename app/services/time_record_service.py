# app/services/time_record_service.py
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from app.models.time_record import TimeRecord, TimeSource
from app.services.club_records_engine import check_and_update_club_record


def create_time_record(
    db: Session,
    swimmer_id: int,
    event_type_id: int,
    time_seconds: float,
    recorded_date: date,
    *,
    pool_length: Optional[int] = None,
    location_note: Optional[str] = None,
    split_increment: Optional[int] = None,
    splits: Optional[list] = None,
    source: TimeSource = TimeSource.TRAINING,
    is_official: bool = False,
    competition_id: Optional[int] = None,
) -> TimeRecord:
    """
    Unico punto de creacion de TimeRecord en el sistema. Centralizarlo aca
    (en vez de instanciar TimeRecord(...) en cada router/servicio) garantiza
    que ningun tiempo nuevo se salte el chequeo de Record del Club, sin
    depender de que cada desarrollador se acuerde de llamarlo.
    """
    record = TimeRecord(
        swimmer_id=swimmer_id,
        event_type_id=event_type_id,
        time_seconds=time_seconds,
        recorded_date=recorded_date,
        pool_length=pool_length,
        location_note=location_note,
        source=source,
        is_official=is_official,
        split_increment=split_increment,
        competition_id=competition_id,
    )
    if splits:
        record.splits = splits

    db.add(record)
    db.commit()
    db.refresh(record)

    check_and_update_club_record(db, record)
    return record
