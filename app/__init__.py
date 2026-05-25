import os
from flask import Flask
from flask_smorest import Api
from .extensions import db, migrate, jwt, cors


def create_app(config_class: type = None) -> Flask:
    app: Flask = Flask(__name__)

    if config_class is None:
        env: str = os.getenv("FLASK_ENV", "development")
        if env == "production":
            from .config import ProductionConfig
            config_class = ProductionConfig
        elif env == "testing":
            from .config import TestingConfig
            config_class = TestingConfig
        else:
            from .config import DevelopmentConfig
            config_class = DevelopmentConfig

    app.config.from_object(config_class)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["FRONTEND_URL"]}},
        supports_credentials=app.config["CORS_SUPPORTS_CREDENTIALS"]
    )

    # Importar modelos para que Flask-Migrate los detecte
    from .models import User

    # Registrar blueprints
    api: Api = Api(app)

    from .api.health import blp as health_blp
    from .api.auth.routes import blp as auth_blp

    api.register_blueprint(health_blp)
    api.register_blueprint(auth_blp)

    return app