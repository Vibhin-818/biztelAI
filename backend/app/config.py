from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    hf_api_key: str = ""
    hf_model: str = "mistralai/Mistral-Small-3.1-24B-Instruct"
    hf_vision_model: str = "Qwen/Qwen2.5-VL-72B-Instruct"
    database_url: str = "sqlite:///records.db"
    upload_dir: str = "uploads"
    cors_origins: str = "https://biztelai23.vercel.app,http://localhost:5173,http://127.0.0.1:5173"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
