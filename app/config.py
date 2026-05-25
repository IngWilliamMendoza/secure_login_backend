import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Aplicación
    SECRET_KEY: str = os.getenv("SECRET_KEY") or "dev-secret-key"
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "0") == "1"

    # Base de datos
    _db_user: str = os.getenv("POSTGRES_USER") or ""
    _db_password: str = os.getenv("POSTGRES_PASSWORD") or ""
    _db_host: str = os.getenv("POSTGRES_HOST", "localhost")
    _db_port: str = os.getenv("POSTGRES_PORT", "5432")
    _db_name: str = os.getenv("POSTGRES_DB") or ""

    if not all([_db_user, _db_password, _db_name]):
        raise ValueError(
            "Faltan variables de entorno requeridas: "
            "POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB."
        )

    SQLALCHEMY_DATABASE_URI: str = (
        f"postgresql://{_db_user}:{_db_password}"
        f"@{_db_host}:{_db_port}/{_db_name}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = os.getenv("FLASK_DEBUG", "0") == "1"

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") or "dev-jwt-secret"
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "15"))
    )
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30"))
    )
    JWT_HEADER_NAME: str = "Authorization"
    JWT_HEADER_TYPE: str = "Bearer"
    JWT_COOKIE_SECURE: bool = os.getenv("FLASK_ENV") == "production"
    JWT_COOKIE_SAMESITE: str = "Lax"
    JWT_REFRESH_COOKIE_PATH: str = "/api/v1/auth/refresh"
    JWT_TOKEN_LOCATION: list[str] = ["headers", "cookies"]

    # OpenAPI / Swagger
    API_TITLE: str = "Mi API"
    API_VERSION: str = "v1"
    OPENAPI_VERSION: str = "3.0.3"
    OPENAPI_URL_PREFIX: str = "/"
    OPENAPI_SWAGGER_UI_PATH: str = "/docs"
    OPENAPI_SWAGGER_UI_URL: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:4321")
    CORS_SUPPORTS_CREDENTIALS: bool = os.getenv("CORS_SUPPORTS_CREDENTIALS", "True") == "True"


    # reCAPTCHA
    RECAPTCHA_ENABLED: bool = os.getenv("RECAPTCHA_ENABLED", "True") == "True"
    RECAPTCHA_SECRET_KEY: str = os.getenv("RECAPTCHA_SECRET_KEY") or ""
    RECAPTCHA_SITE_KEY: str = os.getenv("RECAPTCHA_SITE_KEY") or ""
    RECAPTCHA_MIN_SCORE: float = float(os.getenv("RECAPTCHA_MIN_SCORE", "0.5"))
    RECAPTCHA_VERIFY_URL: str = "https://www.google.com/recaptcha/api/siteverify"

    if not RECAPTCHA_SECRET_KEY:
        raise ValueError("RECAPTCHA_SECRET_KEY es requerida.")


class DevelopmentConfig(Config):
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True


class ProductionConfig(Config):
    DEBUG: bool = False
    SQLALCHEMY_ECHO: bool = False

    def __init_subclass__(cls) -> None:
        if os.getenv("SECRET_KEY") == "dev-secret-key":
            raise ValueError(
                "SECRET_KEY debe definirse explícitamente en producción."
            )


class TestingConfig(Config):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    SQLALCHEMY_ECHO: bool = False