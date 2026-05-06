from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    create_access_token,
    set_refresh_cookies,
    unset_refresh_cookies
)
from http import HTTPStatus

from app.services.auth_service import AuthService
from app.services.recaptcha_service import RecaptchaService
from app.models.user import User
from .schemas import (
    RegisterRequestSchema,
    LoginRequestSchema,
    RegisterResponseSchema,
    LoginResponseSchema,
    ErrorResponseSchema,
    RefreshResponseSchema,
    UserResponseSchema
)


blp: Blueprint = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth",
    description="Registro y autenticación de usuarios"
)


@blp.route("/register")
class Register(MethodView):

    @blp.arguments(RegisterRequestSchema)
    @blp.response(HTTPStatus.CREATED, RegisterResponseSchema)
    @blp.alt_response(HTTPStatus.CONFLICT, schema=ErrorResponseSchema)
    @blp.alt_response(HTTPStatus.UNPROCESSABLE_ENTITY, schema=ErrorResponseSchema)
    @blp.alt_response(HTTPStatus.TOO_MANY_REQUESTS, schema=ErrorResponseSchema)
    def post(self, register_data: dict) -> dict:
        """
        Registra un nuevo usuario.

        Crea una nueva cuenta con email, username y contraseña.
        La contraseña se almacena hasheada con Argon2id.
        Requiere un token de reCAPTCHA V3 válido.
        """
        # Verificar reCAPTCHA
        recaptcha_exito: bool
        score: float
        recaptcha_mensaje: str

        recaptcha_exito, score, recaptcha_mensaje = RecaptchaService.verificar_token(
            register_data["recaptcha_token"]
        )

        if not recaptcha_exito:
            abort(HTTPStatus.TOO_MANY_REQUESTS, message=recaptcha_mensaje)

        exito: bool
        mensaje: str
        usuario: User | None

        exito, mensaje, usuario = AuthService.registrar_usuario(
            email=register_data["email"],
            username=register_data["username"],
            password=register_data["password"]
        )

        if not exito:
            abort(HTTPStatus.CONFLICT, message=mensaje)

        return {
            "message": mensaje,
            "user": usuario
        }


@blp.route("/login")
class Login(MethodView):

    @blp.arguments(LoginRequestSchema)
    @blp.response(HTTPStatus.OK, LoginResponseSchema)
    @blp.alt_response(HTTPStatus.UNAUTHORIZED, schema=ErrorResponseSchema)
    @blp.alt_response(HTTPStatus.UNPROCESSABLE_ENTITY, schema=ErrorResponseSchema)
    @blp.alt_response(HTTPStatus.TOO_MANY_REQUESTS, schema=ErrorResponseSchema)
    def post(self, login_data: dict):
        """
        Autentica un usuario existente.

        Verifica las credenciales y retorna el access token
        en el body y el refresh token en una cookie HttpOnly.
        Requiere un token de reCAPTCHA V3 válido.
        """
        # Verificar reCAPTCHA
        recaptcha_exito: bool
        score: float
        recaptcha_mensaje: str

        recaptcha_exito, score, recaptcha_mensaje = RecaptchaService.verificar_token(
            login_data["recaptcha_token"]
        )

        if not recaptcha_exito:
            abort(HTTPStatus.TOO_MANY_REQUESTS, message=recaptcha_mensaje)

        exito: bool
        mensaje: str
        usuario: User | None
        access_token: str | None
        refresh_token: str | None

        exito, mensaje, usuario, access_token, refresh_token = AuthService.login_usuario(
            email=login_data["email"],
            password=login_data["password"]
        )

        if not exito:
            abort(HTTPStatus.UNAUTHORIZED, message=mensaje)

        user_schema: UserResponseSchema = UserResponseSchema()
        user_data: dict = user_schema.dump(usuario)

        response = jsonify({
            "message": mensaje,
            "access_token": access_token,
            "user": user_data
        })

        set_refresh_cookies(response, refresh_token)

        return response


@blp.route("/refresh")
class Refresh(MethodView):

    @jwt_required(refresh=True)
    @blp.response(HTTPStatus.OK, RefreshResponseSchema)
    @blp.alt_response(HTTPStatus.UNAUTHORIZED, schema=ErrorResponseSchema)
    def post(self):
        """
        Genera un nuevo access token usando el refresh token.

        El refresh token debe enviarse en la cookie HttpOnly.
        Retorna un nuevo access token.
        """
        current_user_id: str = get_jwt_identity()
        new_access_token: str = create_access_token(
            identity=current_user_id
        )

        return {"access_token": new_access_token}


@blp.route("/logout")
class Logout(MethodView):

    @jwt_required()
    @blp.response(HTTPStatus.OK, schema=ErrorResponseSchema)
    def post(self):
        """
        Cierra la sesión del usuario.

        Elimina la cookie HttpOnly del refresh token.
        """
        response = jsonify({"message": "Sesión cerrada exitosamente."})
        unset_refresh_cookies(response)
        return response


@blp.route("/me")
class Me(MethodView):

    @jwt_required()
    @blp.response(HTTPStatus.OK, UserResponseSchema)
    @blp.alt_response(HTTPStatus.UNAUTHORIZED, schema=ErrorResponseSchema)
    @blp.alt_response(HTTPStatus.NOT_FOUND, schema=ErrorResponseSchema)
    def get(self):
        """
        Retorna los datos del usuario autenticado.

        Requiere un access token válido en el header Authorization.
        """
        current_user_id: str = get_jwt_identity()
        usuario: User | None = AuthService.obtener_usuario_por_id(
            int(current_user_id)
        )

        if usuario is None:
            abort(HTTPStatus.NOT_FOUND, message="Usuario no encontrado.")

        return usuario