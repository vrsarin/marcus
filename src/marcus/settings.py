from os import getenv


class Constants:
    MARCUS_DB_HOST: str = getenv("MARCUS_DB_HOST", "localhost")
    MARCUS_DB_SERVICE: str = getenv("MARCUS_DB_SERVICE", "app-db")
    MARCUS_DB_PORT: str = getenv("MARCUS_DB_PORT", "5432")
    MARCUS_DB_USER: str = getenv("MARCUS_DB_USER", "marcus_user")
    MARCUS_DB_PASSWORD: str = getenv("MARCUS_DB_PASSWORD", "marcus_password")
    MARCUS_DB_NAME: str = getenv("MARCUS_DB_NAME", "marcus_db")

    MARCUS_OTEL_HOST: str = getenv("MARCUS_OTEL_HOST", "localhost")
    MARCUS_OTEL_PORT: int = int(getenv("MARCUS_OTEL_PORT", "4318"))
    MARCUS_OTEL_PROTOCOL: str = getenv("MARCUS_OTEL_PROTOCOL", "http")
    MARCUS_OTEL_PATH: str = getenv("MARCUS_OTEL_PATH", "/v1/traces")
    MARCUS_OTEL_TIMEOUT: int = int(getenv("MARCUS_OTEL_TIMEOUT", "10"))

    @staticmethod
    def db_url():
        return f"postgresql://{Constants.MARCUS_DB_USER}:{Constants.MARCUS_DB_PASSWORD}@{Constants.MARCUS_DB_HOST}:{Constants.MARCUS_DB_PORT}/{Constants.MARCUS_DB_NAME}"
