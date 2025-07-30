from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://marcus_user:marcus_password@postgres:5432/marcus_db"

    class Config:
        env_file = ".env"