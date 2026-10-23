"""
niveles.py
Gestiona la progresión de niveles: qué letras están desbloqueadas
en un día dado, y qué nivel requiere un título concreto.
"""
from src.morse import letras_usadas


def letras_desbloqueadas(config: dict, nivel_actual: int) -> set:
    """Devuelve el conjunto de letras desbloqueadas hasta el nivel dado (incluido)."""
    letras = set()
    for nivel in config["niveles"]:
        if nivel["id"] <= nivel_actual:
            letras.update(nivel["letras"])
    return letras


def nivel_requerido(texto: str, config: dict) -> int:
    """Calcula el nivel mínimo necesario para poder traducir este texto,
    es decir, el primer nivel en el que todas sus letras ya están desbloqueadas.
    """
    necesarias = letras_usadas(texto)
    max_nivel = 0
    for nivel in sorted(config["niveles"], key=lambda n: n["id"]):
        max_nivel = nivel["id"]
        desbloqueadas = letras_desbloqueadas(config, max_nivel)
        if necesarias.issubset(desbloqueadas):
            return nivel["id"]
    # Si ningún nivel cubre todas las letras, se requiere el último nivel definido
    return max_nivel


def letras_nuevas_de_hoy(config: dict, nivel_actual: int, letras_enseñadas: set = None) -> list:
    """Letras que se introducen en el nivel actual (para la lección).

    Si se pasa `letras_enseñadas`, solo devuelve las del nivel actual que
    aún no se han enseñado, para que los niveles avancen sin repetir letras.
    """
    nuevas = []
    for nivel in sorted(config["niveles"], key=lambda n: n["id"]):
        if nivel["id"] != nivel_actual:
            continue
        sin_aprender = (
            nivel["letras"] if letras_enseñadas is None
            else [l for l in nivel["letras"] if l.upper() not in letras_enseñadas]
        )
        nuevas.extend(sin_aprender)
    return nuevas


def _letras_nivel(config: dict, nivel_id: int) -> set:
    """Unión de letras necesarias hasta el nivel indicado (incluido)."""
    necesarias = set()
    for nivel in sorted(config["niveles"], key=lambda n: n["id"]):
        if nivel["id"] <= nivel_id:
            necesarias.update(l.upper() for l in nivel["letras"])
    return necesarias


def nivel_completo(config: dict, nivel_actual: int, letras_enseñadas: set) -> bool:
    """Indica si ya se han enseñado todas las letras necesarias hasta el nivel actual."""
    return _letras_nivel(config, nivel_actual).issubset({l.upper() for l in letras_enseñadas})


def siguiente_nivel(config: dict, letras_enseñadas: set) -> int:
    """Devuelve el primer nivel (en orden de ids) que aún no está completo,
    es decir, el nivel al que toca enseñar ahora mismo.
    """
    ids = sorted({n["id"] for n in config["niveles"]})
    for lid in ids:
        if not _letras_nivel(config, lid).issubset({l.upper() for l in letras_enseñadas}):
            return lid
    # Todos los niveles completados: se queda en el último
    return ids[-1]
