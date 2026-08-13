# dedupe_import_mapping_configs.py
from pathlib import Path
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT id, mapping, sample_file_path, updated_at FROM import_mapping_configs ORDER BY id"
    )).fetchall()

    if len(rows) <= 1:
        print("No hay duplicados, nada que hacer.")
    else:
        # Elige la fila "ganadora": la que tenga mapping no vacío y sea la más reciente
        def score(row):
            _, mapping, _, updated_at = row
            has_mapping = 1 if mapping else 0
            return (has_mapping, updated_at or "")

        winner = max(rows, key=score)
        winner_id = winner[0]
        losers = [r for r in rows if r[0] != winner_id]

        print(f"Fila ganadora: id={winner_id}")
        for loser_id, _, loser_path, _ in losers:
            if loser_path:
                p = Path(loser_path)
                if p.exists():
                    p.unlink()
                    print(f"Archivo borrado del disco: {loser_path}")
            conn.execute(text("DELETE FROM import_mapping_configs WHERE id = :id"), {"id": loser_id})
            print(f"Fila borrada: id={loser_id}")

        conn.commit()
        print("Listo, ahora queda una sola fila.")