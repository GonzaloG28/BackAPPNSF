# wipe_all_sample_files.py
from pathlib import Path
from app.database import engine
from sqlalchemy import text

STORAGE_DIR = Path(__file__).resolve().parent / "app" / "storage" / "mapping_samples"

with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT id, sample_file_path FROM import_mapping_configs"
    )).fetchall()

    print(f"Filas encontradas: {len(rows)}")

    # 1. Borra el archivo referenciado en cada fila (si existe)
    for row_id, path in rows:
        if path:
            p = Path(path)
            if p.exists():
                p.unlink()
                print(f"Borrado (referenciado): {path}")

    # 2. Limpia las referencias en TODAS las filas
    conn.execute(text(
        "UPDATE import_mapping_configs SET sample_file_name = NULL, sample_file_path = NULL"
    ))
    conn.commit()
    print("Referencias limpiadas en todas las filas.")

# 3. Por si quedó basura suelta en la carpeta que ninguna fila referenciaba
if STORAGE_DIR.exists():
    leftover = list(STORAGE_DIR.glob("*"))
    for f in leftover:
        if f.is_file():
            f.unlink()
            print(f"Borrado (huérfano): {f}")
    print(f"Total huérfanos borrados: {len(leftover)}")
else:
    print("Carpeta de storage no existe, nada que limpiar ahí.")

print("Listo — no debería quedar ningún excel.")