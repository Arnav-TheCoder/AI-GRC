from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./ai_grc.db"
    upload_dir: str = "./storage"
    max_upload_mb: int = 100
    max_zip_files: int = 5000
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
