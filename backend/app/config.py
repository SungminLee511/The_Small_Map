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

    # Importer scheduling (Phase 1.3.6)
    admin_token: str = ""  # required to call /admin/run-importer; empty = disabled
    importer_scheduler_enabled: bool = False
    importer_csv_dir: str = ""  # if set, importers default to <dir>/<source_id>.csv
    kakao_rest_api_key: str = ""  # for smoking-areas geocoding

    # Auth — cookie config (Phase 2.2.2)
    auth_cookie_name: str = "smallmap_session"
    auth_cookie_secure: bool = False  # set True in production (https-only)
    auth_cookie_samesite: str = "lax"  # or "none" for cross-domain prod

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
