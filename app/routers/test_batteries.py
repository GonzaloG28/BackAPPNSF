# app/routers/test_batteries.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.core.deps import get_db, get_current_user
from app.models.test_battery import TestBattery, TestResultType
from app.models.test_battery_result import TestBatteryResult
from app.models.test_battery_split import TestBatterySplit
from app.models.test_battery_rep import TestBatteryRep, TestBatteryRepSplit
from app.models.time_record import TimeRecord
from app.schemas.test_battery import (
    TestBatteryCreate, TestBatteryUpdate, BulkResultsIn, TestBatteryResultUpdate, RepsResultIn,
)

router = APIRouter(prefix="/test-batteries", tags=["test-batteries"], dependencies=[Depends(get_current_user)])

SPLIT_TOLERANCE = 0.05  # mismo margen que TimeRecord entre suma de parciales y valor total


def _serialize_battery(b: TestBattery) -> dict:
    return {
        "id": b.id, "name": b.name, "description": b.description,
        "structure_label": b.structure_label, "result_type": b.result_type.value,
        "distance_m": b.distance_m, "allows_splits": b.allows_splits, "is_active": b.is_active,
        "reps_count": b.reps_count, "is_control": b.is_control,
        "event_type_id": b.event_type_id,
        "event_type_name": b.event_type.name if b.event_type else None,
    }


def _get_pb_seconds(db: Session, swimmer_id: int, event_type_id: Optional[int]) -> Optional[float]:
    if not event_type_id:
        return None
    best = db.query(func.min(TimeRecord.time_seconds)).filter(
        TimeRecord.swimmer_id == swimmer_id, TimeRecord.event_type_id == event_type_id,
    ).scalar()
    return float(best) if best is not None else None


def _serialize_rep(rep: TestBatteryRep, pb_seconds: Optional[float]) -> dict:
    time_s = float(rep.time_seconds)
    return {
        "id": rep.id, "rep_number": rep.rep_number, "time_seconds": time_s, "notes": rep.notes,
        # gap > 0 = más lento que el PB; gap < 0 = mejoró el PB.
        "gap_vs_pb": round(time_s - pb_seconds, 2) if pb_seconds is not None else None,
        "splits": [
            {
                "distance_mark": s.distance_mark,
                "segment_seconds": float(s.segment_seconds),
                "cumulative_seconds": float(s.cumulative_seconds),
            }
            for s in sorted(rep.splits, key=lambda x: x.distance_mark)
        ],
    }


def _serialize_result(r: TestBatteryResult, pb_seconds: Optional[float] = None) -> dict:
    return {
        "id": r.id, "battery_id": r.battery_id, "swimmer_id": r.swimmer_id,
        "swimmer_name": r.swimmer.full_name if r.swimmer else None,
        "recorded_date": r.recorded_date.isoformat(),
        "value_seconds": float(r.value_seconds) if r.value_seconds is not None else None,
        "value_reps": r.value_reps, "notes": r.notes, "split_increment": r.split_increment,
        "splits": [
            {
                "distance_mark": s.distance_mark,
                "segment_seconds": float(s.segment_seconds),
                "cumulative_seconds": float(s.cumulative_seconds),
            }
            for s in sorted(r.splits, key=lambda x: x.distance_mark)
        ],
        "pb_seconds": pb_seconds,
        "reps": [_serialize_rep(rep, pb_seconds) for rep in sorted(r.reps, key=lambda x: x.rep_number)],
    }


def _build_splits(splits_in, total_seconds: Optional[float]):
    if not splits_in:
        return None
    cumulative = 0.0
    built = []
    for s in splits_in:
        cumulative += s.segment_seconds
        built.append(TestBatterySplit(
            distance_mark=s.distance_mark,
            segment_seconds=s.segment_seconds,
            cumulative_seconds=round(cumulative, 2),
        ))
    if total_seconds is not None and abs(cumulative - total_seconds) > SPLIT_TOLERANCE:
        raise HTTPException(
            status_code=400,
            detail=f"La suma de los parciales ({cumulative:.2f}s) no coincide con el valor total ({total_seconds:.2f}s).",
        )
    return built


