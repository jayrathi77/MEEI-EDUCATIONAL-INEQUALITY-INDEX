from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.parent  # project root


class Settings(BaseSettings):
    app_name: str = "MEEI API"
    app_version: str = "1.0.0"
    debug: bool = False
    processed_dir: Path = BASE_DIR / "data" / "processed"
    models_dir: Path = BASE_DIR / "models"
    synthetic_mode: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
