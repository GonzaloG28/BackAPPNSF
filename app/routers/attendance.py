# app/routers/attendance.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date as date_type, timedelta
from typing import Optional

from app.core.deps import get_db
from app.models.swimmer import Swimmer, SwimmerStatus
from app.models.attendance import Attendance, AttendanceShift
from app.core.deps import get_current_user
from app.schemas.attendance import AttendanceBulkCreate, AttendanceOut, AttendanceSummary

router = APIRouter(prefix="/attendance", tags=["attendance"], dependencies=[Depends(get_current_user)])


@router.get("/today", response_model=list[dict])
def get_today_roster(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Swimmer).filter(Swimmer.status == SwimmerStatus.ACTIVE)
    if category:
        query = query.filter(Swimmer.category == category)

    swimmers = query.order_by(Swimmer.last_name_1).all()
    today = date_type.today()

    today_attendance = {
        a.swimmer_id: a.shift.value if hasattr(a.shift, 'value') else a.shift
        for a in db.query(Attendance).filter(Attendance.date == today).all()
    }

    return [
        {
            "swimmer_id": s.id,
            "name": s.full_name,
            "category": s.category,
            "shift": today_attendance.get(s.id),
        }
        for s in swimmers
    ]


@router.post("", status_code=201)
def register_attendance(payload: dict, db: Session = Depends(get_db)):
    # payload: { "date": "...", "records": [{"swimmer_id": 1, "shift": "AM_PM"}, ...] }
    active_ids = {s.id for s in db.query(Swimmer.id).filter(Swimmer.status == SwimmerStatus.ACTIVE).all()}
    saved = 0
    for record in payload["records"]:
        if record["swimmer_id"] not in active_ids:
            continue
        existing = db.query(Attendance).filter(
            Attendance.swimmer_id == record["swimmer_id"],
            Attendance.date == payload["date"],
        ).first()
        if existing:
            existing.shift = record["shift"]
        else:
            db.add(Attendance(swimmer_id=record["swimmer_id"], date=payload["date"], shift=record["shift"]))
        saved += 1
    db.commit()
    return {"saved": saved}


@router.get("/summary", response_model=list[AttendanceSummary])
def get_attendance_summary(
    period: str = Query("weekly", description="weekly o monthly"),
    swimmer_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    today = date_type.today()
    since = today - timedelta(days=7 if period == "weekly" else 30)

    query = db.query(Swimmer).filter(Swimmer.status == SwimmerStatus.ACTIVE)
    if swimmer_id:
        query = query.filter(Swimmer.id == swimmer_id)

    swimmers = query.all()
    results = []

    for s in swimmers:
        records = db.query(Attendance).filter(
            Attendance.swimmer_id == s.id,
            Attendance.date >= since,
        ).all()

        total = len(records)
        present = sum(1 for r in records if r.present)
        rate = round((present / total * 100), 1) if total > 0 else 0.0

        results.append(AttendanceSummary(
            swimmer_id=s.id,
            swimmer_name=s.full_name,
            total_sessions=total,
            present_count=present,
            attendance_rate=rate,
        ))

    return results