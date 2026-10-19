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
