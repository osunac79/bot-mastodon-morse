"""
revisar_menciones.py
Se ejecuta cada 20 min (cron en GitHub Actions).
Revisa menciones nuevas, compara la respuesta contra el título activo
del quiz (normalizando mayúsculas/espacios) y anota puntos en el ranking.
Cada usuario solo puede puntuar una vez por día.
"""
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import estado, mastodon_client
from src.morse import normalizar_respuesta

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"
ULTIMO_ID_PATH = Path(__file__).resolve().parent.parent / "data" / "ultimo_mention_id.txt"


def cargar_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def leer_ultimo_id():
    if ULTIMO_ID_PATH.exists():
        return ULTIMO_ID_PATH.read_text().strip() or None
    return None


def guardar_ultimo_id(mention_id):
    ULTIMO_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
    ULTIMO_ID_PATH.write_text(str(mention_id))


def extraer_texto_plano(status) -> str:
    # Mastodon.py ya limpia el HTML básico en status['content'] si se usa
    # una librería de parseo; aquí hacemos un strip simple de etiquetas.
    contenido = mastodon_client.contenido_status(status)
    return re.sub(r"<[^>]+>", " ", contenido)


def _fecha_mencion(notif) -> datetime:
    status = mastodon_client._get(notif, "status") or {}
    raw = status.get("created_at") if isinstance(status, dict) else getattr(status, "created_at", None)
    if not raw:
        raw = mastodon_client._get(notif, "created_at")
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _es_mencion_valida(notif, desde: datetime, hasta: datetime) -> bool:
    """True si la mención pertenece a la ventana del quiz."""
    if desde is None or hasta is None:
        return True
    fecha = _fecha_mencion(notif)
    return desde <= fecha <= hasta


def main():
    config = cargar_config()
    est = estado.cargar_estado()

    titulo_activo = est.get("titulo_quiz_activo")
    if not titulo_activo:
        print("No hay quiz activo ahora mismo. Nada que revisar.")
        return

    abierta_desde = est.get("quiz_abierto_desde")
    if abierta_desde:
        abierta = datetime.fromisoformat(str(abierta_desde).replace("Z", "+00:00"))
        ventana = int((config.get("quiz") or {}).get("ventana_horas") or 6)
        if datetime.now(timezone.utc) > abierta + timedelta(hours=ventana):
            # El quiz caducó: se limpia la respuesta activa.
            est.update({
                "titulo_quiz_activo": None,
                "quiz_abierto_desde": None,
                "usuarios_respondieron_hoy": [],
            })
            estado.guardar_estado(est)
            print("El quiz ya caducó. Se limpia la respuesta activa.")
            return

    desde = datetime.fromisoformat(str(abierta_desde).replace("Z", "+00:00")) if abierta_desde else None
    hasta = datetime.now(timezone.utc)

    respuesta_correcta = normalizar_respuesta(
        titulo_activo,
        quitar_articulo=not bool((config.get("quiz") or {}).get("incluir_articulo_the", True)),
    )
    ya_respondieron = set(est.get("usuarios_respondieron_hoy") or [])

    mastodon = mastodon_client.conectar(config)
    ultimo_id = leer_ultimo_id()
    menciones = mastodon_client.leer_menciones_nuevas(mastodon, desde_id=ultimo_id)

    nuevo_ultimo_id = ultimo_id
    aciertos_nuevos = 0
    for notif in menciones:
        id_notif = mastodon_client.id_mencion(notif)
        if id_notif:
            nuevo_ultimo_id = id_notif

        if not id_notif:
            continue
        if not _es_mencion_valida(notif, desde, hasta):
            continue

        usuario = mastodon_client.cuenta_mencion(notif)
        if usuario in ya_respondieron:
            continue

        status = mastodon_client._get(notif, "status") or {}
        texto_respuesta = normalizar_respuesta(
            extraer_texto_plano(status),
            quitar_articulo=not bool((config.get("quiz") or {}).get("incluir_articulo_the", True)),
        )
        if texto_respuesta == respuesta_correcta:
            estado.anotar_punto(usuario)
            ya_respondieron.add(usuario)
            aciertos_nuevos += 1
            mastodon.status_reply(
                mastodon_client.id_status(status),
                f"✅ @{usuario} ¡correcto! Punto anotado 🎉",
            )

    est["usuarios_respondieron_hoy"] = list(ya_respondieron)
    estado.guardar_estado(est)

    if nuevo_ultimo_id:
        guardar_ultimo_id(nuevo_ultimo_id)

    print(f"Revisadas {len(menciones)} menciones. Aciertos nuevos: {aciertos_nuevos}")


if __name__ == "__main__":
    main()
