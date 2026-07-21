# -*- coding: utf-8 -*-
"""Transcribe una narración de audio a texto con faster-whisper (local y gratis).

Pensado para el método de estudio hablado: resuelves el ejercicio en papel/reMarkable
y vas narrando en alto tu razonamiento. Grabas ese audio con el móvil, lo dejas en la
carpeta `grabaciones/` (o lo pasas como argumento) y esto lo convierte en texto para
que luego la IA lo corrija.

Uso:
    python transcribir.py <archivo_audio>   # transcribe ese archivo
    python transcribir.py                    # transcribe el audio más NUEVO de grabaciones/

Salida: un `.txt` junto al audio, y el texto por pantalla.

Modelo: variable de entorno WHISPER_MODEL (por defecto 'large-v3-turbo').
    - large-v3-turbo : mejor equilibrio calidad/velocidad en CPU (recomendado).
    - medium         : más rápido, algo menos preciso.
    - large-v3       : máxima precisión, bastante más lento en CPU.
La primera vez descarga el modelo (~1.6 GB para turbo) una sola vez; luego queda en caché.

Todo corre en tu ordenador: el audio no sale a ningún servidor.
"""
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
GRABACIONES_DIR = os.path.join(BASE, "grabaciones")

# Extensiones de audio que aceptamos (PyAV/ffmpeg decodifica todas).
EXTS_AUDIO = {".m4a", ".mp3", ".wav", ".ogg", ".opus", ".flac", ".aac", ".wma", ".mp4", ".webm"}

MODELO = os.getenv("WHISPER_MODEL", "large-v3-turbo")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE", "int8")  # int8 = rápido y ligero en CPU

# Sesga el reconocimiento hacia vocabulario de física para acertar mejor los términos.
PROMPT_CONTEXTO = (
    "Resolución de un problema de física narrada en voz alta. Vocabulario habitual: "
    "ley de Gauss, campo eléctrico, flujo, integral de superficie, simetría esférica, "
    "carga encerrada, épsilon cero, ecuaciones de Maxwell, potencial, divergencia, "
    "rotacional, gradiente, condiciones de contorno, función de onda, mecánica cuántica, "
    "corrientes lentamente variables, magnetostática."
)


def _mmss(segundos: float) -> str:
    m, s = divmod(int(segundos), 60)
    return f"{m:02d}:{s:02d}"


def audio_mas_nuevo(carpeta: str) -> str | None:
    """Devuelve la ruta del archivo de audio modificado más recientemente en `carpeta`."""
    if not os.path.isdir(carpeta):
        return None
    candidatos = [
        os.path.join(carpeta, f) for f in os.listdir(carpeta)
        if os.path.splitext(f)[1].lower() in EXTS_AUDIO
    ]
    if not candidatos:
        return None
    return max(candidatos, key=os.path.getmtime)


def transcribir(ruta_audio: str) -> str:
    """Transcribe `ruta_audio` a español y devuelve el texto. Muestra el progreso."""
    from faster_whisper import WhisperModel

    print(f"Cargando modelo '{MODELO}' (la primera vez descarga; luego es instantáneo)...")
    t0 = time.time()
    modelo = WhisperModel(MODELO, device="cpu", compute_type=COMPUTE_TYPE)
    print(f"Modelo listo en {time.time() - t0:.0f}s. Transcribiendo: {os.path.basename(ruta_audio)}")
    print("-" * 60)

    segmentos, info = modelo.transcribe(
        ruta_audio,
        language="es",
        vad_filter=True,          # salta los silencios (mientras escribes) -> más rápido y sin alucinaciones
        beam_size=5,
        initial_prompt=PROMPT_CONTEXTO,
    )

    duracion = getattr(info, "duration", 0) or 0
    partes = []
    t_ini = time.time()
    for seg in segmentos:
        texto = seg.text.strip()
        partes.append(texto)
        # Progreso: [posición en el audio] texto reconocido
        print(f"[{_mmss(seg.end)}/{_mmss(duracion)}] {texto}")

    print("-" * 60)
    print(f"Transcripción completada en {time.time() - t_ini:.0f}s "
          f"(audio de {_mmss(duracion)}).")
    return " ".join(p for p in partes if p).strip()


def main():
    if len(sys.argv) > 1:
        ruta = os.path.abspath(sys.argv[1])
        if not os.path.isfile(ruta):
            print(f"[ERROR] No existe el archivo: {ruta}")
            sys.exit(1)
    else:
        os.makedirs(GRABACIONES_DIR, exist_ok=True)
        ruta = audio_mas_nuevo(GRABACIONES_DIR)
        if not ruta:
            print(f"[ERROR] No hay audios en {GRABACIONES_DIR}.")
            print("Deja ahí tu grabación (.m4a, .mp3, .ogg...) o pásala como argumento:")
            print("    python transcribir.py mi_audio.m4a")
            sys.exit(1)
        print(f"Audio más nuevo en grabaciones/: {os.path.basename(ruta)}")

    texto = transcribir(ruta)

    salida = os.path.splitext(ruta)[0] + ".txt"
    with open(salida, "w", encoding="utf-8") as f:
        f.write(texto)

    print()
    print("=" * 60)
    print(f"[LISTO] Texto guardado en: {salida}")
    print(f"        {len(texto.split())} palabras.")
    print("=" * 60)


if __name__ == "__main__":
    main()
