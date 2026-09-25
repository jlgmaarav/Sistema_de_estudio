import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# =====================================================================
# Gemini Web: modelo obligatorio y sin credenciales de API
# =====================================================================

# Este es el único punto de configuración del modelo de Gemini Web. Ahora es
# Gemini 3.8 Flash; cuando Google publique otro modelo, basta con cambiar esta
# variable (o GEMINI_WEB_MODEL en .env). El resto del sistema lee el alias
# GEMINI_REQUIRED_MODEL para mantener una API interna clara.
GEMINI_WEB_MODEL = os.getenv("GEMINI_WEB_MODEL", "Gemini 3.8 Flash").strip()
if not GEMINI_WEB_MODEL:
    raise RuntimeError("GEMINI_WEB_MODEL no puede estar vacío.")
GEMINI_REQUIRED_MODEL = GEMINI_WEB_MODEL
GEMINI_WEB_URL = os.getenv("GEMINI_WEB_URL", "https://gemini.google.com/app").strip()

VAULT_PATH = os.getenv("VAULT_PATH")
if not VAULT_PATH:
    # Si no está definida, usar por defecto el directorio de trabajo actual
    VAULT_PATH = os.getcwd()
else:
    # Normalizar ruta de Windows a barras diagonales
    VAULT_PATH = os.path.abspath(VAULT_PATH).replace("\\", "/")

# =====================================================================
# Definición de Directorios de Obsidian
# =====================================================================

ASSETS_DIR = f"{VAULT_PATH}/Assets"
ERRORES_DIR = f"{VAULT_PATH}/Errores"
INTENTOS_DIR = f"{VAULT_PATH}/Intentos"
ESTUDIOS_DIR = f"{VAULT_PATH}/Estudios"
ASIGNATURAS_DIR = f"{VAULT_PATH}/Estudios/Asignaturas"
CONCEPTOS_DIR = f"{VAULT_PATH}/Conceptos"
INBOX_DIR = f"{VAULT_PATH}/Inbox"
INBOX_PROCESADOS_DIR = f"{VAULT_PATH}/Inbox/Procesados"
LECTURAS_DIR = f"{VAULT_PATH}/Lecturas"
PROYECTOS_DIR = f"{VAULT_PATH}/Proyectos"
DASHBOARD_PATH = f"{VAULT_PATH}/Dashboard.md"

def init_vault_structure():
    """Crea los directorios necesarios del vault de Obsidian si no existen."""
    directories = [
        ASSETS_DIR,
        ERRORES_DIR,
        INTENTOS_DIR,
        ESTUDIOS_DIR,
        ASIGNATURAS_DIR,
        CONCEPTOS_DIR,
        INBOX_DIR,
        INBOX_PROCESADOS_DIR,
        LECTURAS_DIR,
        PROYECTOS_DIR
    ]
    for d in directories:
        if not os.path.exists(d):
            try:
                os.makedirs(d, exist_ok=True)
                print(f"Directorio creado en el vault: {d}")
            except Exception as e:
                print(f"Error al crear el directorio {d}: {e}")
                sys.exit(1)

if __name__ == "__main__":
    print("Configuración cargada correctamente:")
    print(f"  Modelo Gemini Web obligatorio: {GEMINI_REQUIRED_MODEL}")
    print(f"  Vault Path: {VAULT_PATH}")
    print(f"  Assets Dir: {ASSETS_DIR}")
    print(f"  Errores Dir: {ERRORES_DIR}")
    print(f"  Intentos Dir: {INTENTOS_DIR}")
    
    init_vault_structure()
