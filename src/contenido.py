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


def _tiene_nyñ(texto: str) -> bool:
    return "Ñ" in texto.upper() or "ñ" in texto


def _tiene_acentos(texto: str) -> bool:
    # Si al quitar los acentos el texto cambia, es que tenía acentos/diacríticos
    normalizado = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    return sin_acentos != texto


def _tiene_puntuacion(texto: str) -> bool:
    # Solo permitimos letras, números y espacios
    return bool(re.search(r"[^A-Za-z0-9 ]", texto))


def titulo_es_apto(titulo: str, config: dict) -> bool:
    cfg = config["contenido"]
    if cfg.get("excluir_nyñ") and _tiene_nyñ(titulo):
        return False
    if cfg.get("excluir_acentos", True) and _tiene_acentos(titulo):
        return False
    if cfg.get("excluir_puntuacion") and _tiene_puntuacion(titulo):
        return False
    longitud = len(titulo.replace(" ", ""))
    if not (cfg["min_longitud"] <= longitud <= cfg["max_longitud"]):
        return False
    return es_valido(titulo)


def _decadas_a_filtrar(config: dict) -> list:
    return [int(d) for d in (config.get("contenido") or {}).get("decadas") or []]


def _en_decada(anio: int, decadas: list) -> bool:
    if not decadas:
        return True
    decima = (anio // 10) * 10
    return decima in decadas


def _nombres_keywords(peli: dict) -> set:
    """Devuelve los nombres (lowercase) de los keywords de una película de TMDb."""
    raw = peli.get("keywords") or {}
    kws = raw.get("keyword") if isinstance(raw, dict) else raw
    nombres = set()
    for k in kws or []:
        if isinstance(k, dict):
            nombre = str(k.get("name") or "").strip().lower()
            if nombre:
                nombres.add(nombre)
    return nombres


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
        resp = requests.get(f"{TMDB_API_BASE}/discover/movie", params=params, timeout=15)
        resp.raise_for_status()
        resultados = resp.json().get("results", [])

        for peli in resultados:
            titulo = peli.get("title", "").strip()
            if not titulo or not titulo_es_apto(titulo, config):
                continue
            candidatos.append((titulo, peli))

    # quitar duplicados manteniendo el primer título por cada uno
    vistos = set()
    unicos = []
    for titulo, peli in candidatos:
        clave = titulo.upper()
        if clave in vistos:
            continue
        vistos.add(clave)
        unicos.append((titulo, peli))

    # filtrar por palabras clave ("friki/culto") y décadas, cuando estén configuradas
    palabras_clave = [
        str(p).strip().lower() for p in (cfg.get("palabras_clave") or []) if str(p).strip()
    ]
    decadas = _decadas_a_filtrar(config)

    filtrados = []
    for titulo, peli in unicos:
        if palabras_clave and not any(p in _nombres_keywords(peli) for p in palabras_clave):
            continue
        release_date = str(peli.get("release_date") or "")
        try:
            anio = int(release_date[:4])
        except ValueError:
            anio = None
        if anio is not None and not _en_decada(anio, decadas):
            continue
        filtrados.append(titulo)

    return filtrados
