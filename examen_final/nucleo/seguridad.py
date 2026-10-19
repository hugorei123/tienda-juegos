"""Seguridad basica del sistema: encriptado de claves de acceso."""

import hashlib


def encriptar_clave(clave):
    """
    Convierte una clave escrita en su valor encriptado (SHA-256).
    En la base de datos NUNCA se guarda la clave en texto plano.
    """
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


def verificar_clave(clave, hash_guardado):
    """Devuelve True si la clave escrita coincide con el hash guardado."""
    return encriptar_clave(clave) == hash_guardado