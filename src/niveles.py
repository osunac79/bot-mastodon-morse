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


def letras_nuevas_de_hoy(config: dict, nivel_actual: int) -> list:
    """Letras que se introducen exactamente en el nivel actual (para la lección)."""
    for nivel in config["niveles"]:
        if nivel["id"] == nivel_actual:
            return nivel["letras"]
    return []
