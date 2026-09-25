# -*- coding: utf-8 -*-
"""Graba audio del micrófono del portátil directamente a grabaciones/.

Sin móvil ni pasar archivos: grabas aquí mismo mientras resuelves y narras.
Se para pulsando ENTER. El audio se escribe a disco sobre la marcha (si se corta
la luz no pierdes lo grabado).

Uso:
    python grabar.py             # solo graba (hasta pulsar Enter)
    python grabar.py --corregir  # al parar, transcribe y prepara Gemini Web
"""
import os
import sys
import math
import queue
import threading
import datetime
import subprocess

import numpy as np
import sounddevice as sd
import soundfile as sf

BASE = os.path.dirname(os.path.abspath(__file__))
GRABACIONES_DIR = os.path.join(BASE, "grabaciones")
MICRO_GUARDADO = os.path.join(BASE, "micro.json")

# Por debajo de esto se considera silencio (dBFS). Una voz normal a 40 cm ronda -30/-15.
UMBRAL_SILENCIO_DB = -45.0


# ---------------------------------------------------------------------------
# Elección de micrófono (se recuerda entre sesiones en micro.json)
# ---------------------------------------------------------------------------
def listar_entradas():
    """Imprime los dispositivos de entrada disponibles y devuelve sus índices."""
    import json
    guardado = _micro_guardado()
    por_defecto = sd.default.device[0]
    print()
    print("MICRÓFONOS DISPONIBLES")
    print("-" * 66)
    indices = []
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] <= 0:
            continue
        indices.append(i)
        marcas = []
        if i == guardado:
            marcas.append("EN USO")
        elif guardado is None and i == por_defecto:
            marcas.append("por defecto de Windows")
        marca = ("   <-- " + ", ".join(marcas)) if marcas else ""
        print(f"  [{i:2d}] {d['name'][:44]:44s} {int(d['default_samplerate']):>6} Hz{marca}")
    print("-" * 66)
    return indices


def _micro_guardado():
    """Índice del micro elegido, o None si nunca se ha elegido / ya no existe."""
    import json
    if not os.path.exists(MICRO_GUARDADO):
        return None
    try:
        with open(MICRO_GUARDADO, "r", encoding="utf-8") as f:
            datos = json.load(f)
        idx, nombre = datos["indice"], datos.get("nombre", "")
    except Exception:
        return None
    # Los índices de PortAudio bailan al conectar/desconectar Bluetooth: se valida el nombre.
    try:
        d = sd.query_devices(idx)
    except Exception:
        return None
    if d["max_input_channels"] <= 0:
        return None
    if nombre and not d["name"].startswith(nombre[:20]):
        # Cambió de sitio: se busca por nombre.
        for i, otro in enumerate(sd.query_devices()):
            if otro["max_input_channels"] > 0 and otro["name"].startswith(nombre[:20]):
                return i
        return None
    return idx


def guardar_micro(indice: int):
    import json
    d = sd.query_devices(indice)
    if d["max_input_channels"] <= 0:
        raise ValueError(f"El dispositivo [{indice}] ({d['name']}) no tiene entrada de audio.")
    with open(MICRO_GUARDADO, "w", encoding="utf-8") as f:
        json.dump({"indice": indice, "nombre": d["name"]}, f, ensure_ascii=False, indent=2)
    print(f"Micrófono fijado: [{indice}] {d['name']}")


def elegir_micro_interactivo():
    """Lista los micros y pide uno por teclado. Para lanzar desde micro.bat."""
    indices = listar_entradas()
    print("Escribe el número del micrófono y pulsa ENTER (o ENTER a secas para no cambiar).")
    try:
        resp = input("  > ").strip()
    except EOFError:
        resp = ""
    if not resp:
        print("Sin cambios.")
        return
    try:
        idx = int(resp)
    except ValueError:
        print("Eso no es un número.")
        return
    if idx not in indices:
        print(f"[{idx}] no está en la lista de entradas.")
        return
    guardar_micro(idx)


def _dbfs(bloque) -> float:
    """Nivel RMS del bloque en dBFS. -inf si es silencio absoluto."""
    rms = float(np.sqrt(np.mean(np.square(bloque, dtype=np.float64))))
    return 20.0 * math.log10(rms) if rms > 0 else -120.0


def _barra(db: float, ancho: int = 34) -> str:
    """Vúmetro de texto: mapea [-60, 0] dBFS a una barra de `ancho` bloques."""
    frac = max(0.0, min(1.0, (db + 60.0) / 60.0))
    llenos = int(round(frac * ancho))
    return "#" * llenos + "-" * (ancho - llenos)


def _elegir_samplerate(dispositivo, preferida: int = 16000) -> int:
    """16 kHz mono es lo que usa Whisper (archivo pequeño). Si el micro no lo
    admite, cae a su frecuencia por defecto (Whisper remuestrea igualmente)."""
    try:
        sd.check_input_settings(device=dispositivo, samplerate=preferida, channels=1)
        return preferida
    except Exception:
        info = sd.query_devices(dispositivo) if dispositivo is not None \
            else sd.query_devices(kind="input")
        return int(info["default_samplerate"])