def _build_rep_splits(splits_in, total_seconds: float):
    if not splits_in:
        return None
    cumulative = 0.0
    built = []
    for s in splits_in:
        cumulative += s.segment_seconds
        built.append(TestBatteryRepSplit(
            distance_mark=s.distance_mark,
            segment_seconds=s.segment_seconds,
            cumulative_seconds=round(cumulative, 2),
        ))
    if abs(cumulative - total_seconds) > SPLIT_TOLERANCE:
        raise HTTPException(
            status_code=400,
            detail=f"La suma de los parciales ({cumulative:.2f}s) no coincide con el tiempo de la repetición ({total_seconds:.2f}s).",
        )
    return built


@router.get("")
def list_batteries(include_inactive: bool = False, db: Session = Depends(get_db)):
    query = db.query(TestBattery)
    if not include_inactive:
        query = query.filter(TestBattery.is_active == True)
    batteries = query.order_by(TestBattery.name).all()
    return [_serialize_battery(b) for b in batteries]


@router.post("", status_code=201)
def create_battery(payload: TestBatteryCreate, db: Session = Depends(get_db)):
    battery = TestBattery(**payload.model_dump())
    db.add(battery)
    db.commit()
    db.refresh(battery)
    return _serialize_battery(battery)


@router.patch("/{battery_id}")
def update_battery(battery_id: int, payload: TestBatteryUpdate, db: Session = Depends(get_db)):
    battery = db.query(TestBattery).filter(TestBattery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Batería no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(battery, field, value)
    db.add(battery)
    db.commit()
    db.refresh(battery)
    return _serialize_battery(battery)


@router.patch("/{battery_id}/archive")
def archive_battery(battery_id: int, db: Session = Depends(get_db)):
    battery = db.query(TestBattery).filter(TestBattery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Batería no encontrada")
    battery.is_active = False
    db.add(battery)
    db.commit()
    return {"id": battery.id, "is_active": battery.is_active}


@router.delete("/{battery_id}", status_code=204)
def delete_battery(battery_id: int, db: Session = Depends(get_db)):
    battery = db.query(TestBattery).filter(TestBattery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Batería no encontrada")
    results_count = db.query(TestBatteryResult).filter(TestBatteryResult.battery_id == battery_id).count()
    if results_count > 0:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar: la batería tiene resultados cargados. Archívala en su lugar.",
        )
    db.delete(battery)
    db.commit()


@router.post("/{battery_id}/results/bulk", status_code=201)
def create_results_bulk(battery_id: int, payload: BulkResultsIn, db: Session = Depends(get_db)):
    battery = db.query(TestBattery).filter(TestBattery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Batería no encontrada")

    new_results = []
    for entry in payload.entries:
        if battery.result_type == TestResultType.TIME and entry.value_seconds is None:
            raise HTTPException(status_code=400, detail=f"Falta value_seconds para el nadador {entry.swimmer_id}")
        if battery.result_type == TestResultType.REPETITIONS and entry.value_reps is None:
            raise HTTPException(status_code=400, detail=f"Falta value_reps para el nadador {entry.swimmer_id}")

        splits = _build_splits(entry.splits, entry.value_seconds)
        result = TestBatteryResult(
            battery_id=battery_id, swimmer_id=entry.swimmer_id,
            recorded_date=payload.recorded_date, value_seconds=entry.value_seconds,
            value_reps=entry.value_reps, notes=entry.notes, split_increment=entry.split_increment,
        )
        if splits:
            result.splits = splits
        new_results.append(result)

    # Un solo add_all + un solo commit: la carga de 20-40 nadadores no hace N round-trips.
    db.add_all(new_results)
    db.commit()
    for r in new_results:
        db.refresh(r)

    return {"created": len(new_results), "results": [_serialize_result(r) for r in new_results]}


@router.get("/{battery_id}/results")
def list_results(
    battery_id: int,
    recorded_date: Optional[date] = None,
    swimmer_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    battery = db.query(TestBattery).filter(TestBattery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Batería no encontrada")

    query = db.query(TestBatteryResult).filter(TestBatteryResult.battery_id == battery_id)
    if recorded_date:
        query = query.filter(TestBatteryResult.recorded_date == recorded_date)
    if swimmer_id:
        query = query.filter(TestBatteryResult.swimmer_id == swimmer_id)
    results = query.order_by(TestBatteryResult.recorded_date.desc()).all()

    # PB por nadador, calculado una vez por nadador distinto en la lista
    # (no una query por resultado) — solo tiene sentido en modo Control.
    pb_cache: dict[int, Optional[float]] = {}
    def pb_for(sid: int) -> Optional[float]:
        if not battery.is_control:
            return None
        if sid not in pb_cache:
            pb_cache[sid] = _get_pb_seconds(db, sid, battery.event_type_id)
        return pb_cache[sid]

    return [_serialize_result(r, pb_for(r.swimmer_id)) for r in results]


@router.post("/{battery_id}/results-with-reps", status_code=201)
def create_result_with_reps(battery_id: int, payload: RepsResultIn, db: Session = Depends(get_db)):
    """Carga una sesión completa con N repeticiones numeradas (ej. 10x100m =
    10 tiempos). Si la batería es "Control / Toma de Marca", la respuesta
    incluye el GAP de cada repetición contra la Mejor Marca Personal del
    nadador en battery.event_type_id."""
    battery = db.query(TestBattery).filter(TestBattery.id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Batería no encontrada")
    if not payload.reps:
        raise HTTPException(status_code=400, detail="Debes ingresar al menos una repetición")

    result = TestBatteryResult(
        battery_id=battery_id, swimmer_id=payload.swimmer_id,
        recorded_date=payload.recorded_date, notes=payload.notes,
    )
    reps = []
    for rep_in in payload.reps:
        rep = TestBatteryRep(rep_number=rep_in.rep_number, time_seconds=rep_in.time_seconds, notes=rep_in.notes)
        rep_splits = _build_rep_splits(rep_in.splits, rep_in.time_seconds)
        if rep_splits:
            rep.splits = rep_splits
        reps.append(rep)
    result.reps = reps

    db.add(result)
    db.commit()
    db.refresh(result)

    pb_seconds = _get_pb_seconds(db, payload.swimmer_id, battery.event_type_id) if battery.is_control else None
    return _serialize_result(result, pb_seconds)


@router.patch("/{battery_id}/results/{result_id}")
def update_result(battery_id: int, result_id: int, payload: TestBatteryResultUpdate, db: Session = Depends(get_db)):
    result = db.query(TestBatteryResult).filter(
        TestBatteryResult.id == result_id, TestBatteryResult.battery_id == battery_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")

    data = payload.model_dump(exclude_unset=True, exclude={"splits"})
    for field, value in data.items():
        setattr(result, field, value)

    if payload.splits is not None:
        effective_total = (
            payload.value_seconds if payload.value_seconds is not None
            else (float(result.value_seconds) if result.value_seconds is not None else None)
        )
        splits = _build_splits(payload.splits, effective_total)
        result.splits = splits or []
        result.split_increment = payload.split_increment

    db.add(result)
    db.commit()
    db.refresh(result)
    return _serialize_result(result)


@router.delete("/{battery_id}/results/{result_id}", status_code=204)
def delete_result(battery_id: int, result_id: int, db: Session = Depends(get_db)):
    result = db.query(TestBatteryResult).filter(
        TestBatteryResult.id == result_id, TestBatteryResult.battery_id == battery_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    db.delete(result)
    db.commit()


@router.get("/{battery_id}/evolution")
def get_battery_evolution(battery_id: int, swimmer_id: int, db: Session = Depends(get_db)):
    """Mismo shape que GET /swimmers/{id}/evolution, para reusar EvolutionLineChart tal cual en el frontend."""
    results = db.query(TestBatteryResult).filter(
        TestBatteryResult.battery_id == battery_id, TestBatteryResult.swimmer_id == swimmer_id
    ).order_by(TestBatteryResult.recorded_date.asc()).all()

    return [{
        "id": r.id,
        "date": r.recorded_date.isoformat(),
        "time_seconds": float(r.value_seconds) if r.value_seconds is not None else None,
        "value_reps": r.value_reps,
        "label": r.notes or "Registro",
        "split_increment": r.split_increment,
        "splits": [
            {
                "distance_mark": s.distance_mark,
                "segment_seconds": float(s.segment_seconds),
                "cumulative_seconds": float(s.cumulative_seconds),
            }
            for s in sorted(r.splits, key=lambda x: x.distance_mark)
        ],
    } for r in results]
