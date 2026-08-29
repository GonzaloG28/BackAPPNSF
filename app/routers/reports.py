# app/routers/reports.py
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


class ReportCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


@router.post("", status_code=201)
async def create_report(payload: ReportCreate, current_user=Depends(get_current_user)):
    user_email = getattr(current_user, "email", "desconocido")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                json={
                    "from": settings.RESEND_FROM,
                    "to": [settings.REPORTS_EMAIL_TO],
                    "subject": f"[SwimAI] Nuevo reporte de {user_email}",
                    "text": f"Usuario: {user_email}\n\nMensaje:\n{payload.message}",
                },
            )
            resp.raise_for_status()
        except Exception:
            logger.exception("Fallo al enviar reporte por correo vía Resend")
            raise HTTPException(status_code=502, detail="No se pudo enviar el reporte por correo")

    return {"ok": True}