"""
estado.py
Lectura/escritura de los ficheros JSON que guardan el estado del bot
entre ejecuciones de GitHub Actions. Todo vive dentro del propio repo
(se hace commit tras cada ejecución), sin base de datos externa.
"""
import json
from pathlib import Path
from datetime import date

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CONTENIDO_USADO = DATA_DIR / "contenido_usado.json"
ESTADO = DATA_DIR / "estado.json"
RANKING = DATA_DIR / "ranking.json"


def _leer(path: Path, por_defecto):
    if not path.exists():
        return por_defecto
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _escribir(path: Path, datos):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2, sort_keys=True)


# ---------- contenido ya usado (para no repetir títulos) ----------

def cargar_contenido_usado() -> list:
    return _leer(CONTENIDO_USADO, [])


def marcar_como_usado(titulo: str):
    usados = cargar_contenido_usado()
    if titulo not in usados:
        usados.append(titulo)
        _escribir(CONTENIDO_USADO, usados)


# ---------- estado del día (nivel actual, quiz activo, etc.) ----------

def cargar_estado() -> dict:
    return _leer(ESTADO, {
        "nivel_actual": 1,
        "fecha_leccion": None,
        "titulo_leccion": None,
        "titulo_quiz_activo": None,
        "quiz_abierto_desde": None,
        "usuarios_respondieron_hoy": [],
    })


def guardar_estado(estado: dict):
    _escribir(ESTADO, estado)


# ---------- ranking ----------

def cargar_ranking() -> dict:
    return _leer(RANKING, {"total": {}, "hoy": {}})


def guardar_ranking(ranking: dict):
    _escribir(RANKING, ranking)


def anotar_punto(usuario: str):
    ranking = cargar_ranking()
    ranking["hoy"][usuario] = ranking["hoy"].get(usuario, 0) + 1
    ranking["total"][usuario] = ranking["total"].get(usuario, 0) + 1
    guardar_ranking(ranking)


def top_ranking(ranking_parcial: dict, n: int = 3) -> list:
    """Devuelve los [n] usuarios con más puntos, como lista de (usuario, puntos)."""
    return sorted(ranking_parcial.items(), key=lambda x: x[1], reverse=True)[:n]


def cerrar_dia_y_resetear_ranking_diario():
    ranking = cargar_ranking()
    ranking_de_ayer = ranking["hoy"]
    ranking["hoy"] = {}
    guardar_ranking(ranking)
    return ranking_de_ayer
