from pydantic import BaseModel
from typing import Optional

class RosterExportRequest(BaseModel):
    fields: list[str]  # ej. ["first_name_1","last_name_1","document_id","category"]
    status: Optional[str] = None
    category: Optional[str] = None
    profile: Optional[str] = None
    is_federated: Optional[bool] = None