# app/routers/calendar.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from datetime import date

from app.core.deps import get_db, get_current_user
from app.models.custom_group import CustomGroup
from app.models.training_sessions import TrainingSessions
from app.models.competition import Competition
from app.models.convocatoria import Convocatoria, ConvocatoriaStatus
from app.models.convocatoria_entry import ConvocatoriaEntry
from app.schemas.calendar import CustomGroupCreate, TrainingSessionCreate, TrainingSessionUpdate
from app.services.holidays_cl import get_holidays_for_year
from app.models.day_note import DayNote

router = APIRouter(prefix="/calendar", tags=["calendar"], dependencies=[Depends(get_current_user)])


# ── Feriados ──────────────────────────────────────────
@router.get("/holidays/{year}")
def holidays(year: int):
    return get_holidays_for_year(year)


# ── Grupos personalizados ─────────────────────────────
@router.get("/groups")
def list_groups(db: Session = Depends(get_db)):
    return db.query(CustomGroup).all()

@router.post("/groups", status_code=201)
def create_group(payload: CustomGroupCreate, db: Session = Depends(get_db)):
    group = CustomGroup(**payload.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group

@router.delete("/groups/{group_id}", status_code=204)
def delete_group(group_id: int, db: Session = Depends(get_db)):
    db.query(CustomGroup).filter(CustomGroup.id == group_id).delete()
    db.commit()


# ── Vista mensual ──────────────────────────────────────
@router.get("/month/{year}/{month}")
def get_month_data(year: int, month: int, db: Session = Depends(get_db)):
    # Competencias que se solapan con este mes
    from calendar import monthrange
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    competitions = db.query(Competition).filter(
        Competition.start_date <= last_day, Competition.end_date >= first_day
    ).all()

    # Volumen por día del mes
    sessions = db.query(TrainingSessions).filter(
        extract('year', TrainingSessions.date) == year,
        extract('month', TrainingSessions.date) == month,
    ).all()

    volume_by_day: dict[str, int] = {}
    for s in sessions:
        d = s.date.isoformat()
        volume_by_day[d] = volume_by_day.get(d, 0) + (s.total_volume_m or 0)

    total_month = sum(volume_by_day.values())

    return {
        "competitions": [
            {"id": c.id, "name": c.name, "start_date": c.start_date.isoformat(), "end_date": c.end_date.isoformat(), "location": c.location}
            for c in competitions
        ],
        "volume_by_day": volume_by_day,
        "total_month_volume": total_month,
        "holidays": get_holidays_for_year(year),
    }


# ── Detalle de un día ───────────────────────────────────
@router.get("/day/{iso_date}")
def get_day_detail(iso_date: str, db: Session = Depends(get_db)):
    from datetime import datetime
    target_date = datetime.strptime(iso_date, "%Y-%m-%d").date()

    # Competencia (si el día cae dentro de un rango start_date-end_date)
    competition = db.query(Competition).filter(
        Competition.start_date <= target_date, Competition.end_date >= target_date
    ).first()

    competition_data = None
    if competition:
        convocatoria = db.query(Convocatoria).filter(
            Convocatoria.competition_id == competition.id,
            Convocatoria.status.in_([ConvocatoriaStatus.CONFIRMED, ConvocatoriaStatus.EXPORTED]),
        ).first()

        swimmers_confirmed = []
        if convocatoria:
            entries = db.query(ConvocatoriaEntry).filter(
                ConvocatoriaEntry.convocatoria_id == convocatoria.id,
                ConvocatoriaEntry.selected == True,
            ).all()
            seen = {}
            for e in entries:
                seen[e.swimmer_id] = e.swimmer.full_name
            swimmers_confirmed = list(seen.values())

        competition_data = {
            "id": competition.id, "name": competition.name, "start_date": competition.start_date.isoformat(),
            "end_date": competition.end_date.isoformat(), "location": competition.location,
            "pool_length": competition.pool_length,
            "swimmers_confirmed": swimmers_confirmed,
        }

    # Sesiones de entrenamiento de ese día
    sessions = db.query(TrainingSessions).filter(TrainingSessions.date == target_date).all()

    total_volume = sum(s.total_volume_m or 0 for s in sessions)

    return {
        "date": iso_date,
        "competition": competition_data,
        "sessions": [
            {
                "id": s.id, "shift": s.shift.value, "profile": s.profile.value,
                "target_type": s.target_type.value, "target_category": s.target_category,
                "target_group_id": s.target_group_id,
                "target_group_name": s.target_group.name if s.target_group else None,
                "week_number": s.week_number, "objective": s.objective, "total_volume_m": s.total_volume_m,
                "warmup_text": s.warmup_text, "technique_text": s.technique_text,
                "work1_text": s.work1_text, "work2_text": s.work2_text, "cooldown_text": s.cooldown_text,
            } for s in sessions
        ],
        "total_volume_m": total_volume,
    }



@router.get("/day/{iso_date}/notes")
def get_day_notes(iso_date: str, db: Session = Depends(get_db)):
    from datetime import datetime
    target_date = datetime.strptime(iso_date, "%Y-%m-%d").date()
    note = db.query(DayNote).filter(DayNote.date == target_date).first()
    return {"notes": note.notes if note else ""}

@router.put("/day/{iso_date}/notes")
def save_day_notes(iso_date: str, payload: dict, db: Session = Depends(get_db)):
    from datetime import datetime
    target_date = datetime.strptime(iso_date, "%Y-%m-%d").date()
    note = db.query(DayNote).filter(DayNote.date == target_date).first()
    if note:
        note.notes = payload.get("notes", "")
    else:
        note = DayNote(date=target_date, notes=payload.get("notes", ""))
        db.add(note)
    db.commit()
    return {"ok": True}



@router.get("/today-summary")
def today_summary(db: Session = Depends(get_db)):
    from datetime import date
    today = date.today()
    sessions = db.query(TrainingSessions).filter(TrainingSessions.date == today).all()
    return {
        "date": today.isoformat(),
        "has_competitive": any(s.profile.value == "COMPETITIVE" for s in sessions),
        "has_formative": any(s.profile.value == "FORMATIVE" for s in sessions),
        "competitive_count": sum(1 for s in sessions if s.profile.value == "COMPETITIVE"),
        "formative_count": sum(1 for s in sessions if s.profile.value == "FORMATIVE"),
    }

# ── CRUD de sesiones ─────────────────────────────────────
@router.post("/sessions", status_code=201)
def create_session(payload: TrainingSessionCreate, db: Session = Depends(get_db)):
    session_obj = TrainingSessions(**payload.model_dump())
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return session_obj

@router.patch("/sessions/{session_id}")
def update_session(session_id: int, payload: TrainingSessionUpdate, db: Session = Depends(get_db)):
    session_obj = db.query(TrainingSessions).filter(TrainingSessions.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(session_obj, field, value)
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return session_obj

@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    db.query(TrainingSessions).filter(TrainingSessions.id == session_id).delete()
    db.commit()