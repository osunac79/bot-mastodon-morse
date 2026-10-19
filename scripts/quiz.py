"""
quiz.py
Se ejecuta por la tarde (cron en GitHub Actions).
1. Elige un título (puede ser el mismo de la lección, o uno nuevo apto
   para el nivel actual) como reto del quiz.
2. Genera el audio en morse y lo publica.
3. Guarda cuál es la respuesta correcta activa, para que
   revisar_menciones.py pueda comprobar las respuestas.
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import estado, mastodon_client, audio
from src.morse import texto_a_morse

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"
AUDIO_TMP = Path("/tmp/quiz_morse.mp3")


def cargar_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = cargar_config()
    est = estado.cargar_estado()

    titulo = est.get("titulo_leccion")
    if not titulo:
        raise RuntimeError(
            "No hay título de lección guardado para hoy. "
            "¿Se ejecutó leccion.py antes que quiz.py?"
        )

    morse = texto_a_morse(titulo)

    wpm_cfg = config["audio"]
    nivel = est.get("nivel_actual", 1)
    wpm = wpm_cfg.get("wpm_por_nivel", {}).get(nivel, wpm_cfg["wpm"])

    muestras = audio.morse_a_audio(morse, wpm=wpm, frecuencia_hz=wpm_cfg["frecuencia_hz"])
    audio.guardar_audio(muestras, str(AUDIO_TMP), formato=wpm_cfg["formato"])

    texto_toot = (
        "🎧🔤 **¡QUIZ DE MORSE!** 🎧\n\n"
        "Dale al play, descifra el título de la peli y respóndeme por aquí 👇\n\n"
        "🎬 Es una peli que ya hemos visto en lecciones anteriores, ¡a ver esos oídos! 👂\n\n"
        f"⏰ Tienes hasta dentro de {config['quiz']['ventana_horas']}h.\n\n"
        "#AprendeMorse #Cine #Quiz"
    )

    mastodon = mastodon_client.conectar(config)
    mastodon_client.publicar_toot(mastodon, texto_toot, ruta_audio=str(AUDIO_TMP))

    est.update({
        "titulo_quiz_activo": titulo,
        "quiz_abierto_desde": datetime.now(timezone.utc).isoformat(),
        "usuarios_respondieron_hoy": [],
    })
    estado.guardar_estado(est)

    print(f"Quiz publicado. Respuesta activa: {titulo}")


if __name__ == "__main__":
    main()
