# -*- coding: utf-8 -*-
"""Convierte las transcripciones de exámenes (CUESTIONES.txt / PROBLEMAS.txt,
formato Obsidian por convocatoria) al formato MD estándar del banco.

Uso:
  python convertir_examenes_txt.py <CUESTIONES.txt> <PROBLEMAS.txt> <salida.md>
"""
import re
import sys


def limpiar(texto: str) -> str:
    lineas = []
    for l in texto.splitlines():
        s = l.strip()
        if not s:
            lineas.append("")
            continue
        if s.startswith("Pasted image") or s.startswith("![[") or s == "---":
            continue
        lineas.append(l)
    out = "\n".join(lineas)
    out = re.sub(r"\[\[(.*?)\]\]", r"\1", out)  # quitar wiki-links
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def extraer_titulo(cuerpo: str, defecto: str) -> tuple[str, str]:
    """El título suele ser un remate corto tipo 'Nombre (2022)' al final."""
    lineas = cuerpo.splitlines()
    idx_ult = max((i for i, l in enumerate(lineas) if l.strip()), default=-1)
    if idx_ult < 0:
        return defecto, cuerpo
    ult = lineas[idx_ult].strip()
    # Caso 1: la última línea ES el título
    if len(ult) < 80 and re.search(r"\(20\d\d\)$", ult):
        resto = "\n".join(lineas[:idx_ult]).strip()
        return ult, resto
    # Caso 2: el título va pegado al final de la última línea
    m = re.search(r"[.?!)]\s+([A-ZÁÉÍÓÚÑ][^.!?]{5,70}\(20\d\d\))\s*$", ult)
    if m:
        titulo = m.group(1).strip()
        lineas[idx_ult] = ult[: m.start(1)].rstrip()
        return titulo, "\n".join(lineas).strip()
    return defecto, cuerpo


def parsear_cuestiones(ruta: str) -> list[dict]:
    with open(ruta, "r", encoding="utf-8") as f:
        texto = f.read()
    items = []
    convocatoria, ambito = "", ""
    # Secciones por convocatoria y cabeceras de ámbito en negrita (formatos variados)
    bloques = re.split(r"(?m)^(### .*|\*\*[^*\n]*(?:FINAL|PARCIAL|GLOBAL)[^*\n]*\*\*)\s*$", texto)
    for trozo in bloques:
        t = trozo.strip()
        if t.startswith("### "):
            convocatoria = re.sub(r"[#*]", "", t).replace("Electromagnetismo —", "").strip()
            continue
        if re.fullmatch(r"\*\*[^*\n]*\*\*", t):
            ambito = re.sub(r"[*]", "", t).strip().lower()
            continue
        # Cuestiones: '- **C1.**', '- **C1.-**', '- **C1 (3 de junio).**'
        partes = re.split(r"(?m)^- \*\*C(\d+[^*]*?)\*\*\s*", t)
        for i in range(1, len(partes), 2):
            num, cuerpo = partes[i].strip(" .-"), limpiar(partes[i + 1])
            if not cuerpo:
                continue
            titulo, cuerpo = extraer_titulo(cuerpo, f"Cuestión C{num} ({convocatoria})")
            items.append({
                "hoja": f"Examen {convocatoria} — cuestiones ({ambito})",
                "titulo": titulo,
                "enunciado": cuerpo,
            })
    return items


def parsear_problemas(ruta: str) -> list[dict]:
    with open(ruta, "r", encoding="utf-8") as f:
        texto = f.read()
    # Solo la primera mitad (la segunda repite los mismos problemas numerados)
    corte = texto.find("### **")
    if corte > 0:
        texto = texto[:corte]
    items = []
    convocatoria = ""
    partes = re.split(r"(?m)^(### .*)$", texto)
    for trozo in partes:
        t = trozo.strip()
        if t.startswith("### "):
            convocatoria = re.sub(r"[#*]", "", t).replace("Electromagnetismo —", "").strip()
            continue
        subpartes = re.split(r"(?m)^\*\*((?:S[OÓ]LO|TODOS)[^*\n]*?)\.?\*\*\s*", t)
        for i in range(1, len(subpartes), 2):
            ambito, cuerpo = subpartes[i].lower(), limpiar(subpartes[i + 1])
            if not cuerpo:
                continue
            titulo, cuerpo = extraer_titulo(cuerpo, "Problema de examen")
            items.append({
                "hoja": f"Examen {convocatoria} — problemas ({ambito})",
                "titulo": titulo,
                "enunciado": cuerpo,
            })
    return items


def main():
    ruta_c, ruta_p, salida = sys.argv[1], sys.argv[2], sys.argv[3]
    cuestiones = parsear_cuestiones(ruta_c)
    problemas = parsear_problemas(ruta_p)
    print(f"Cuestiones: {len(cuestiones)} · Problemas: {len(problemas)}")

    lineas = ["# Compilación de exámenes de Electromagnetismo (convocatorias anteriores)", "",
              "# Tema 0: Exámenes de convocatorias anteriores", ""]
    hoja_actual = None
    n = 0
    for it in cuestiones + problemas:
        if it["hoja"] != hoja_actual:
            hoja_actual = it["hoja"]
            lineas.append(f"## {hoja_actual}")
            lineas.append("")
        n += 1
        lineas.append(f"### {n}.- {it['titulo']}")
        lineas.append(it["enunciado"])
        lineas.append("")
    with open(salida, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    print(f"Escrito {salida} con {n} items")


if __name__ == "__main__":
    main()
