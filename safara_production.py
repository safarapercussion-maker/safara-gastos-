"""Comprueba que la versión definitiva apunta al proyecto Supabase previsto."""

import re
from urllib.parse import unquote, urlsplit


PROYECTO_PRUEBAS = "grqfhdmnymybulfeyyrf"


def conexion_de_produccion_valida(database_url: str, proyecto: str) -> bool:
    """Admite conexiones directas y el pooler de sesión oficial de Supabase."""
    if not re.fullmatch(r"[a-z0-9]{20}", proyecto) or proyecto == PROYECTO_PRUEBAS:
        return False
    try:
        url = urlsplit(database_url)
        if url.scheme not in {"postgres", "postgresql", "postgresql+psycopg"}:
            return False
        if url.port not in (None, 5432) or url.path != "/postgres":
            return False
        usuario = unquote(url.username or "")
        if url.hostname == f"db.{proyecto}.supabase.co":
            return usuario == "postgres"
        return bool(
            url.hostname
            and url.hostname.endswith(".pooler.supabase.com")
            and usuario == f"postgres.{proyecto}"
        )
    except ValueError:
        return False
