# -*- coding: utf-8 -*-
"""Corregir lo nuevo — un solo comando de baja fricción.

Flujo pensado para el reMarkable: resuelves problemas a mano (cada uno con su
código, ej. 3.1), enciendes el portátil y ejecutas esto. Hace, en orden:

  1) Sincroniza el reMarkable (trae al Inbox lo escrito nuevo).
  2) Procesa el Inbox con Gemini (una llamada por hoja; varios problemas por hoja).
  3) Deja el feedback en la vista "Correcciones" de la app (Obsidian = registro).

Uso:
    python corregir.py            # sincroniza y procesa
    python corregir.py --no-sync  # solo procesa lo que ya haya en el Inbox
"""
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)


def _sincronizar():
    """Ejecuta la sincronización del reMarkable. Devuelve True si fue bien."""
    print("=" * 56)
    print("  1/2  Sincronizando el reMarkable...")
    print("=" * 56)
    try:
        sys.path.insert(0, os.path.join(BASE, "remarkable_sync"))
        import sync as rm_sync
    except Exception as e:
        print(f"  [AVISO] No se pudo cargar el sincronizador: {e}")
        return False
    try:
        rm_sync.sync()
        return True
    except SystemExit as e:
        # sync() usa sys.exit() ante errores (p. ej. app de reMarkable no instalada)
        print(f"  [AVISO] La sincronización terminó pronto (código {e.code}). "
              f"Se procesará lo que ya haya en el Inbox.")
        return False
    except Exception as e:
        print(f"  [AVISO] Error durante la sincronización: {e}")
        return False


def _procesar():
    """Procesa el Inbox una vez con el watcher."""
    print("\n" + "=" * 56)
    print("  2/2  Procesando lo nuevo con Gemini...")
    print("=" * 56)
    import watcher
    import generar_dashboard
    watcher.scan_once()
    try:
        generar_dashboard.run()
    except Exception:
        pass


def main():
    hacer_sync = "--no-sync" not in sys.argv
    t0 = time.time()
    if hacer_sync:
        _sincronizar()
    else:
        print("  (--no-sync) Se omite la sincronización; solo se procesa el Inbox.")
    _procesar()
    print(f"\n[LISTO] Terminado en {time.time() - t0:.0f}s. "
          f"Abre la app y mira la pestaña 'Correcciones'.")


if __name__ == "__main__":
    main()
