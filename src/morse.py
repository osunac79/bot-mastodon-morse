"""
morse.py
Traducción texto <-> morse. Solo letras, números y espacios
(sin signos de puntuación, sin Ñ ni acentos, de momento).
"""

MORSE_CODE = {
    "A": ".-",    "B": "-...",  "C": "-.-.",  "D": "-..",   "E": ".",
    "F": "..-.",  "G": "--.",   "H": "....",  "I": "..",    "J": ".---",
    "K": "-.-",   "L": ".-..",  "M": "--",    "N": "-.",    "O": "---",
    "P": ".--.",  "Q": "--.-",  "R": ".-.",   "S": "...",   "T": "-",
    "U": "..-",   "V": "...-",  "W": ".--",   "X": "-..-",  "Y": "-.--",
    "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
}

MORSE_CODE_INV = {v: k for k, v in MORSE_CODE.items()}

# Caracteres permitidos en el contenido del bot (fase actual: sin puntuación)
CARACTERES_PERMITIDOS = set(MORSE_CODE.keys()) | {" "}


def texto_a_morse(texto: str) -> str:
    """Convierte texto (A-Z, 0-9, espacios) a morse.
    Letras separadas por un espacio, palabras separadas por ' / '.
    Lanza ValueError si hay un carácter no soportado.
    """
    texto = texto.upper().strip()
    palabras = texto.split(" ")
    palabras_morse = []
    for palabra in palabras:
        letras_morse = []
        for char in palabra:
            if char not in MORSE_CODE:
                raise ValueError(f"Carácter no soportado en morse: {char!r}")
            letras_morse.append(MORSE_CODE[char])
        palabras_morse.append(" ".join(letras_morse))
    return " / ".join(palabras_morse)


def morse_a_texto(morse: str) -> str:
    """Convierte morse (con ' / ' entre palabras, ' ' entre letras) a texto."""
    palabras = morse.strip().split(" / ")
    texto_palabras = []
    for palabra in palabras:
        letras = palabra.strip().split(" ")
        texto = "".join(MORSE_CODE_INV.get(l, "") for l in letras if l)
        texto_palabras.append(texto)
    return " ".join(texto_palabras)


def es_valido(texto: str) -> bool:
    """Comprueba que el texto solo use caracteres soportados por el bot."""
    return all(c.upper() in CARACTERES_PERMITIDOS for c in texto)


def letras_usadas(texto: str) -> set:
    """Devuelve el conjunto de letras/números distintos que aparecen en el texto."""
    return {c.upper() for c in texto if c.upper() in MORSE_CODE}


def normalizar_respuesta(texto: str) -> str:
    """Normaliza una respuesta de usuario para comparar contra la solución:
    mayúsculas -> minúsculas, espacios colapsados y recortados.
    """
    return " ".join(texto.strip().lower().split())


if __name__ == "__main__":
    ejemplo = "DUNE"
    m = texto_a_morse(ejemplo)
    print(f"{ejemplo} -> {m}")
    print(f"{m} -> {morse_a_texto(m)}")
