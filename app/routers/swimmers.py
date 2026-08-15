# app/routers/swimmers.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from io import BytesIO


from app.core.deps import get_db, get_current_user
from app.models.swimmer import Swimmer, SwimmerStatus
from app.models.time_record import TimeRecord, TimeSource
from app.schemas.time_record import TimeRecordUpdate
from app.models.swimmer_metric import SwimmerMetric
from app.models.convocatoria_entry import ConvocatoriaEntry
from app.schemas.swimmer import SwimmerCreate, SwimmerUpdate, SwimmerStatusUpdate, SwimmerOut
from app.models.gym_record import GymRecord
from app.utils.rut_validator import validate_rut, normalize_rut

router = APIRouter(prefix="/swimmers", tags=["swimmers"], dependencies=[Depends(get_current_user)])


# app/routers/swimmers.py
@router.get("", response_model=list[SwimmerOut])
def list_swimmers(
    status: Optional[str] = Query(None),
    category: Optional[str] = None,
    profile: Optional[str] = None,
    is_federated: Optional[bool] = None,
    search: Optional[str] = None,
    include_deleted: bool = Query(False),
    db: Session = Depends(get_db),
):
    query = db.query(Swimmer)
    if status:
        query = query.filter(Swimmer.status == status)
    elif not include_deleted:
        query = query.filter(Swimmer.status != SwimmerStatus.DELETED)
    if category:
        query = query.filter(Swimmer.category == category)
    if profile:
        query = query.filter(Swimmer.profile == profile)
    if is_federated is not None:
        query = query.filter(Swimmer.is_federated == is_federated)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Swimmer.first_name_1.ilike(like)) | (Swimmer.last_name_1.ilike(like)) |
            (Swimmer.first_name_2.ilike(like)) | (Swimmer.last_name_2.ilike(like))
        )
    return query.order_by(Swimmer.last_name_1).all()


@router.get("/{swimmer_id}", response_model=SwimmerOut)
def get_swimmer(swimmer_id: int, db: Session = Depends(get_db)):
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Nadador no encontrado")
    return swimmer


@router.post("", response_model=SwimmerOut, status_code=201)
def create_swimmer(payload: SwimmerCreate, db: Session = Depends(get_db)):
    if payload.document_id and not validate_rut(payload.document_id):
        raise HTTPException(status_code=400, detail="RUT inválido")

    data = payload.model_dump()
    if data.get("document_id"):
        data["document_id"] = normalize_rut(data["document_id"])

        existing = db.query(Swimmer).filter(Swimmer.document_id == data["document_id"]).first()
        if existing:
            if existing.status == SwimmerStatus.DELETED:
                raise HTTPException(
                    status_code=409,
                    detail=f"Este RUT pertenece a un nadador eliminado ({existing.first_name_1} {existing.last_name_1}).",
                )
            raise HTTPException(status_code=400, detail="Este RUT ya existe en el sistema")

    swimmer = Swimmer(**data, status=SwimmerStatus.ACTIVE)
    if swimmer.birth_date:
        swimmer.category = swimmer.compute_category()

    db.add(swimmer)
    db.commit()
    db.refresh(swimmer)
    return swimmer


@router.patch("/{swimmer_id}", response_model=SwimmerOut)
def update_swimmer(swimmer_id: int, payload: SwimmerUpdate, db: Session = Depends(get_db)):
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Nadador no encontrado")

    data = payload.model_dump(exclude_unset=True)

    if "document_id" in data and data["document_id"]:
        if not validate_rut(data["document_id"]):
            raise HTTPException(status_code=400, detail="RUT inválido")
        data["document_id"] = normalize_rut(data["document_id"])

        other = db.query(Swimmer).filter(
            Swimmer.document_id == data["document_id"],
            Swimmer.id != swimmer_id,
        ).first()
        if other:
            detail = (
                f"Este RUT pertenece a un nadador eliminado ({other.first_name_1} {other.last_name_1})."
                if other.status == SwimmerStatus.DELETED
                else "Este RUT ya existe en el sistema"
            )
            raise HTTPException(status_code=409 if other.status == SwimmerStatus.DELETED else 400, detail=detail)

    for field, value in data.items():
        setattr(swimmer, field, value)

    if "birth_date" in data:
        swimmer.category = swimmer.compute_category()

    db.add(swimmer)
    db.commit()
    db.refresh(swimmer)
    return swimmer


