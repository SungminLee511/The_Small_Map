from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://smallmap:smallmap@localhost:5432/smallmap"

    # App
    app_env: str = "development"
    app_secret_key: str = "change-me"
    app_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:5173"

    # Auth (Phase 2+)
    kakao_client_id: str = ""
    kakao_client_secret: str = ""
    kakao_redirect_uri: str = "http://localhost:5173/auth/kakao/callback"
    jwt_secret: str = "change-me"
    jwt_issuer: str = "smallmap"
    jwt_audience: str = "smallmap-web"
    jwt_ttl_seconds: int = 2592000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
