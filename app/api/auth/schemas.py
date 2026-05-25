from flask import current_app
from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    validates_schema,
    pre_load,
    ValidationError
)
from email_validator import validate_email, EmailNotValidError


class BaseEmailSchema(Schema):
    """Schema base con validación de email reutilizable."""

    email: fields.Str = fields.Str(
        required=True,
        metadata={"description": "Correo electrónico"}
    )

    @pre_load
    def normalizar_email(self, data: dict, **kwargs) -> dict:
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].strip().lower()
        return data

    @validates("email")
    def validate_email_format(self, value: str, **kwargs) -> None:
        try:
            check: bool = current_app.config.get(
                "EMAIL_CHECK_DELIVERABILITY", False
            )
            validate_email(value, check_deliverability=check)
        except EmailNotValidError as e:
            raise ValidationError(str(e))


class RegisterRequestSchema(BaseEmailSchema):
    """Schema para validar los datos de registro de un nuevo usuario."""

    username: fields.Str = fields.Str(
        required=True,
        validate=[
            validate.Length(
                min=3,
                max=30,
                error="El username debe tener entre 3 y 30 caracteres."
            ),
            validate.Regexp(
                r"^[a-zA-Z0-9_]+$",
                error="El username solo puede contener letras, números y guiones bajos."
            )
        ],
        metadata={"description": "Nombre de usuario único"}
    )
    password: fields.Str = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(
            min=8,
            max=16,
            error="La contraseña debe tener entre 8 y 16 caracteres."
        ),
        metadata={"description": "Contraseña — mínimo 8 caracteres"}
    )
    confirm_password: fields.Str = fields.Str(
        required=True,
        load_only=True,
        metadata={"description": "Confirmación de contraseña"}
    )
    recaptcha_token: fields.Str = fields.Str(
        required=True,
        load_only=True,
        metadata={"description": "Token de reCAPTCHA V3 generado por el frontend"}
    )

    @validates("username")
    def validate_username(self, value: str, **kwargs) -> None:
        if value.startswith("_") or value.endswith("_"):
            raise ValidationError(
                "El username no puede empezar ni terminar con guión bajo."
            )
        if value.isdigit():
            raise ValidationError("El username no puede ser solo números.")
        palabras_reservadas: list[str] = [
            "admin", "root", "system", "null", "undefined"
        ]
        if value.lower() in palabras_reservadas:
            raise ValidationError("Este username no está disponible.")

    @validates("password")
    def validate_password_strength(self, value: str, **kwargs) -> None:
        if not any(c.isupper() for c in value):
            raise ValidationError(
                "La contraseña debe contener al menos una mayúscula."
            )
        if not any(c.islower() for c in value):
            raise ValidationError(
                "La contraseña debe contener al menos una minúscula."
            )
        if not any(c.isdigit() for c in value):
            raise ValidationError(
                "La contraseña debe contener al menos un número."
            )
        caracteres_especiales: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in caracteres_especiales for c in value):
            raise ValidationError(
                "La contraseña debe contener al menos un carácter especial."
            )
        if " " in value:
            raise ValidationError(
                "La contraseña no puede contener espacios."
            )
        passwords_comunes: list[str] = [
            "password123", "12345678", "qwerty123",
            "admin123", "letmein1"
        ]
        if value.lower() in passwords_comunes:
            raise ValidationError("Esta contraseña es demasiado común.")

    @validates_schema
    def validate_passwords_match(self, data: dict, **kwargs) -> None:
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError(
                "Las contraseñas no coinciden.",
                field_name="confirm_password"
            )


class LoginRequestSchema(BaseEmailSchema):
    """Schema para validar los datos de login."""

    password: fields.Str = fields.Str(
        required=True,
        load_only=True,
        metadata={"description": "Contraseña del usuario"}
    )
    recaptcha_token: fields.Str = fields.Str(
        required=True,
        load_only=True,
        metadata={"description": "Token de reCAPTCHA V3 generado por el frontend"}
    )


class UserResponseSchema(Schema):
    """Schema para serializar los datos del usuario en la respuesta."""

    id: fields.Int = fields.Int(
        dump_only=True,
        metadata={"description": "ID único del usuario"}
    )
    email: fields.Email = fields.Email(
        dump_only=True,
        metadata={"description": "Correo electrónico del usuario"}
    )
    username: fields.Str = fields.Str(
        dump_only=True,
        metadata={"description": "Nombre de usuario"}
    )
    is_active: fields.Bool = fields.Bool(
        dump_only=True,
        metadata={"description": "Estado de la cuenta"}
    )
    is_verified: fields.Bool = fields.Bool(
        dump_only=True,
        metadata={"description": "Si el email fue verificado"}
    )
    created_at: fields.DateTime = fields.DateTime(
        dump_only=True,
        format="iso",
        metadata={"description": "Fecha de registro en formato ISO 8601"}
    )
    last_login: fields.DateTime = fields.DateTime(
        dump_only=True,
        allow_none=True,
        format="iso",
        metadata={"description": "Último login en formato ISO 8601"}
    )


class RegisterResponseSchema(Schema):
    """Schema para la respuesta del endpoint de registro."""

    message: fields.Str = fields.Str(
        metadata={"description": "Mensaje de resultado"}
    )
    user: fields.Nested = fields.Nested(
        UserResponseSchema,
        metadata={"description": "Datos del usuario registrado"}
    )


class LoginResponseSchema(Schema):
    """Schema para la respuesta del endpoint de login."""

    message: fields.Str = fields.Str(
        metadata={"description": "Mensaje de resultado"}
    )
    access_token: fields.Str = fields.Str(
        metadata={"description": "JWT access token"}
    )
    user: fields.Nested = fields.Nested(
        UserResponseSchema,
        metadata={"description": "Datos del usuario autenticado"}
    )


class ErrorResponseSchema(Schema):
    """Schema para respuestas de error."""

    message: fields.Str = fields.Str(
        metadata={"description": "Descripción del error"}
    )
    errors: fields.Dict = fields.Dict(
        keys=fields.Str(),
        values=fields.List(fields.Str()),
        load_default=None,
        metadata={"description": "Detalle de errores de validación por campo"}
    )


class RefreshResponseSchema(Schema):
    """Schema para la respuesta del endpoint de refresh."""

    access_token: fields.Str = fields.Str(
        metadata={"description": "Nuevo access token generado"}
    )