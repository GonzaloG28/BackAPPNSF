# app/routers/app_update_notes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, get_current_admin
from app.models.app_update_note import AppUpdateNote
from app.models.user import User
from app.schemas.app_update_note import AppUpdateNoteCreate, AppUpdateNoteUpdate

# La lectura queda abierta a cualquier profesor autenticado (así el dashboard
# del profesor puede mostrar las novedades); crear/editar/borrar exige
# is_admin=True — ver get_current_admin en cada endpoint de escritura.
router = APIRouter(prefix="/app-updates", tags=["app-updates"], dependencies=[Depends(get_current_user)])


def _serialize_note(n: AppUpdateNote) -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "body": n.body,
        "audience": n.audience,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


@router.get("")
def list_notes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(AppUpdateNote)
    # El admin ve todo (necesita administrar cada nota); un profesor normal
    # solo ve las dirigidas a "COACHES" o "ALL" — igual que el filtro que
    # aplica /swimmer-self/updates para el lado nadador.
    if not user.is_admin:
        query = query.filter(AppUpdateNote.audience.in_(["COACHES", "ALL"]))
    notes = query.order_by(AppUpdateNote.created_at.desc()).all()
    return [_serialize_note(n) for n in notes]


@router.post("", status_code=201)
def create_note(payload: AppUpdateNoteCreate, admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    note = AppUpdateNote(title=payload.title, body=payload.body, audience=payload.audience, created_by_user_id=admin.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return _serialize_note(note)


@router.patch("/{note_id}")
def update_note(note_id: int, payload: AppUpdateNoteUpdate, admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    note = db.query(AppUpdateNote).filter(AppUpdateNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    db.add(note)
    db.commit()
    db.refresh(note)
    return _serialize_note(note)


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    note = db.query(AppUpdateNote).filter(AppUpdateNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    db.delete(note)
    db.commit()