def grabar() -> str:
    os.makedirs(GRABACIONES_DIR, exist_ok=True)
    dispositivo = _micro_guardado()          # None = el que diga Windows
    sr = _elegir_samplerate(dispositivo)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = os.path.join(GRABACIONES_DIR, f"grabacion_{ts}.wav")

    cola: "queue.Queue" = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print(status, file=sys.stderr)
        cola.put(indata.copy())

    info = sd.query_devices(dispositivo) if dispositivo is not None \
        else sd.query_devices(kind="input")
    origen = "elegido por ti" if dispositivo is not None else "por defecto de Windows"
    print(f"Micrófono: {info['name']}  ({sr} Hz)  [{origen}]")
    print("           Para cambiarlo: micro.bat")
    print("-" * 56)
    print("  GRABANDO. Narra tu razonamiento mientras resuelves.")
    print("  Pulsa ENTER para PARAR.")
    print("-" * 56)
    print("  El vúmetro de abajo tiene que MOVERSE al hablar.")
    print("  Si se queda plano en [------], el micro no está entrando.")
    print()

    parar = threading.Event()
    threading.Thread(target=lambda: (input(), parar.set()), daemon=True).start()

    pico_db = -120.0        # el bloque más fuerte de toda la grabación
    bloques_voz = 0         # bloques por encima del umbral de silencio
    bloques_total = 0

    def _pintar(db: float):
        """Vúmetro en la misma línea. `end=''` + `\\r` para no llenar la consola."""
        estado = "VOZ " if db > UMBRAL_SILENCIO_DB else "sil."
        print(f"\r  [{_barra(db)}] {db:6.1f} dBFS  {estado}", end="", flush=True)

    with sf.SoundFile(ruta, mode="w", samplerate=sr, channels=1, subtype="PCM_16") as f:
        with sd.InputStream(device=dispositivo, samplerate=sr, channels=1, callback=callback):
            while not parar.is_set():
                try:
                    bloque = cola.get(timeout=0.2)
                except queue.Empty:
                    continue
                f.write(bloque)
                db = _dbfs(bloque)
                pico_db = max(pico_db, db)
                bloques_total += 1
                if db > UMBRAL_SILENCIO_DB:
                    bloques_voz += 1
                _pintar(db)
            while not cola.empty():   # vaciar el búfer pendiente
                f.write(cola.get())

    dur = os.path.getsize(ruta) / (sr * 2)  # bytes / (Hz * 2 bytes) = segundos
    pct_voz = (100.0 * bloques_voz / bloques_total) if bloques_total else 0.0

    print("\n")
    print(f"Guardado: {ruta}  ({int(dur // 60):02d}:{int(dur % 60):02d})")
    print(f"Nivel máximo: {pico_db:.1f} dBFS  ·  con voz: {pct_voz:.0f}% del tiempo")

    # Diagnóstico explícito: mejor enterarse aquí que tras 3 minutos de transcripción vacía.
    if pico_db <= UMBRAL_SILENCIO_DB:
        print()
        print("[ERROR] NO SE HA GRABADO NADA. El audio está en silencio de principio a fin.")
        print("        Revisa: micrófono correcto en Configuración > Sistema > Sonido > Entrada,")
        print("        permiso de micrófono para aplicaciones de escritorio, y que no esté silenciado.")
        print("        Dispositivos de entrada que ve Python:")
        for i, d in enumerate(sd.query_devices()):
            if d["max_input_channels"] > 0:
                print(f"          [{i}] {d['name']}")
    elif pico_db < -30.0:
        print("[aviso] Nivel bajo. Se entenderá peor: acércate al micro o sube el volumen de entrada.")
    elif pct_voz < 10.0:
        print("[aviso] Muy poca voz detectada para lo que dura el audio. ¿Se cortó el micro a mitad?")

    return ruta


def main():
    if "--listar" in sys.argv:
        listar_entradas()
        return
    if "--elegir" in sys.argv:
        elegir_micro_interactivo()
        return
    if "--micro" in sys.argv:
        i = sys.argv.index("--micro")
        if i + 1 >= len(sys.argv):
            print("Uso: python grabar.py --micro <numero>   (ver la lista con --listar)")
            return
        guardar_micro(int(sys.argv[i + 1]))
        if "--corregir" not in sys.argv:
            return

    ruta = grabar()
    if "--corregir" in sys.argv:
        print("\nTranscribiendo y corrigiendo...\n")
        subprocess.run([sys.executable, os.path.join(BASE, "corregir_voz.py"), ruta])
    else:
        print("Para corregirla: doble clic en voz.bat (coge la grabación más nueva).")


if __name__ == "__main__":
    main()
