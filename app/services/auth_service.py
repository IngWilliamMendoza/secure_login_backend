from datetime import datetime, timezone
from typing import Optional
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import db, argon2
from app.models.user import User


class AuthService:

    @staticmethod
    def registrar_usuario(
        email: str,
        username: str,
        password: str
    ) -> tuple[bool, str, Optional[User]]:
        """
        Registra un nuevo usuario en la base de datos.
        Retorna una tupla (exito, mensaje, usuario).
        """
        try:
            usuario_existente: Optional[User] = db.session.execute(
                select(User).filter_by(email=email)
            ).scalar_one_or_none()

            if usuario_existente is not None:
                return False, "El email ya está registrado.", None

            username_existente: Optional[User] = db.session.execute(
                select(User).filter_by(username=username)
            ).scalar_one_or_none()

            if username_existente is not None:
                return False, "El nombre de usuario ya está en uso.", None

            password_hash: str = argon2.hash(password)

            nuevo_usuario: User = User(
                email=email,
                username=username,
                password_hash=password_hash
            )

            db.session.add(nuevo_usuario)
            db.session.commit()

            return True, "Usuario registrado exitosamente.", nuevo_usuario

        except IntegrityError:
            db.session.rollback()
            return False, "Error de integridad en la base de datos.", None

        except Exception as e:
            db.session.rollback()
            return False, f"Error inesperado: {str(e)}", None

    @staticmethod
    def login_usuario(
        email: str,
        password: str
    ) -> tuple[bool, str, Optional[User], Optional[str], Optional[str]]:
        """
        Verifica las credenciales de un usuario.
        Retorna una tupla (exito, mensaje, usuario, access_token, refresh_token).
        """
        try:
            usuario: Optional[User] = db.session.execute(
                select(User).filter_by(email=email)
            ).scalar_one_or_none()

            if usuario is None:
                return False, "Credenciales inválidas.", None, None, None

            if not usuario.is_active:
                return False, "La cuenta está desactivada.", None, None, None

            argon2.verify(usuario.password_hash, password)

            # Actualizar último login
            usuario.last_login = datetime.now(timezone.utc)
            db.session.commit()

            # Generar tokens — el subject es el id del usuario como string
            access_token: str = create_access_token(
                identity=str(usuario.id)
            )
            refresh_token: str = create_refresh_token(
                identity=str(usuario.id)
            )

            return True, "Login exitoso.", usuario, access_token, refresh_token

        except VerifyMismatchError:
            return False, "Credenciales inválidas.", None, None, None

        except (VerificationError, InvalidHashError):
            db.session.rollback()
            return False, "Error al verificar credenciales.", None, None, None

        except Exception as e:
            db.session.rollback()
            return False, f"Error inesperado: {str(e)}", None, None, None

    @staticmethod
    def obtener_usuario_por_id(
        user_id: int
    ) -> Optional[User]:
        """
        Retorna un usuario por su ID o None si no existe.
        """
        return db.session.get(User, user_id)

    @staticmethod
    def obtener_usuario_por_email(
        email: str
    ) -> Optional[User]:
        """
        Retorna un usuario por su email o None si no existe.
        """
        return db.session.execute(
            select(User).filter_by(email=email)
        ).scalar_one_or_none()