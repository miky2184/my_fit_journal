from functools import lru_cache
from os import getenv

from dotenv import load_dotenv


load_dotenv()


class Settings:
    db_host: str = getenv("DB_HOST", "127.0.0.1")
    db_port: int = int(getenv("DB_PORT", "5432"))
    db_name: str = getenv("DB_NAME", "myfitjournal")
    db_schema: str = getenv("DB_SCHEMA", "myfit")
    db_user: str = getenv("DB_USER", "postgres")
    db_password: str = getenv("DB_PASSWORD", "postgres")

    app_host: str = getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(getenv("APP_PORT", "8000"))
    app_env: str = getenv("APP_ENV", "development")
    secret_key: str = getenv("SECRET_KEY", "dev-only-key")

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