@router.patch("/{swimmer_id}/status", response_model=SwimmerOut)
def update_swimmer_status(swimmer_id: int, payload: SwimmerStatusUpdate, db: Session = Depends(get_db)):
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Nadador no encontrado")

    swimmer.status = payload.status
    swimmer.status_reason = payload.reason
    swimmer.status_updated_at = datetime.now()

    db.add(swimmer)
    db.commit()
    db.refresh(swimmer)
    return swimmer


@router.delete("/{swimmer_id}", status_code=204)
def hard_delete_swimmer(swimmer_id: int, db: Session = Depends(get_db)):
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Nadador no encontrado")

    try:
        # Limpia registros relacionados que NO tienen cascade definido en el modelo.
        # (metrics, time_records y attendances sí tienen cascade="all, delete-orphan"
        # en la relationship de Swimmer, así que esos se borran solos al hacer db.delete)
        db.query(GymRecord).filter(GymRecord.swimmer_id == swimmer_id).delete()
        db.query(ConvocatoriaEntry).filter(ConvocatoriaEntry.swimmer_id == swimmer_id).delete()

        db.delete(swimmer)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo eliminar: el nadador tiene registros asociados que impiden el borrado."
        )


@router.get("/{swimmer_id}/times")
def get_swimmer_times(
    swimmer_id: int,
    event_type_id: Optional[int] = None,
    sort: str = Query("date_desc"),
    db: Session = Depends(get_db),
):
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Nadador no encontrado")

    query = db.query(TimeRecord).filter(TimeRecord.swimmer_id == swimmer_id)
    if event_type_id:
        query = query.filter(TimeRecord.event_type_id == event_type_id)

    order_map = {
        "date_desc": TimeRecord.recorded_date.desc(),
        "date_asc": TimeRecord.recorded_date.asc(),
        "time_asc": TimeRecord.time_seconds.asc(),
        "time_desc": TimeRecord.time_seconds.desc(),
    }
    records = query.order_by(order_map.get(sort, TimeRecord.recorded_date.desc())).all()

    return [{
        "id": r.id, "event_type_id": r.event_type_id,
        "event_name": r.event_type.name, "time_seconds": float(r.time_seconds),
        "recorded_date": r.recorded_date, "location_note": r.location_note,
        "competition_name": r.competition.name if r.competition else None,
    } for r in records]


@router.get("/{swimmer_id}/metrics")
def get_swimmer_metrics(swimmer_id: int, db: Session = Depends(get_db)):
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Nadador no encontrado")

    return db.query(SwimmerMetric).filter(
        SwimmerMetric.swimmer_id == swimmer_id
    ).order_by(SwimmerMetric.recorded_at.desc()).all()


