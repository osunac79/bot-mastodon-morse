"""
mastodon_client.py
Envoltorio sencillo sobre Mastodon.py para publicar toots (con o sin
audio adjunto) y leer menciones nuevas.
Requiere las variables de entorno:
  MASTODON_ACCESS_TOKEN
  MASTODON_BASE_URL (o se toma de config.yaml -> mastodon.base_url)
"""
import os
from mastodon import Mastodon


def _get(obj, clave, defecto=None):
    """Compatibilidad entre diccionarios y objetos de Mastodon.py."""
    if isinstance(obj, dict):
        return obj.get(clave, defecto)
    return getattr(obj, clave, defecto)


def conectar(config: dict) -> Mastodon:
    token = os.environ.get("MASTODON_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("Falta la variable de entorno MASTODON_ACCESS_TOKEN")
    base_url = os.environ.get("MASTODON_BASE_URL") or config["mastodon"]["base_url"]
    return Mastodon(access_token=token, api_base_url=base_url)


def publicar_toot(mastodon: Mastodon, texto: str, ruta_audio: str = None) -> dict:
    media_ids = None
    if ruta_audio:
        media = mastodon.media_post(ruta_audio, description="Audio en código morse")
        media_ids = [media["id"]]
    return mastodon.status_post(texto, media_ids=media_ids)


def leer_menciones_nuevas(mastodon: Mastodon, desde_id: str = None) -> list:
    """Devuelve las notificaciones de tipo 'mention' más recientes que desde_id."""
    notifs = mastodon.notifications(types=["mention"], since_id=desde_id)
    return list(reversed(notifs))  # de más antigua a más reciente


def id_mencion(notif) -> str:
    """Devuelve el ID de la notificación (no el del status) — se usa como cursor."""
    status = _get(notif, "status")
    return str(_get(notif, "id") or _get(status, "id") or "")


def id_status(status) -> str:
    """Devuelve el ID interno de un status (para responder sobre él)."""
    return str(_get(status, "id") or "")


def contenido_mencion(notif) -> str:
    """Devuelve el contenido HTML del status asociado a la notificación."""
    status = _get(notif, "status") or {}
    return str(_get(status, "content") or "")


def contenido_status(status) -> str:
    """Devuelve el contenido HTML de un status (o de un objeto status-like)."""
    return str(_get(status, "content") or "")


def cuenta_mencion(notif) -> str:
    """Devuelve el acct del usuario que hizo la mención."""
    status = _get(notif, "status") or {}
    cuenta = _get(status, "account") or {}
    return str(_get(cuenta, "acct") or _get(cuenta, "username") or "")
