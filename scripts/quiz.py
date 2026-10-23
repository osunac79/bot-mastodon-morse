"""
quiz.py
Se ejecuta por la tarde (cron en GitHub Actions).
1. Comprueba que el quiz sigue abierto (ventana de respuestas).
2. Elige un título (puede ser el mismo de la lección, o uno nuevo apto
   para el nivel actual) como reto del quiz.
3. Genera el audio en morse y lo publica.
4. Guarda cuál es la respuesta correcta activa, para que
   revisar_menciones.py pueda comprobar las respuestas.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import estado, mastodon_client, audio
from src.morse import texto_a_morse

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"
AUDIO_TMP = Path("/tmp/quiz_morse")


def cargar_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _quiz_caducado(est: dict, config: dict) -> bool:
    """Comprueba si la ventana del quiz ya ha caducado.

    Si todavía no hay ventana registrada (`quiz_abierto_desde` vacío) no ha
    caducado: es el momento de abrir el quiz.
    """
    abierta_desde = est.get("quiz_abierto_desde")
    if not abierta_desde:
        return False
    ventana = int((config.get("quiz") or {}).get("ventana_horas") or 6)
    abierta = datetime.fromisoformat(str(abierta_desde).replace("Z", "+00:00"))
    return datetime.now(timezone.utc) > abierta + timedelta(hours=ventana)


def main():
    config = cargar_config()
    est = estado.cargar_estado()

    titulo = est.get("titulo_leccion")
    if not titulo:
        raise RuntimeError(
            "No hay título de lección guardado para hoy. "
            "¿Se ejecutó leccion.py antes que quiz.py?"
        )

    if _quiz_caducado(est, config):
        # La ventana ya caducó: no se publica ni se aceptan respuestas.
        est.update({
            "titulo_quiz_activo": None,
            "quiz_abierto_desde": None,
            "usuarios_respondieron_hoy": [],
        })
        estado.guardar_estado(est)
        print("El quiz ya caducó. No se publica una nueva respuesta.")
        return

    morse = texto_a_morse(titulo)

    wpm_cfg = config["audio"]
    nivel = est.get("nivel_actual", 1)
    wpm = wpm_cfg.get("wpm_por_nivel") or {}
    wpm = wpm.get(nivel, wpm_cfg.get("wpm", 15))

    muestras = audio.morse_a_audio(morse, wpm=wpm, frecuencia_hz=wpm_cfg.get("frecuencia_hz", 700))
    ruta_audio = AUDIO_TMP.with_suffix(f".{wpm_cfg.get('formato', 'mp3')}")
    audio.guardar_audio(muestras, str(ruta_audio), formato=wpm_cfg.get("formato", "mp3"))

    texto_toot = (
        "🎧🔤 **¡QUIZ DE MORSE!** 🎧\n\n"
        "Dale al play, descifra el título de la peli y respóndeme por aquí 👇\n\n"
        "🎬 Es una peli que ya hemos visto en lecciones anteriores, ¡a ver esos oídos! 👂\n\n"
        f"⏰ Tienes hasta dentro de {config['quiz']['ventana_horas']}h.\n\n"
        "#AprendeMorse #Cine #Quiz"
    )

    mastodon = mastodon_client.conectar(config)
    mastodon_client.publicar_toot(mastodon, texto_toot, ruta_audio=str(ruta_audio))

    est.update({
        "titulo_quiz_activo": titulo,
        "quiz_abierto_desde": datetime.now(timezone.utc).isoformat(),
        "usuarios_respondieron_hoy": [],
    })
    estado.guardar_estado(est)

    print(f"Quiz publicado. Respuesta activa: {titulo}")


if __name__ == "__main__":
    main()
