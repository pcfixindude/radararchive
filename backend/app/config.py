from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    version: str = "0.1.0"
    frontend_origin: str = "http://localhost:5173"

settings = Settings()
