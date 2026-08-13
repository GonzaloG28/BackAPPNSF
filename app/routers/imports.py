# app/routers/imports.py
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
import io
import re
import json

from app.core.deps import get_db, get_current_user
from app.services.import_service import process_roster_import, process_roster_import_upsert, register_time_record
from app.services.event_code_parser import parse_event_code, EventCodeParseError
from app.services.time_parser import parse_time_to_seconds, TimeParseError
from app.models.import_log import ImportLog, ImportType, ImportStatus
from app.models.import_config import ImportMappingConfig
from app.schemas.import_ import ImportResult
from app.services.file_storage import save_sample_file, delete_sample_file

router = APIRouter(prefix="/imports", tags=["imports"], dependencies=[Depends(get_current_user)])

FIXED_COLUMNS = {
    "nombre": "first_name",
    "apellidos": "last_name",
    "rut": "document_id",
    "genero": "gender",
    "fecha_nacimiento": "birth_date",
    "comuna": "comuna",
    "telefono": "telefono",
    "correo_electronico": "email",
}

DB_FIELDS_CATALOG = [
    {"value": "", "label": "No importar"},
    {"value": "first_name", "label": "Primer nombre"},
    {"value": "first_name_2", "label": "Segundo nombre"},
    {"value": "last_name", "label": "Primer apellido"},
    {"value": "last_name_2", "label": "Segundo apellido"},
    {"value": "document_id", "label": "RUT"},
    {"value": "birth_date", "label": "Fecha de nacimiento"},
    {"value": "comuna", "label": "Comuna"},
    {"value": "institution", "label": "Institución"},
    {"value": "phone", "label": "Teléfono"},
    {"value": "email", "label": "Correo electrónico"},
]


@router.get("/mapping-config")
def get_mapping_config(db: Session = Depends(get_db)):
    config = db.query(ImportMappingConfig).first()
    return {
        "fields_catalog": DB_FIELDS_CATALOG,
        "mapping": config.mapping if config else None,
        "sample_file_name": config.sample_file_name if config else None,
    }


@router.put("/mapping-config")
def save_mapping_config(payload: dict, db: Session = Depends(get_db)):
    """payload: { "mapping": {"Nombre": "first_name", "RUT": "document_id", ...} } """
    config = db.query(ImportMappingConfig).first()
    if config:
        config.mapping = payload["mapping"]
    else:
        config = ImportMappingConfig(mapping=payload["mapping"])
        db.add(config)
    db.commit()
    return {"ok": True}



@router.post("/mapping-config/sample-file")
async def upload_mapping_sample_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="El archivo debe ser Excel (.xlsx/.xls) o CSV")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents)) if file.filename.endswith(".csv") else pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {str(e)}")

    df.columns = [str(c).strip() for c in df.columns]

    config = db.query(ImportMappingConfig).order_by(ImportMappingConfig.id.asc()).first()
    if not config:
        config = ImportMappingConfig(mapping={})
        db.add(config)
        db.commit()
        db.refresh(config)

    delete_sample_file(config.sample_file_path)

    saved_path = save_sample_file(contents, file.filename)
    config.sample_file_name = file.filename
    config.sample_file_path = saved_path
    config.mapping = {}  # <-- el mapeo viejo ya no corresponde a las columnas del excel nuevo
    db.add(config)
    db.commit()

    return {
        "columns": list(df.columns),
        "preview_rows": df.head(5).fillna("").to_dict(orient="records"),
        "total_rows": len(df),
        "sample_file_name": config.sample_file_name,
    }


@router.delete("/mapping-config/mapping")
def clear_mapping(db: Session = Depends(get_db)):
    """Vacía el mapeo guardado (columna Excel -> campo DB), sin tocar el archivo de ejemplo."""
    config = db.query(ImportMappingConfig).order_by(ImportMappingConfig.id.asc()).first()
    if not config:
        raise HTTPException(status_code=404, detail="No hay una plantilla configurada")

    config.mapping = {}
    db.add(config)
    db.commit()

    return {"ok": True}



@router.delete("/mapping-config/sample-file")
def delete_mapping_sample_file(db: Session = Depends(get_db)):
    config = db.query(ImportMappingConfig).order_by(ImportMappingConfig.id.asc()).first()
    if not config or not config.sample_file_path:
        raise HTTPException(status_code=404, detail="No hay un archivo de ejemplo guardado")

    delete_sample_file(config.sample_file_path)
    config.sample_file_name = None
    config.sample_file_path = None
    db.add(config)
    db.commit()

    return {"ok": True}



@router.post("/roster/preview")
async def preview_roster_import(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents)) if not file.filename.endswith(".csv") else pd.read_csv(io.BytesIO(contents))
    df.columns = [str(c).strip() for c in df.columns]

    return {
        "columns": list(df.columns),
        "preview_rows": df.head(5).fillna("").to_dict(orient="records"),
        "total_rows": len(df),
    }


