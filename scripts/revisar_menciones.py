"""
revisar_menciones.py
Se ejecuta cada 15-30 min (cron en GitHub Actions).
Revisa menciones nuevas, compara la respuesta contra el título activo
del quiz (normalizando mayúsculas/espacios) y anota puntos en el ranking.
Cada usuario solo puede puntuar una vez por día.
"""
import sys
from pathlib import Path

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
    import re
    contenido = status["content"]
    return re.sub(r"<[^>]+>", " ", contenido)


def main():
    config = cargar_config()
    est = estado.cargar_estado()

    titulo_activo = est.get("titulo_quiz_activo")
    if not titulo_activo:
        print("No hay quiz activo ahora mismo. Nada que revisar.")
        return

    respuesta_correcta = normalizar_respuesta(titulo_activo)
    ya_respondieron = set(est.get("usuarios_respondieron_hoy", []))

    mastodon = mastodon_client.conectar(config)
    ultimo_id = leer_ultimo_id()
    menciones = mastodon_client.leer_menciones_nuevas(mastodon, desde_id=ultimo_id)

    nuevo_ultimo_id = ultimo_id
    for notif in menciones:
        status = notif["status"]
        usuario = status["account"]["acct"]
        nuevo_ultimo_id = status["id"]

        if usuario in ya_respondieron:
            continue

        texto_respuesta = normalizar_respuesta(extraer_texto_plano(status))
        if respuesta_correcta in texto_respuesta:
            estado.anotar_punto(usuario)
            ya_respondieron.add(usuario)
            mastodon.status_reply(
                status,
                f"✅ @{usuario} ¡correcto! Punto anotado 🎉",
            )

    est["usuarios_respondieron_hoy"] = list(ya_respondieron)
    estado.guardar_estado(est)

    if nuevo_ultimo_id:
        guardar_ultimo_id(nuevo_ultimo_id)

    print(f"Revisadas {len(menciones)} menciones. Aciertos nuevos: {len(ya_respondieron)}")


if __name__ == "__main__":
    main()
