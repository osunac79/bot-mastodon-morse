"""
leccion.py
Se ejecuta por la mañana (cron en GitHub Actions).
1. Calcula el nivel/letras nuevas de hoy.
2. Elige un título de película apto para ese nivel.
3. Publica el toot de la lección (con rankings de ayer si los hay).
4. Guarda el título elegido como "respuesta del quiz de hoy".
"""
import sys
import random
from pathlib import Path
from datetime import date

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import estado, contenido, mastodon_client, niveles
from src.niveles import nivel_requerido, letras_nuevas_de_hoy, siguiente_nivel
from src.morse import texto_a_morse

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def cargar_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def elegir_titulo_del_dia(config: dict, nivel_actual: int) -> str:
    """Busca en TMDb y elige un título aún no usado que encaje en el nivel actual."""
    usados = {t.upper() for t in estado.cargar_contenido_usado()}
    candidatos = contenido.buscar_candidatos_tmdb(config)

    aptos = [
        t for t in candidatos
        if t.upper() not in usados and nivel_requerido(t, config) <= nivel_actual
    ]
    if not aptos:
        raise RuntimeError(
            f"No se encontró ningún título apto para el nivel {nivel_actual}. "
            "Prueba a ampliar géneros/palabras clave en config.yaml."
        )
    return random.choice(aptos)


def _bloque_ranking_ayer(ranking_ayer: list) -> str:
    if not ranking_ayer:
        return ""
    medallas = ["🥇", "🥈", "🥉"]
    lineas = [f"{medallas[i]} @{u}" for i, (u, _) in enumerate(ranking_ayer)]
    return "\n\n🏆 **AYER LO PETARON:**\n" + "\n".join(lineas)


def _bloque_ranking_total(ranking_total: list) -> str:
    if not ranking_total:
        return ""
    lineas = [f"{i+1}️⃣ @{u} — {p} pts" for i, (u, p) in enumerate(ranking_total)]
    return "\n\n📊 **RANKING TOTAL**\n" + "\n".join(lineas)


def formatear_toot_leccion(config: dict, nivel: int, letras_nuevas: list,
                           titulo_ejemplo: str, morse_ejemplo: str,
                           ranking_ayer: list, ranking_total: list,
                           numero_leccion: int) -> str:
    """Construye el toot de la lección, recortando bloques opcionales
    (ranking total primero, ranking de ayer después) si el resultado
    supera el límite de caracteres configurado para la instancia.
    """
    letras_txt = ", ".join(f"**{l}**" for l in letras_nuevas)
    tabla = "\n".join(
        f"{l}: {texto_a_morse(l)}" for l in letras_nuevas
    )

    base = (
        f"🎬🔤 **LECCIÓN MORSE #{numero_leccion}** — ¡Buenas, frikis del cine! 👋\n\n"
        f"📖 Hoy le metemos caña a: {letras_txt}\n\n"
        f"```\n{tabla}\n```\n\n"
        f"🎯 Vamos a probarlo con lo que ya sabemos:\n"
        f"`{titulo_ejemplo}` → {morse_ejemplo}"
    )
    cierre = (
        f"\n\n⏰ El quiz cae esta tarde, ¡prepárate! 🍿👽\n\n"
        f"#AprendeMorse #Cine #CienciaFicción"
    )

    limite = config.get("mastodon", {}).get("max_caracteres", 500)

    # Empezamos con todos los bloques y vamos quitando los opcionales,
    # de menor a mayor prioridad, hasta que quepa en el límite.
    bloques_opcionales = [
        _bloque_ranking_total(ranking_total),
        _bloque_ranking_ayer(ranking_ayer),
    ]
    # orden de recorte: primero se quita el ranking total (índice 0),
    # así que probamos combinaciones de más a menos contenido:
    combinaciones = [
        bloques_opcionales[1] + bloques_opcionales[0],  # ayer + total (todo)
        bloques_opcionales[1],                           # solo ayer
        "",                                                # nada
    ]

    toot = base + cierre
    for extra in combinaciones:
        candidato = base + extra + cierre
        if len(candidato) <= limite:
            toot = candidato
            break

    # Si ni siquiera el toot mínimo cabe (límite muy bajo o título muy largo),
    # recortamos el propio cuerpo como último recurso sin pasarse del límite.
    if len(toot) > limite:
        exceso = len(toot) - limite
        corte = max(0, len(base) - max(0, exceso))
        toot = base[:corte] + cierre
        if len(toot) > limite:
            toot = toot[: max(0, limite - 1)] + "…"

    return toot


def main():
    config = cargar_config()
    est = estado.cargar_estado()

    hoy = str(date.today())
    if est.get("fecha_leccion") == hoy:
        print("Ya hay una lección publicada hoy. No se repite.")
        return

    ranking = estado.cargar_ranking()
    ranking_ayer = estado.top_ranking(ranking.get("hoy") or {}, n=3)
    ranking_total = estado.top_ranking(ranking.get("total") or {}, n=3)

    letras_enseñadas = estado.cargar_letras_enseñadas()
    nivel_actual = siguiente_nivel(config, letras_enseñadas)
    letras_nuevas = letras_nuevas_de_hoy(config, nivel_actual, letras_enseñadas)

    titulo = elegir_titulo_del_dia(config, nivel_actual)
    morse = texto_a_morse(titulo)

    numero_leccion = int(est.get("numero_leccion") or 0) + 1

    texto_toot = formatear_toot_leccion(
        config, nivel_actual, letras_nuevas, titulo, morse,
        ranking_ayer, ranking_total, numero_leccion,
    )

    mastodon = mastodon_client.conectar(config)
    mastodon_client.publicar_toot(mastodon, texto_toot)

    # Guardar estado para el quiz de la tarde
    est.update({
        "nivel_actual": nivel_actual,
        "numero_leccion": numero_leccion,
        "fecha_leccion": hoy,
        "titulo_leccion": titulo,
        "titulo_quiz_activo": None,       # se rellena en quiz.py
        "quiz_abierto_desde": None,
        "usuarios_respondieron_hoy": [],
    })
    estado.guardar_estado(est)
    estado.marcar_como_usado(titulo)
    estado.marcar_letras_enseñadas(letras_nuevas)

    # Solo se resetea el ranking diario tras publicar con éxito
    ranking["hoy"] = {}
    estado.guardar_ranking(ranking)

    print(f"Lección publicada. Nivel {nivel_actual}. Título: {titulo}")


if __name__ == "__main__":
    main()