@router.post("/{swimmer_id}/metrics")
def add_swimmer_metric(
    swimmer_id: int,
    weight_kg: Optional[float] = None,
    height_cm: Optional[float] = None,
    wingspan_cm: Optional[float] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
):
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Nadador no encontrado")

    metric = SwimmerMetric(
        swimmer_id=swimmer_id, recorded_at=date.today(),
        weight_kg=weight_kg, height_cm=height_cm, wingspan_cm=wingspan_cm, notes=notes,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.get("/{swimmer_id}/gym")
def get_gym_records(swimmer_id: int, db: Session = Depends(get_db)):
    """Devuelve el RM más reciente por ejercicio (para la vista resumen)."""
    from sqlalchemy import func as sqlfunc
    records = db.query(GymRecord).filter(GymRecord.swimmer_id == swimmer_id).order_by(GymRecord.recorded_at.desc()).all()

    latest_by_exercise = {}
    for r in records:
        if r.exercise_id not in latest_by_exercise:
            latest_by_exercise[r.exercise_id] = r

    return [
        {"exercise_id": r.exercise_id, "exercise_name": r.exercise.name, "one_rm_kg": float(r.one_rm_kg)}
        for r in latest_by_exercise.values()
    ]


@router.get("/{swimmer_id}/gym/{exercise_id}/history")
def get_gym_history(swimmer_id: int, exercise_id: int, db: Session = Depends(get_db)):
    records = db.query(GymRecord).filter(
        GymRecord.swimmer_id == swimmer_id, GymRecord.exercise_id == exercise_id
    ).order_by(GymRecord.recorded_at.desc()).all()

    return [
        {"id": r.id, "one_rm_kg": float(r.one_rm_kg), "recorded_at": r.recorded_at.isoformat()}
        for r in records
    ]


@router.post("/{swimmer_id}/gym/{exercise_id}")
def add_gym_record(swimmer_id: int, exercise_id: int, one_rm_kg: float, db: Session = Depends(get_db)):
    """Agrega un registro NUEVO al historial (no sobreescribe)."""
    record = GymRecord(swimmer_id=swimmer_id, exercise_id=exercise_id, one_rm_kg=one_rm_kg)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{swimmer_id}/gym/record/{record_id}", status_code=204)
def delete_gym_record(swimmer_id: int, record_id: int, db: Session = Depends(get_db)):
    db.query(GymRecord).filter(
        GymRecord.id == record_id, GymRecord.swimmer_id == swimmer_id
    ).delete()
    db.commit()

@router.delete("/{swimmer_id}/gym/{exercise_id}", status_code=204)
def delete_swimmer_gym_history(swimmer_id: int, exercise_id: int, db: Session = Depends(get_db)):
    """Elimina TODO el historial de este nadador para este ejercicio (no borra el ejercicio en sí)."""
    db.query(GymRecord).filter(
        GymRecord.swimmer_id == swimmer_id, GymRecord.exercise_id == exercise_id
    ).delete()
    db.commit()


@router.get("/export/clean")
def export_clean_roster(db: Session = Depends(get_db)):
    swimmers = db.query(Swimmer).filter(Swimmer.status != SwimmerStatus.DELETED).all()

    wb = Workbook()
    ws = wb.active
    headers = ["Nombres", "Apellidos", "RUT", "Fecha de Nacimiento", "Teléfono", "Correo", "Institución", "Estado"]
    ws.append(headers)

    for s in swimmers:
        ws.append([
            f"{s.first_name_1} {s.first_name_2 or ''}".strip(),
            f"{s.last_name_1} {s.last_name_2 or ''}".strip(),
            s.document_id or "", s.birth_date.strftime("%d/%m/%Y") if s.birth_date else "",
            s.phone or "", s.email or "", s.institution or "",
            "Activo" if s.status.value == "ACTIVE" else "Congelado",
        ])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="nadadores.xlsx"'})


@router.patch("/{swimmer_id}/times/{time_id}")
def update_time_record(swimmer_id: int, time_id: int, payload: TimeRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(TimeRecord).filter(
        TimeRecord.id == time_id, TimeRecord.swimmer_id == swimmer_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(record, field, value)

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/{swimmer_id}/times")
def create_time_record(swimmer_id: int, event_type_id: int, time_seconds: float, recorded_date: date, location_note: Optional[str] = None, db: Session = Depends(get_db)):
    record = TimeRecord(
        swimmer_id=swimmer_id, event_type_id=event_type_id, time_seconds=time_seconds,
        recorded_date=recorded_date, location_note=location_note, source="MANUAL" if hasattr(TimeSource, "MANUAL") else "TRAINING",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{swimmer_id}/times/grouped")
def get_times_grouped(swimmer_id: int, db: Session = Depends(get_db)):
    """Nivel 1: solo los nombres de pruebas que el nadador tiene registradas."""
    records = db.query(TimeRecord).filter(TimeRecord.swimmer_id == swimmer_id).all()
    seen = {}
    for r in records:
        seen[r.event_type_id] = r.event_type.name
    return [{"event_type_id": k, "event_name": v} for k, v in seen.items()]

@router.delete("/{swimmer_id}/times/{time_id}", status_code=204)
def delete_time_record(swimmer_id: int, time_id: int, db: Session = Depends(get_db)):
    record = db.query(TimeRecord).filter(
        TimeRecord.id == time_id, TimeRecord.swimmer_id == swimmer_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db.delete(record)
    db.commit()

@router.delete("/{swimmer_id}/times/event/{event_type_id}", status_code=204)
def delete_all_times_for_event(swimmer_id: int, event_type_id: int, db: Session = Depends(get_db)):
    db.query(TimeRecord).filter(
        TimeRecord.swimmer_id == swimmer_id,
        TimeRecord.event_type_id == event_type_id,
    ).delete()
    db.commit()
