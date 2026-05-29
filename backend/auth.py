"""
Principio SOLID: Single Responsibility — solo maneja login y sesiones
"""

import hashlib
import secrets
from typing import Optional

# Almacén de sesiones en memoria (token → usuario_id)
# En producción se reemplazaría por Redis o JWT
_sesiones: dict[str, dict] = {}


def hash_password(password: str) -> str:
    """Genera hash SHA-256 de la contraseña."""
    return hashlib.sha256(password.encode()).hexdigest()


def verificar_credenciales(conn, username: str, password: str) -> Optional[dict]:
    """Busca el usuario y verifica la contraseña hasheada."""
    row = conn.execute(
        "SELECT * FROM usuarios WHERE nombre = ? AND password = ?",
        (username, hash_password(password))
    ).fetchone()
    return dict(row) if row else None


def crear_sesion(usuario: dict) -> str:
    """Genera un token único y lo almacena en memoria."""
    token = secrets.token_hex(32)
    _sesiones[token] = {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "rol": usuario["rol"],
    }
    return token


def obtener_sesion(token: str) -> Optional[dict]:
    """Retorna los datos del usuario asociado al token."""
    return _sesiones.get(token)


def cerrar_sesion(token: str):
    """Elimina el token de la sesión activa."""
    _sesiones.pop(token, None)