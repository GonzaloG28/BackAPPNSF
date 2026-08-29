# app/routers/reports.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.deps import get_current_user
from app.config import settings  # asume que tienes settings con credenciales SMTP

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


class ReportCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


@router.post("", status_code=201)
def create_report(payload: ReportCreate, current_user=Depends(get_current_user)):
    try:
        _send_report_email(payload.message, current_user)
    except Exception as e:
        raise HTTPException(status_code=502, detail="No se pudo enviar el reporte por correo")
    return {"ok": True}


def _send_report_email(message: str, current_user):
    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = settings.REPORTS_EMAIL_TO
    msg["Subject"] = f"[SwimAI] Nuevo reporte de {getattr(current_user, 'email', 'usuario')}"

    body = f"Usuario: {getattr(current_user, 'email', 'desconocido')}\n\nMensaje:\n{message}"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)