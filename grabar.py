# -*- coding: utf-8 -*-
"""Graba audio del micrófono del portátil directamente a grabaciones/.

Sin móvil ni pasar archivos: grabas aquí mismo mientras resuelves y narras.
Se para pulsando ENTER. El audio se escribe a disco sobre la marcha (si se corta
la luz no pierdes lo grabado).

Uso:
    python grabar.py             # solo graba (hasta pulsar Enter)
    python grabar.py --corregir  # al parar, transcribe y corrige (Whisper + Claude)
"""
import os
import sys
import queue
import threading
import datetime
import subprocess

import sounddevice as sd
import soundfile as sf

BASE = os.path.dirname(os.path.abspath(__file__))
GRABACIONES_DIR = os.path.join(BASE, "grabaciones")


def _elegir_samplerate(preferida: int = 16000) -> int:
    """16 kHz mono es lo que usa Whisper (archivo pequeño). Si el micro no lo
    admite, cae a su frecuencia por defecto (Whisper remuestrea igualmente)."""
    try:
        sd.check_input_settings(samplerate=preferida, channels=1)
        return preferida
    except Exception:
        return int(sd.query_devices(kind="input")["default_samplerate"])


def grabar() -> str:
    os.makedirs(GRABACIONES_DIR, exist_ok=True)
    sr = _elegir_samplerate()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = os.path.join(GRABACIONES_DIR, f"grabacion_{ts}.wav")

    cola: "queue.Queue" = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print(status, file=sys.stderr)
        cola.put(indata.copy())

    print(f"Micrófono: {sd.query_devices(kind='input')['name']}  ({sr} Hz)")
    print("-" * 56)
    print("  GRABANDO. Narra tu razonamiento mientras resuelves.")
    print("  Pulsa ENTER para PARAR.")
    print("-" * 56)

    parar = threading.Event()
    threading.Thread(target=lambda: (input(), parar.set()), daemon=True).start()

    with sf.SoundFile(ruta, mode="w", samplerate=sr, channels=1, subtype="PCM_16") as f:
        with sd.InputStream(samplerate=sr, channels=1, callback=callback):
            while not parar.is_set():
                try:
                    f.write(cola.get(timeout=0.2))
                except queue.Empty:
                    pass
            while not cola.empty():   # vaciar el búfer pendiente
                f.write(cola.get())

    dur = os.path.getsize(ruta) / (sr * 2)  # bytes / (Hz * 2 bytes) = segundos
    print(f"\nGuardado: {ruta}  ({int(dur // 60):02d}:{int(dur % 60):02d})")
    return ruta


def main():
    ruta = grabar()
    if "--corregir" in sys.argv:
        print("\nTranscribiendo y corrigiendo...\n")
        subprocess.run([sys.executable, os.path.join(BASE, "corregir_voz.py"), ruta])
    else:
        print("Para corregirla: doble clic en voz.bat (coge la grabación más nueva).")


if __name__ == "__main__":
    main()
