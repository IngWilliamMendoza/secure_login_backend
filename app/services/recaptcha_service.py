import requests
from flask import current_app


class RecaptchaService:

    @staticmethod
    def verificar_token(token: str) -> tuple[bool, float, str]:
        """
        Verifica un token de reCAPTCHA V3 con Google.
        Retorna una tupla (exito, score, mensaje).
        """
        try:
            if not token:
                return False, 0.0, "Token de reCAPTCHA requerido."

            secret_key: str = current_app.config["RECAPTCHA_SECRET_KEY"]
            min_score: float = current_app.config["RECAPTCHA_MIN_SCORE"]
            verify_url: str = current_app.config["RECAPTCHA_VERIFY_URL"]

            # Enviar el token a Google para verificación
            response = requests.post(
                verify_url,
                data={
                    "secret": secret_key,
                    "response": token
                },
                timeout=5
            )

            resultado: dict = response.json()

            # Verificar si Google validó el token
            if not resultado.get("success"):
                errores: list = resultado.get("error-codes", [])
                return False, 0.0, f"Token inválido: {errores}"

            score: float = resultado.get("score", 0.0)

            # Verificar que el score supera el mínimo
            if score < min_score:
                return False, score, f"Score insuficiente: {score}"

            return True, score, "Verificación exitosa."

        except requests.Timeout:
            return False, 0.0, "Tiempo de espera agotado verificando reCAPTCHA."

        except requests.RequestException as e:
            return False, 0.0, f"Error de conexión con Google: {str(e)}"

        except Exception as e:
            return False, 0.0, f"Error inesperado: {str(e)}"