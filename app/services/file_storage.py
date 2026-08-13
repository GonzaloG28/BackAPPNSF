# app/services/file_storage.py
import uuid
from pathlib import Path

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage" / "mapping_samples"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_sample_file(contents: bytes, original_filename: str) -> str:
    """Guarda el archivo en disco con nombre único y devuelve la ruta."""
    ext = Path(original_filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = STORAGE_DIR / unique_name
    with open(dest_path, "wb") as f:
        f.write(contents)
    return str(dest_path)


def delete_sample_file(path: str | None) -> None:
    """Elimina el archivo si existe. No falla si ya no está (idempotente)."""
    if not path:
        return
    try:
        p = Path(path)
        if p.exists() and p.is_file():
            p.unlink()
    except OSError:
        pass