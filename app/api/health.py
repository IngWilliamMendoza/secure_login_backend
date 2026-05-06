from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields
from sqlalchemy import text

from app.extensions import db


blp: Blueprint = Blueprint(
    "health",
    __name__,
    url_prefix="/api/v1",
    description="Verificación del estado del servicio"
)


class HealthResponseSchema(Schema):
    status: fields.Str = fields.Str(dump_default="ok")
    service: fields.Str = fields.Str()
    database: fields.Str = fields.Str()
    version: fields.Str = fields.Str()
    environment: fields.Str = fields.Str()


@blp.route("/health")
class HealthCheck(MethodView):

    @blp.response(200, HealthResponseSchema)
    def get(self) -> dict[str, str]:
        """
        Verifica que la API y la base de datos estén operativas.

        Retorna el estado actual del servicio incluyendo
        la conectividad con PostgreSQL.
        """
        import os

        db_status: str = "ok"

        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            db_status = "error"

        return {
            "status": "ok" if db_status == "ok" else "degraded",
            "service": "secure_login",
            "database": db_status,
            "version": "1.0.0",
            "environment": os.getenv("FLASK_ENV", "development")
        }