@router.post("/roster/mapped")
async def import_roster_mapped(file: UploadFile = File(...), mapping: str = Form(...), db: Session = Depends(get_db)):
    """mapping: JSON string {"Columna Excel": "campo_db"} ej. {"Nombre":"first_name","RUT":"document_id"}"""
    field_map = json.loads(mapping)

    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents)) if not file.filename.endswith(".csv") else pd.read_csv(io.BytesIO(contents))

    rows = []
    for _, row in df.iterrows():
        mapped_row = {}
        for excel_col, db_field in field_map.items():
            if db_field and excel_col in df.columns:
                value = row.get(excel_col)
                mapped_row[db_field] = None if pd.isna(value) else value
        rows.append(mapped_row)

    matched, created, unmatched, _ = process_roster_import(db, rows, None)
    return {"matched": matched, "created": created, "unmatched": unmatched}


@router.post("/roster/apply-saved-mapping")
async def import_with_saved_mapping(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Usa la plantilla guardada — el flujo diario del profesor, sin remapear cada vez.
    Solo rellena campos vacíos en nadadores existentes, nunca sobreescribe datos ya cargados."""
    config = db.query(ImportMappingConfig).first()
    if not config:
        raise HTTPException(status_code=400, detail="No hay una plantilla de mapeo configurada aún")

    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents)) if not file.filename.endswith(".csv") else pd.read_csv(io.BytesIO(contents))
    df.columns = [str(c).strip() for c in df.columns]

    rows = []
    for _, row in df.iterrows():
        mapped = {}
        for excel_col, db_field in config.mapping.items():
            if db_field and excel_col in df.columns:
                value = row.get(excel_col)
                mapped[db_field] = None if pd.isna(value) else value
        rows.append(mapped)

    matched, created, unmatched, _ = process_roster_import_upsert(db, rows, None)
    return {"matched": matched, "created": created, "unmatched": unmatched}


@router.post("/roster", response_model=ImportResult)
async def import_roster(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="El archivo debe ser Excel (.xlsx/.xls) o CSV")

    contents = await file.read()
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {str(e)}")

    df.columns = [str(c).strip().lower().replace(" ", "_").replace("°", "") for c in df.columns]

    missing = [col for col in FIXED_COLUMNS if col not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan columnas requeridas: {missing}. Encontradas: {list(df.columns)}"
        )

    prueba_cols = sorted(
        [c for c in df.columns if re.fullmatch(r"nprueba(\.\d+)?", c)],
        key=lambda c: int(c.split(".")[1]) if "." in c else 0
    )
    tiempo_cols = sorted(
        [c for c in df.columns if re.fullmatch(r"tiempo(\.\d+)?", c)],
        key=lambda c: int(c.split(".")[1]) if "." in c else 0
    )

    if len(prueba_cols) != len(tiempo_cols):
        raise HTTPException(
            status_code=400,
            detail=f"Descalce entre columnas de prueba ({len(prueba_cols)}) y tiempo ({len(tiempo_cols)})"
        )

    rows = []
    time_entries_by_row = []

    for _, row in df.iterrows():
        rows.append({
            "first_name": _clean_str(row.get("nombre")),
            "last_name": _clean_str(row.get("apellidos")),
            "document_id": _clean_str(row.get("rut")),
            "birth_date": _clean_date(row.get("fecha_nacimiento")),
        })

        pairs = []
        for pcol, tcol in zip(prueba_cols, tiempo_cols):
            code = _clean_str(row.get(pcol))
            time_raw = _clean_str(row.get(tcol))
            if code and time_raw:
                pairs.append((code, time_raw))
        time_entries_by_row.append(pairs)

    import_log = ImportLog(
        file_name=file.filename, type=ImportType.ROSTER,
        row_count=len(rows), status=ImportStatus.SUCCESS,
    )
    db.add(import_log)
    db.commit()
    db.refresh(import_log)

    matched, created, unmatched, swimmer_ids = process_roster_import(db, rows, import_log.id)

    time_errors = []
    for idx, swimmer_id in enumerate(swimmer_ids):
        if swimmer_id is None:
            continue
        for code, time_raw in time_entries_by_row[idx]:
            try:
                distance, stroke = parse_event_code(code)
                seconds = parse_time_to_seconds(time_raw)
                register_time_record(db, swimmer_id, distance, stroke, seconds)
            except (EventCodeParseError, TimeParseError) as e:
                time_errors.append({"row": idx, "code": code, "time": time_raw, "error": str(e)})

    import_log.matched_count = matched + created
    import_log.unmatched_count = len(unmatched)
    import_log.status = (
        ImportStatus.SUCCESS if not unmatched and not time_errors
        else ImportStatus.PARTIAL if (matched + created) > 0
        else ImportStatus.FAILED
    )
    db.add(import_log)
    db.commit()

    return ImportResult(
        import_log_id=import_log.id,
        status=import_log.status,
        row_count=len(rows),
        matched_count=matched + created,
        unmatched_count=len(unmatched),
        unmatched_rows=unmatched,
    )


def _clean_str(value):
    if pd.isna(value):
        return None
    return str(value).strip()


def _clean_date(value):
    if pd.isna(value):
        return None
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None