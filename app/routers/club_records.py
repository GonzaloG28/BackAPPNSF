# app/routers/club_records.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user
from app.models.swimmer import SwimmerGender
from app.services.club_records_engine import build_club_records_matrix, recompute_all_club_records

router = APIRouter(prefix="/club-records", tags=["club-records"], dependencies=[Depends(get_current_user)])


@router.get("")
def get_club_records(
    category: Optional[str] = None,
    gender: Optional[SwimmerGender] = None,
    db: Session = Depends(get_db),
):
    """Panel de Mejores Marcas: lectura directa de la tabla club_records (sin
    agregación en caliente), cubriendo toda la matriz evento x categoría x
    género x piscina aunque falten récords (celdas en null = 'Sin récord')."""
    return build_club_records_matrix(db, category=category, gender=gender)


@router.get("/event/{event_type_id}")
def get_club_record_for_event(event_type_id: int, db: Session = Depends(get_db)):
    return build_club_records_matrix(db, event_type_id=event_type_id)


@router.post("/recompute")
def recompute_records(db: Session = Depends(get_db)):
    """Recálculo total explícito (MIN() de verificación), disparado a mano
    desde el panel — no se ejecuta en el camino de lectura habitual."""
    updated = recompute_all_club_records(db)
    return {"updated_slots": updated}
