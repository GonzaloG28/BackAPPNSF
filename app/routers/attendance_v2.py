# app/routers/attendance_v2.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime as dt
from typing import Optional
 
from app.core.deps import get_db, get_current_user
from app.models.swimmer import Swimmer, SwimmerStatus
from app.models.personal_schedule import PersonalSchedule
from app.models.attendance_log import AttendanceLog, AttendanceShift
 
router = APIRouter(prefix="/attendance-v2", tags=["attendance"], dependencies=[Depends(get_current_user)])
 
 
def _parse_shift(value: Optional[str]) -> AttendanceShift:
    if not value:
        return AttendanceShift.AM_PM
    try:
        return AttendanceShift(value)
    except ValueError:
        return AttendanceShift.AM_PM
 
 
def _swimmer_ids_for(db: Session, profile: Optional[str], category: Optional[str]) -> Optional[set[int]]:
    """Devuelve el set de swimmer_id que matchean profile/category, o None
    si no hay ningún filtro (para no restringir la query innecesariamente)."""
    if not profile and not category:
        return None
    q = db.query(Swimmer.id)
    if profile:
        q = q.filter(Swimmer.profile == profile)
    if category:
        q = q.filter(Swimmer.category == category)
    return {row[0] for row in q.all()}
 
 
@router.get("/today")
def get_today_checklist(
    date_param: Optional[str] = Query(None, alias="date"),
    shift: Optional[str] = None,
    profile: Optional[str] = None,
    db: Session = Depends(get_db),
):
    target_date = dt.strptime(date_param, "%Y-%m-%d").date() if date_param else date.today()
    weekday = target_date.weekday()
    target_shift = _parse_shift(shift)
 
    query = db.query(Swimmer).filter(Swimmer.status == SwimmerStatus.ACTIVE)
    if profile:
        query = query.filter(Swimmer.profile == profile)
 
    swimmers = query.order_by(Swimmer.last_name_1).all()
 
    logs_query = db.query(AttendanceLog).filter(AttendanceLog.date == target_date)
    if target_shift != AttendanceShift.AM_PM:
        logs_query = logs_query.filter(AttendanceLog.shift == target_shift)
    existing = {l.swimmer_id: l.complied for l in logs_query.all()}
 
    schedules = {s.swimmer_id: s.shift.value for s in db.query(PersonalSchedule).filter(PersonalSchedule.weekday == weekday).all()}
 
    result = []
    for s in swimmers:
        expected_shift = schedules.get(s.id, "NONE")
        if expected_shift == "NONE":
            continue
        if shift and shift != "AM_PM" and expected_shift not in (shift, "AM_PM"):
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
    target_shift = _parse_shift(payload.get("shift"))
 
    records = payload.get("records", [])
    saved = 0
 
    for r in records:
        swimmer_id = r["swimmer_id"]
        complied = bool(r["complied"])
 
        existing = db.query(AttendanceLog).filter(
            AttendanceLog.swimmer_id == swimmer_id,
            AttendanceLog.date == target_date,
            AttendanceLog.shift == target_shift,
        ).first()
 
        if existing:
            existing.complied = complied
        else:
            db.add(AttendanceLog(
                swimmer_id=swimmer_id, date=target_date,
                complied=complied, shift=target_shift,
            ))
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
def get_swimmer_attendance_history(
    swimmer_id: int,
    shift: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(AttendanceLog).filter(AttendanceLog.swimmer_id == swimmer_id)
    if shift and shift != "AM_PM":
        query = query.filter(AttendanceLog.shift == _parse_shift(shift))
 
    logs = query.order_by(AttendanceLog.date.desc()).all()
 
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
 
    week_logs = [l for l in logs if l.date >= week_ago]
    month_logs = [l for l in logs if l.date >= month_ago]
 
    def rate(items):
        return round(sum(1 for l in items if l.complied) / len(items) * 100, 1) if items else 0
 
    return {
        "logs": [
            {"date": l.date.isoformat(), "complied": l.complied, "shift": l.shift.value}
            for l in logs
        ],
        "weekly_rate": rate(week_logs),
        "weekly_complied": sum(1 for l in week_logs if l.complied),
        "weekly_total": len(week_logs),
        "monthly_rate": rate(month_logs),
        "monthly_complied": sum(1 for l in month_logs if l.complied),
        "monthly_total": len(month_logs),
    }
 
 
@router.delete("/{swimmer_id}/log/{log_date}")
def delete_swimmer_log(
    swimmer_id: int,
    log_date: str,
    shift: Optional[str] = None,
    db: Session = Depends(get_db),
):
    parsed_date = dt.strptime(log_date, "%Y-%m-%d").date()
    query = db.query(AttendanceLog).filter(
        AttendanceLog.swimmer_id == swimmer_id, AttendanceLog.date == parsed_date
    )
    if shift:
        query = query.filter(AttendanceLog.shift == _parse_shift(shift))
    deleted = query.delete()
    db.commit()
    return {"deleted": deleted}
 
 
@router.get("/history-summary/{log_date}/detail")
def get_day_detail(
    log_date: str,
    shift: Optional[str] = None,
    profile: Optional[str] = None,      # NUEVO: filtrar por Formativo/Competitivo
    category: Optional[str] = None,     # NUEVO: filtrar por categoría oficial
    db: Session = Depends(get_db),
):
    parsed_date = dt.strptime(log_date, "%Y-%m-%d").date()
 
    query = db.query(AttendanceLog).filter(AttendanceLog.date == parsed_date)
    if shift and shift != "AM_PM":
        query = query.filter(AttendanceLog.shift == _parse_shift(shift))
 
    swimmer_ids = _swimmer_ids_for(db, profile, category)
    if swimmer_ids is not None:
        if not swimmer_ids:
            return {"date": log_date, "complied": [], "not_complied": []}
        query = query.filter(AttendanceLog.swimmer_id.in_(swimmer_ids))
 
    logs = query.all()
 
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
def get_history_summary(
    days: int = 15,
    shift: Optional[str] = None,
    profile: Optional[str] = None,      # NUEVO
    category: Optional[str] = None,     # NUEVO
    db: Session = Depends(get_db),
):
    """Resumen por día: cuántos cumplieron y cuántos no, filtrado por
    grupo/categoría/sesión — antes mezclaba a TODOS los nadadores del club
    sin importar qué se estaba viendo en pantalla."""
    today = date.today()
    since = today - timedelta(days=days)
 
    query = db.query(AttendanceLog).filter(AttendanceLog.date >= since)
    if shift and shift != "AM_PM":
        query = query.filter(AttendanceLog.shift == _parse_shift(shift))
 
    swimmer_ids = _swimmer_ids_for(db, profile, category)
    if swimmer_ids is not None:
        if not swimmer_ids:
            return []
        query = query.filter(AttendanceLog.swimmer_id.in_(swimmer_ids))
 
    logs = query.all()
 
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
 