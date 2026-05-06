from marshmallow import Schema, fields, validate, validates, validates_schema, ValidationError


class RegisterRequestSchema(Schema):
    """Schema para validar los datos de registro de un nuevo usuario."""

    email: fields.Email = fields.Email(
        required=True,
        metadata={"description": "Correo electrónico del usuario"}
    )
    username: fields.Str = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=80),
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
        validate=validate.Length(min=8, max=128),
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

    @validates("email")
    def validate_email_format(self, value: str, **kwargs) -> None:
        if len(value) > 255:
            raise ValidationError("El email no puede superar los 255 caracteres.")

    @validates_schema
    def validate_passwords_match(
        self,
        data: dict,
        **kwargs
    ) -> None:
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError(
                "Las contraseñas no coinciden.",
                field_name="confirm_password"
            )


class LoginRequestSchema(Schema):
    """Schema para validar los datos de login."""

    email: fields.Email = fields.Email(
        required=True,
        metadata={"description": "Correo electrónico registrado"}
    )
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