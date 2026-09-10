# app/schemas/app_update_note.py
from pydantic import BaseModel
from typing import Literal, Optional

Audience = Literal["SWIMMERS", "COACHES", "ALL"]


class AppUpdateNoteCreate(BaseModel):
    title: str
    body: str
    audience: Audience = "ALL"


class AppUpdateNoteUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    audience: Optional[Audience] = None
