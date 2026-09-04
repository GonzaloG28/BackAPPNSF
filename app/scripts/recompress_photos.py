# app/scripts/recompress_photos.py
from app.database import SessionLocal
from app.models.swimmer import Swimmer
from PIL import Image
import io, base64

def recompress_all():
    db = SessionLocal()
    swimmers = db.query(Swimmer).filter(Swimmer.photo_base64.isnot(None)).all()
    for s in swimmers:
        try:
            _, encoded = s.photo_base64.split(",", 1)
            img = Image.open(io.BytesIO(base64.b64decode(encoded))).convert("RGB")
            img.thumbnail((400, 400))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=60, optimize=True)
            s.photo_base64 = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()
            db.add(s)
        except Exception as e:
            print(f"Error con nadador {s.id}: {e}")
    db.commit()
    print(f"Recomprimidas {len(swimmers)} fotos")

if __name__ == "__main__":
    recompress_all()