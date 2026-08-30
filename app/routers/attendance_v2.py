# app/routers/attendance_v2.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional

from fastapi import Query
from datetime import datetime as dt

from app.core.deps import get_db, get_current_user
from app.models.swimmer import Swimmer, SwimmerStatus
from app.models.personal_schedule import PersonalSchedule
from app.models.attendance_log import AttendanceLog

router = APIRouter(prefix="/attendance-v2", tags=["attendance"], dependencies=[Depends(get_current_user)])


@router.get("/today")
def get_today_checklist(shift: Optional[str] = None, profile: Optional[str] = None, db: Session = Depends(get_db)):
    today = date.today()
    weekday = today.weekday()

    query = db.query(Swimmer).filter(Swimmer.status == SwimmerStatus.ACTIVE)
    if profile:
        query = query.filter(Swimmer.profile == profile)
    if shift:
        # AM_PM siempre aparece en ambos filtros
        query = query.filter((Swimmer.schedule_shift == shift) | (Swimmer.schedule_shift == "AM_PM"))

    swimmers = query.order_by(Swimmer.last_name_1).all()
    existing = {l.swimmer_id: l.complied for l in db.query(AttendanceLog).filter(AttendanceLog.date == today).all()}
    schedules = {s.swimmer_id: s.shift.value for s in db.query(PersonalSchedule).filter(PersonalSchedule.weekday == weekday).all()}

    result = []
    for s in swimmers:
        expected_shift = schedules.get(s.id, "NONE")
        if expected_shift == "NONE":
            continue
        result.append({
            "swimmer_id": s.id, "name": s.full_name,
            "expected_shift": expected_shift, "complied": existing.get(s.id),
        })
    return result


@router.post("")
def register_daily_attendance(payload: dict, db: Session = Depends(get_db)):
    date_param = payload.get("date")
    target_date = dt.strptime(date_param, "%Y-%m-%d").date() if date_param else date.today()

    records = payload.get("records", [])
    saved = 0

    for r in records:
        swimmer_id = r["swimmer_id"]
        complied = bool(r["complied"])

        existing = db.query(AttendanceLog).filter(
            AttendanceLog.swimmer_id == swimmer_id, AttendanceLog.date == target_date
        ).first()

        if existing:
            existing.complied = complied
        else:
            db.add(AttendanceLog(swimmer_id=swimmer_id, date=target_date, complied=complied))
        saved += 1

    db.commit()
    return {"saved": saved}


@router.get("/summary")
def get_general_summary(days: int = 6, db: Session = Depends(get_db)):
    today = date.today()
    result = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        logs = db.query(AttendanceLog).filter(AttendanceLog.date == d).all()
        complied_count = sum(1 for l in logs if l.complied)
        result.append({"date": d.isoformat(), "count": complied_count})
    return result


@router.get("/{swimmer_id}/history")
def get_swimmer_attendance_history(swimmer_id: int, db: Session = Depends(get_db)):
    logs = db.query(AttendanceLog).filter(
        AttendanceLog.swimmer_id == swimmer_id
    ).order_by(AttendanceLog.date.desc()).all()

    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    week_logs = [l for l in logs if l.date >= week_ago]
    month_logs = [l for l in logs if l.date >= month_ago]

    def rate(items):
        return round(sum(1 for l in items if l.complied) / len(items) * 100, 1) if items else 0

    return {
        "logs": [{"date": l.date.isoformat(), "complied": l.complied} for l in logs],
        "weekly_rate": rate(week_logs),
        "weekly_complied": sum(1 for l in week_logs if l.complied),
        "weekly_total": len(week_logs),
        "monthly_rate": rate(month_logs),
        "monthly_complied": sum(1 for l in month_logs if l.complied),
        "monthly_total": len(month_logs),
    }





@router.get("/history-summary/{log_date}/detail")
def get_day_detail(log_date: str, db: Session = Depends(get_db)):
    from datetime import datetime as dt
    parsed_date = dt.strptime(log_date, "%Y-%m-%d").date()

    logs = db.query(AttendanceLog).filter(AttendanceLog.date == parsed_date).all()

    complied, not_complied = [], []
    for log in logs:
        name = log.swimmer.full_name if log.swimmer else f"Nadador #{log.swimmer_id}"
        if log.complied:
            complied.append(name)
        else:
            not_complied.append(name)

    return {"date": log_date, "complied": sorted(complied), "not_complied": sorted(not_complied)}


@router.get("/{swimmer_id}/schedule")
def get_schedule(swimmer_id: int, db: Session = Depends(get_db)):
    schedules = db.query(PersonalSchedule).filter(PersonalSchedule.swimmer_id == swimmer_id).all()
    return {s.weekday: s.shift.value for s in schedules}


@router.put("/{swimmer_id}/schedule")
def update_schedule(swimmer_id: int, payload: dict, db: Session = Depends(get_db)):
    """payload: { "0": "AM_PM", "1": "PM", ... }"""
    for weekday_str, shift in payload.items():
        weekday = int(weekday_str)
        existing = db.query(PersonalSchedule).filter(
            PersonalSchedule.swimmer_id == swimmer_id, PersonalSchedule.weekday == weekday
        ).first()
        if existing:
            existing.shift = shift
        else:
            db.add(PersonalSchedule(swimmer_id=swimmer_id, weekday=weekday, shift=shift))
    db.commit()
    return {"ok": True}



@router.get("/history-summary")
def get_history_summary(days: int = 15, db: Session = Depends(get_db)):
    """Devuelve un resumen por día: cuántos cumplieron y cuántos no, últimos N días con registros."""
    today = date.today()
    since = today - timedelta(days=days)

    logs = db.query(AttendanceLog).filter(AttendanceLog.date >= since).all()

    by_date: dict = {}
    for log in logs:
        d = log.date.isoformat()
        if d not in by_date:
            by_date[d] = {"complied": 0, "not_complied": 0}
        if log.complied:
            by_date[d]["complied"] += 1
        else:
            by_date[d]["not_complied"] += 1

    result = [
        {"date": d, "complied": v["complied"], "not_complied": v["not_complied"]}
        for d, v in by_date.items()
    ]
    result.sort(key=lambda x: x["date"], reverse=True)
    return result


@router.delete("/history-summary/{log_date}")
def delete_day_history(log_date: str, db: Session = Depends(get_db)):
    """Elimina todos los registros de asistencia de un día específico (AAAA-MM-DD)."""
    from datetime import datetime as dt
    parsed_date = dt.strptime(log_date, "%Y-%m-%d").date()
    db.query(AttendanceLog).filter(AttendanceLog.date == parsed_date).delete()
    db.commit()
    return {"ok": True}


@router.delete("/{swimmer_id}/log/{log_date}")
def delete_swimmer_log(swimmer_id: int, log_date: str, db: Session = Depends(get_db)):
    from datetime import datetime as dt
    parsed_date = dt.strptime(log_date, "%Y-%m-%d").date()
    db.query(AttendanceLog).filter(
        AttendanceLog.swimmer_id == swimmer_id,
        AttendanceLog.date == parsed_date,
    ).delete()
    db.commit()
    return {"ok": True}