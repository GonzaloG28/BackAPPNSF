from datetime import datetime, timedelta
from jose import jwt
from app.config import settings

def create_swimmer_token(swimmer_id: int) -> str:
    to_encode = {"sub": str(swimmer_id), "type": "swimmer"}
    expire = datetime.utcnow() + timedelta(hours=12)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)