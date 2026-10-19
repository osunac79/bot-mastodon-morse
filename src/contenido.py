"""
contenido.py
Obtiene títulos de películas desde TMDb según la configuración
(géneros, palabras clave, décadas) y los filtra para que sean
aptos para el bot de morse (sin Ñ, acentos ni puntuación).
"""
import os
import re
import unicodedata
import requests

from src.morse import es_valido

TMDB_API_BASE = "https://api.themoviedb.org/3"

# Mapa de nombres de género (config.yaml) a IDs de género de TMDb
GENEROS_TMDB = {
    "Science Fiction": 878,
    "Horror": 27,
    "Fantasy": 14,
    "Action": 28,
    "Comedy": 35,
    "Animation": 16,
    "Thriller": 53,
}


def _tiene_nyñ_o_acentos(texto: str) -> bool:
    if "Ñ" in texto.upper() or "ñ" in texto:
        return True
    # Si al quitar los acentos el texto cambia, es que tenía acentos/diacríticos
    normalizado = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    return sin_acentos != texto


def _tiene_puntuacion(texto: str) -> bool:
    # Solo permitimos letras, números y espacios
    return bool(re.search(r"[^A-Za-z0-9 ]", texto))


def titulo_es_apto(titulo: str, config: dict) -> bool:
    cfg = config["contenido"]
    if cfg.get("excluir_nyñ") and _tiene_nyñ_o_acentos(titulo):
        return False
    if cfg.get("excluir_puntuacion") and _tiene_puntuacion(titulo):
        return False
    longitud = len(titulo.replace(" ", ""))
    if not (cfg["min_longitud"] <= longitud <= cfg["max_longitud"]):
        return False
    return es_valido(titulo)


def buscar_candidatos_tmdb(config: dict, paginas: int = 3) -> list:
    """Consulta el endpoint /discover/movie de TMDb con los filtros de config.yaml.
    Requiere la variable de entorno TMDB_API_KEY.
    Devuelve una lista de títulos (strings) que pasan el filtro de aptitud.
    """
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta la variable de entorno TMDB_API_KEY. "
            "Consigue una clave gratuita en https://www.themoviedb.org/settings/api"
        )

    cfg = config["contenido"]
    genero_ids = [str(GENEROS_TMDB[g]) for g in cfg["generos"] if g in GENEROS_TMDB]

    candidatos = []
    for pagina in range(1, paginas + 1):
        params = {
            "api_key": api_key,
            "with_genres": ",".join(genero_ids),
            "sort_by": "popularity.desc",
            "page": pagina,
            "include_adult": "false",
        }
        if cfg.get("decadas"):
            # TMDb no filtra por década directamente; se podría iterar por rango de años.
            # De momento dejamos preparado el hueco para futuras mejoras.
            pass

        resp = requests.get(f"{TMDB_API_BASE}/discover/movie", params=params, timeout=15)
        resp.raise_for_status()
        resultados = resp.json().get("results", [])

        for peli in resultados:
            titulo = peli.get("title", "").strip()
            if titulo and titulo_es_apto(titulo, config):
                candidatos.append(titulo)

    # quitar duplicados manteniendo orden
    vistos = set()
    unicos = []
    for t in candidatos:
        if t.upper() not in vistos:
            vistos.add(t.upper())
            unicos.append(t)
    return unicos
