import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# =====================================================================
# Validación de Variables de Entorno Fundamentales
# =====================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    print("Error: La variable GEMINI_API_KEY no está configurada en el archivo .env.")
    print("Por favor, edita el archivo .env e introduce tu clave de la API de Gemini.")
    sys.exit(1)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
# Modelo de respaldo: si el principal falla (429/503/sin cuota), se reintenta con
# este. Debe ser un modelo DISTINTO y existente (tiene su propia cuota gratuita):
# gemini-flash-lite-latest es un alias siempre válido y más ligero.
GEMINI_MODEL_FALLBACK = os.getenv("GEMINI_MODEL_FALLBACK", "gemini-flash-lite-latest")

try:
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
except ValueError:
    TEMPERATURE = 0.1

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
    print(f"  Modelo Gemini: {GEMINI_MODEL}")
    print(f"  Modelo de respaldo: {GEMINI_MODEL_FALLBACK}")
    print(f"  Temperatura: {TEMPERATURE}")
    print(f"  Vault Path: {VAULT_PATH}")
    print(f"  Assets Dir: {ASSETS_DIR}")
    print(f"  Errores Dir: {ERRORES_DIR}")
    print(f"  Intentos Dir: {INTENTOS_DIR}")
    
    init_vault_structure()
