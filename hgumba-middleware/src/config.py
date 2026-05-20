from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # SENAITE
    senaite_url: str = "http://localhost:8083/senaite"
    senaite_user: str = "admin"
    senaite_password: str = ""

    # PostgreSQL (CATSERV billing)
    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "financeiro"
    db_user: str = "catserv"
    db_password: str = ""

    # SANDRA (Exército) — mock endpoints
    sandra_base_url: str = ""
    sandra_api_key: str = ""

    # CADBEN (Exército) — mock endpoints
    cadben_base_url: str = ""
    cadben_api_key: str = ""

    # SIRE (Exército) — mock endpoints
    sire_base_url: str = ""
    sire_api_key: str = ""

    # API Security
    api_key: str = ""
    cors_origins: str = "http://localhost:3000"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
