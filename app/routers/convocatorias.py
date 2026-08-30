# app/routers/convocatorias.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.convocatoria import Convocatoria, ConvocatoriaStatus
from app.models.convocatoria_entry import ConvocatoriaEntry
from app.schemas.convocatoria import ConvocatoriaCreate, ConvocatoriaEntriesUpdate
from app.models.competition import Competition
from app.services.convocatoria_engine import build_convocatoria_matrix, sync_convocatoria_entries
from app.core.deps import get_current_user


router = APIRouter(prefix="/convocatorias", tags=["convocatorias"], dependencies=[Depends(get_current_user)])


@router.get("")
def list_convocatorias(db: Session = Depends(get_db)):
    convocatorias = db.query(Convocatoria).order_by(Convocatoria.created_at.desc()).all()
    return [{
        "id": c.id, "competition_id": c.competition_id, "status": c.status.value, "created_at": c.created_at,
        "competition_name": c.competition.name if c.competition else None,
        "competition_start_date": c.competition.start_date.isoformat() if c.competition and c.competition.start_date else None,
        "competition_end_date": c.competition.end_date.isoformat() if c.competition and c.competition.end_date else None,
    } for c in convocatorias]

@router.post("", status_code=201)
def create_convocatoria(payload: ConvocatoriaCreate, db: Session = Depends(get_db)):
    convocatoria = Convocatoria(competition_id=payload.competition_id, status=ConvocatoriaStatus.DRAFT)
    db.add(convocatoria)
    db.commit()
    db.refresh(convocatoria)
    return convocatoria


@router.get("/{convocatoria_id}/matrix")
def get_convocatoria_matrix(convocatoria_id: int, db: Session = Depends(get_db)):
    convocatoria = db.query(Convocatoria).filter(Convocatoria.id == convocatoria_id).first()
    if not convocatoria:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    matrix = build_convocatoria_matrix(db, convocatoria)
    sync_convocatoria_entries(db, convocatoria, matrix)

    return {"convocatoria_id": convocatoria_id, "swimmers": matrix}


@router.get("/stats")
def get_convocatoria_stats(db: Session = Depends(get_db)):
    all_conv = db.query(Convocatoria).all()
    return {
        "total": len(all_conv),
        "active": sum(1 for c in all_conv if c.status in ("CONFIRMED", "EXPORTED")),
        "draft": sum(1 for c in all_conv if c.status == "DRAFT"),
    }

@router.patch("/{convocatoria_id}/entries")
def update_entries(convocatoria_id: int, payload: ConvocatoriaEntriesUpdate, db: Session = Depends(get_db)):
    convocatoria = db.query(Convocatoria).filter(Convocatoria.id == convocatoria_id).first()
    if not convocatoria:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    updated = 0
    for item in payload.entries:
        entry = db.query(ConvocatoriaEntry).filter(
            ConvocatoriaEntry.convocatoria_id == convocatoria_id,
            ConvocatoriaEntry.swimmer_id == item.swimmer_id,
            ConvocatoriaEntry.event_type_id == item.event_type_id,
        ).first()

        if not entry:
            entry = ConvocatoriaEntry(
                convocatoria_id=convocatoria_id, swimmer_id=item.swimmer_id, event_type_id=item.event_type_id,
            )

        entry.selected = item.selected

        # Si se manda un tiempo manual (incluyendo "NT"), se registra como inscripción sin marca oficial
        if item.manual_time == "NT":
            entry.best_time_seconds = None
            entry.is_nt_inscription = True  # nuevo campo, ver abajo
        elif isinstance(item.manual_time, (int, float)):
            entry.best_time_seconds = item.manual_time
            entry.is_nt_inscription = False

        db.add(entry)
        updated += 1

    db.commit()
    return {"updated": updated}


@router.get("/{convocatoria_id}/matrix")
def get_convocatoria_matrix(convocatoria_id: int, db: Session = Depends(get_db)):
    convocatoria = db.query(Convocatoria).filter(Convocatoria.id == convocatoria_id).first()
    if not convocatoria:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    matrix = build_convocatoria_matrix(db, convocatoria)
    sync_convocatoria_entries(db, convocatoria, matrix)

    return {"convocatoria_id": convocatoria_id, **matrix}


@router.patch("/{convocatoria_id}/confirm")
def confirm_convocatoria(convocatoria_id: int, db: Session = Depends(get_db)):
    c = db.query(Convocatoria).filter(Convocatoria.id == convocatoria_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    c.status = ConvocatoriaStatus.CONFIRMED
    db.commit()
    db.refresh(c)
    return c


@router.patch("/{convocatoria_id}/unconfirm")
def unconfirm_convocatoria(convocatoria_id: int, db: Session = Depends(get_db)):
    c = db.query(Convocatoria).filter(Convocatoria.id == convocatoria_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    c.status = ConvocatoriaStatus.DRAFT
    db.commit()
    db.refresh(c)
    return c


@router.patch("/{convocatoria_id}/skip-minimums")
def skip_minimums(convocatoria_id: int, db: Session = Depends(get_db)):
    return {"ok": True}


@router.delete("/{convocatoria_id}", status_code=204)
def delete_convocatoria(convocatoria_id: int, db: Session = Depends(get_db)):
    convocatoria = db.query(Convocatoria).filter(Convocatoria.id == convocatoria_id).first()
    if not convocatoria:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    competition_id = convocatoria.competition_id

    db.delete(convocatoria)  # cascade="all, delete-orphan" borra las entries asociadas
    db.flush()

    remaining = db.query(Convocatoria).filter(Convocatoria.competition_id == competition_id).count()
    if remaining == 0:
        competition = db.query(Competition).filter(Competition.id == competition_id).first()
        if competition:
            db.delete(competition)  # cascade borra sus qualifying_times

    db.commit()
    return None