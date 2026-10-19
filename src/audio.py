"""
audio.py
Genera el pitido de audio a partir de una cadena morse (ej. "-.. ..- -. .")
usando numpy para sintetizar la onda y pydub/ffmpeg para exportar a
mp3 u ogg (formatos comprimidos, más ligeros para adjuntar al toot).

Timing estándar morse (en unidades):
  punto = 1 unidad
  raya = 3 unidades
  espacio entre símbolos de la misma letra = 1 unidad
  espacio entre letras = 3 unidades
  espacio entre palabras = 7 unidades
"""
import io
import numpy as np
from pydub import AudioSegment

SAMPLE_RATE = 44100


def _unidad_segundos(wpm: int) -> float:
    """Duración de una unidad morse en segundos, según la fórmula estándar PARIS."""
    return 1.2 / wpm


def _tono(duracion_s: float, frecuencia_hz: int) -> np.ndarray:
    n_muestras = int(SAMPLE_RATE * duracion_s)
    t = np.linspace(0, duracion_s, n_muestras, endpoint=False)
    onda = 0.5 * np.sin(2 * np.pi * frecuencia_hz * t)
    # fade in/out corto para evitar "clics" al principio/final del tono
    fade_len = max(1, int(SAMPLE_RATE * 0.005))
    envolvente = np.ones(n_muestras)
    envolvente[:fade_len] = np.linspace(0, 1, fade_len)
    envolvente[-fade_len:] = np.linspace(1, 0, fade_len)
    return onda * envolvente


def _silencio(duracion_s: float) -> np.ndarray:
    return np.zeros(int(SAMPLE_RATE * duracion_s))


def morse_a_audio(morse: str, wpm: int = 15, frecuencia_hz: int = 700) -> np.ndarray:
    """Convierte una cadena morse (con ' / ' entre palabras, ' ' entre letras)
    en un array de audio (numpy, float32, mono).
    """
    unidad = _unidad_segundos(wpm)
    bloques = []

    palabras = morse.strip().split(" / ")
    for i_palabra, palabra in enumerate(palabras):
        letras = palabra.strip().split(" ")
        for i_letra, letra in enumerate(letras):
            for i_simbolo, simbolo in enumerate(letra):
                dur = unidad if simbolo == "." else unidad * 3
                bloques.append(_tono(dur, frecuencia_hz))
                if i_simbolo < len(letra) - 1:
                    bloques.append(_silencio(unidad))  # entre símbolos de la letra
            if i_letra < len(letras) - 1:
                bloques.append(_silencio(unidad * 3))  # entre letras
        if i_palabra < len(palabras) - 1:
            bloques.append(_silencio(unidad * 7))  # entre palabras

    if not bloques:
        return np.zeros(1)
    return np.concatenate(bloques).astype(np.float32)


def guardar_audio(muestras: np.ndarray, ruta_salida: str, formato: str = "mp3"):
    """Exporta el array de audio a un fichero mp3 u ogg usando pydub/ffmpeg."""
    audio_int16 = np.int16(np.clip(muestras, -1, 1) * 32767)
    segmento = AudioSegment(
        audio_int16.tobytes(),
        frame_rate=SAMPLE_RATE,
        sample_width=2,
        channels=1,
    )
    segmento.export(ruta_salida, format=formato)


if __name__ == "__main__":
    from src.morse import texto_a_morse

    morse = texto_a_morse("DUNE")
    muestras = morse_a_audio(morse, wpm=15, frecuencia_hz=700)
    guardar_audio(muestras, "/tmp/dune_test.mp3", formato="mp3")
    print(f"Audio generado: {len(muestras)/SAMPLE_RATE:.2f}s -> /tmp/dune_test.mp3")
