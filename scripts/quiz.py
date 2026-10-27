"""
quiz.py
Se ejecuta por la tarde (cron en GitHub Actions).
El quiz ya se publica integrado en el toot combinado de la lección
(lección + quiz + audio + ranking), por eso este script solo se encarga
de abrir la ventana de respuestas del quiz.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import estado

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


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
    ventana = int((config.get("quiz") or {}).get("ventana_horas") or 24)
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
        # La ventana ya caducó: no se abre una de nuevo
        est.update({
            "titulo_quiz_activo": None,
            "quiz_abierto_desde": None,
            "usuarios_respondieron_hoy": [],
        })
        estado.guardar_estado(est)
        print("El quiz ya caducó. No se abre una nueva ventana.")
        return

    # Abrir la ventana del quiz (configurable, por defecto 24 horas)
    est.update({
        "titulo_quiz_activo": titulo,
        "quiz_abierto_desde": datetime.now(timezone.utc).isoformat(),
        "usuarios_respondieron_hoy": [],
    })
    estado.guardar_estado(est)

    print(f"Quiz abierto. Respuesta activa: {titulo}")


if __name__ == "__main__":
    main()
