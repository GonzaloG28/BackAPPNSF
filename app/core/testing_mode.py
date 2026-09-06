import os
from dotenv import load_dotenv

load_dotenv()  # asegura que .env se cargue al entorno del proceso, sin depender de Pydantic Settings
GOD_MODE = os.getenv("SWIMAI_GOD_MODE", "false").lower() == "true"