# app/routers/exports.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.convocatoria import Convocatoria, ConvocatoriaStatus
from app.services.export_service import generate_convocatoria_excel
from app.core.deps import get_current_user

router = APIRouter(prefix="/convocatorias", tags=["exports"], dependencies=[Depends(get_current_user)])


@router.get("/{convocatoria_id}/export")
def export_convocatoria(convocatoria_id: int, db: Session = Depends(get_db)):
    convocatoria = db.query(Convocatoria).filter(Convocatoria.id == convocatoria_id).first()
    if not convocatoria:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")

    if convocatoria.status == ConvocatoriaStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="La convocatoria debe estar confirmada antes de exportar"
        )

    buffer = generate_convocatoria_excel(db, convocatoria)

    convocatoria.status = ConvocatoriaStatus.EXPORTED
    db.add(convocatoria)
    db.commit()

    filename = f"convocatoria_{convocatoria.competition.name.replace(' ', '_')}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )