# -*- coding: utf-8 -*-
"""Genera el visor HTML interactivo de un knowledge graph.

Uso: python generar_visor.py electromagnetismo.json
Produce: visor_<materia>.html (autocontenido, sin dependencias externas).
"""
import json
import sys
import os

PLANTILLA = """<title>Grafo __MATERIA__ UVa</title>
<style>
:root {
  --bg: #F7F9FB;
  --surface: #FFFFFF;
  --ink: #1C2733;
  --muted: #5B6B7A;
  --line: #D8E0E8;
  --accent: #1D5FC2;
  --accent-ink: #FFFFFF;
  --accent-soft: rgba(29, 95, 194, 0.10);
  --copper: #B4690E;
  --copper-soft: rgba(180, 105, 14, 0.12);
  --sel: #12345E;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0E141B;
    --surface: #16202B;
    --ink: #E2E9F0;
    --muted: #8FA1B3;
    --line: #26323F;
    --accent: #6FA5F2;
    --accent-ink: #0E141B;
    --accent-soft: rgba(111, 165, 242, 0.14);
    --copper: #E39A4E;
    --copper-soft: rgba(227, 154, 78, 0.14);
    --sel: #BDD7FF;
  }
}
:root[data-theme="light"] {
  --bg: #F7F9FB; --surface: #FFFFFF; --ink: #1C2733; --muted: #5B6B7A;
  --line: #D8E0E8; --accent: #1D5FC2; --accent-ink: #FFFFFF;
  --accent-soft: rgba(29, 95, 194, 0.10); --copper: #B4690E;
  --copper-soft: rgba(180, 105, 14, 0.12); --sel: #12345E;
}
:root[data-theme="dark"] {
  --bg: #0E141B; --surface: #16202B; --ink: #E2E9F0; --muted: #8FA1B3;
  --line: #26323F; --accent: #6FA5F2; --accent-ink: #0E141B;
  --accent-soft: rgba(111, 165, 242, 0.14); --copper: #E39A4E;
  --copper-soft: rgba(227, 154, 78, 0.14); --sel: #BDD7FF;
}
* { box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: system-ui, "Segoe UI", sans-serif;
  margin: 0;
  line-height: 1.45;
}
.wrap { max-width: 1240px; margin: 0 auto; padding: 28px 20px 80px; }
header.top { margin-bottom: 20px; }
h1 {
  font-family: Charter, Georgia, "Times New Roman", serif;
  font-size: 1.7rem;
  font-weight: 700;
  margin: 0 0 4px;
  text-wrap: balance;
}
.sub { color: var(--muted); font-size: 0.92rem; margin: 0; }
.toolbar {
  display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
  margin-top: 16px;
}
#buscar {
  background: var(--surface); color: var(--ink);
  border: 1px solid var(--line); border-radius: 6px;
  padding: 8px 12px; font-size: 0.9rem; width: 260px; max-width: 100%;
}
#buscar:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
.leyenda { display: flex; flex-wrap: wrap; gap: 14px; font-size: 0.8rem; color: var(--muted); }
.leyenda span { display: inline-flex; align-items: center; gap: 6px; }
.dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }
.dot.d-sel { background: var(--accent); }
.dot.d-pre { background: transparent; border: 2px solid var(--accent); }
.dot.d-anc { background: var(--accent-soft); border: 1px solid var(--accent); }
.dot.d-dep { background: transparent; border: 2px solid var(--copper); }

.cols { display: grid; grid-template-columns: 1fr 340px; gap: 24px; align-items: start; }
@media (max-width: 900px) { .cols { grid-template-columns: 1fr; } .panel { position: static !important; } }

section.tema { margin-bottom: 18px; }
.tema h2 {
  font-family: Charter, Georgia, serif;
  font-size: 1.02rem; font-weight: 700; margin: 0 0 8px;
  padding-bottom: 4px; border-bottom: 1px solid var(--line);
}
.tema h2 small { color: var(--muted); font-weight: 400; font-size: 0.8rem; margin-left: 8px; }
.pills { display: flex; flex-wrap: wrap; gap: 7px; }
button.pill {
  background: var(--surface); color: var(--ink);
  border: 1px solid var(--line); border-radius: 999px;
  padding: 5px 12px; font-size: 0.82rem; cursor: pointer;
  font-family: inherit; line-height: 1.3;
  transition: border-color 120ms, background 120ms, opacity 120ms;
}
@media (prefers-reduced-motion: reduce) { button.pill { transition: none; } }
button.pill .nid {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 0.68rem; color: var(--muted); margin-right: 6px;
}
button.pill:hover { border-color: var(--accent); }
button.pill:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
button.pill.sel { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }
button.pill.sel .nid { color: var(--accent-ink); opacity: 0.75; }
button.pill.pre { border: 2px solid var(--accent); background: var(--accent-soft); }
button.pill.pre.blanda { border-style: dashed; }
button.pill.anc { background: var(--accent-soft); }
button.pill.dep { border: 2px solid var(--copper); background: var(--copper-soft); }
button.pill.apagado { opacity: 0.28; }

.panel {
  position: sticky; top: 16px;
  background: var(--surface); border: 1px solid var(--line);
  border-radius: 10px; padding: 18px 18px 20px;
}
.panel .vacio { color: var(--muted); font-size: 0.9rem; }
.panel h3 {
  font-family: Charter, Georgia, serif;
  font-size: 1.15rem; margin: 2px 0 2px; text-wrap: balance;
}
.panel .meta {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 0.72rem; color: var(--muted);
}
.panel .temaLbl { font-size: 0.78rem; color: var(--accent); margin: 4px 0 10px; }
.panel p.desc { font-size: 0.88rem; margin: 0 0 14px; }
.panel h4 {
  font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--muted); margin: 14px 0 6px; font-weight: 600;
}
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
button.chip {
  background: none; border: 1px solid var(--line); border-radius: 6px;
  color: var(--ink); font-size: 0.78rem; padding: 3px 9px; cursor: pointer;
  font-family: inherit; text-align: left;
}
button.chip:hover, button.chip:focus-visible { border-color: var(--accent); outline: none; }
button.chip .peso { color: var(--muted); font-size: 0.7rem; }
.chip.cPre { border-left: 3px solid var(--accent); }
.chip.cDep { border-left: 3px solid var(--copper); }
ul.fuentes { margin: 0; padding: 0 0 0 2px; list-style: none; font-size: 0.82rem; }
ul.fuentes li { margin-bottom: 3px; }
ul.fuentes .libro { color: var(--muted); }
.stats { font-size: 0.78rem; color: var(--muted); margin-top: 14px; border-top: 1px solid var(--line); padding-top: 10px; }
</style>

<div class="wrap">
  <header class="top">
    <h1>__MATERIA__ · grafo de conocimiento</h1>
    <p class="sub" id="resumen"></p>
    <div class="toolbar">
      <input id="buscar" type="search" placeholder="Filtrar nodos… (ej. Gauss, dieléctrico)" aria-label="Filtrar nodos">
      <div class="leyenda">
        <span><span class="dot d-sel"></span> seleccionado</span>
        <span><span class="dot d-pre"></span> prerrequisito directo</span>
        <span><span class="dot d-anc"></span> ancestro</span>
        <span><span class="dot d-dep"></span> lo necesita</span>
      </div>
    </div>
  </header>

  <div class="cols">
    <main id="temas"></main>
    <aside class="panel" id="panel">
      <p class="vacio">Haz clic en un nodo para ver sus prerrequisitos, qué temas dependen de él y dónde estudiarlo en la bibliografía.</p>
    </aside>
  </div>
</div>

<script>
const GRAFO = __GRAFO_JSON__;

const nodos = GRAFO.nodos;
const porId = Object.fromEntries(nodos.map(n => [n.id, n]));
const dependientes = {};
nodos.forEach(n => (n.prerequisitos || []).forEach(p => {
  (dependientes[p.id] = dependientes[p.id] || []).push(n.id);
}));

const NOMBRES_LIBROS = {
  wangsness: "Wangsness", griffiths: "Griffiths", jackson: "Jackson",
  feynman: "Feynman", panofsky: "Panofsky", thide: "Thidé",
  problemas: "Problemas (López/Núñez)", apuntes: "Apuntes UVa"
};
function nombreDe(id) {
  return porId[id] ? porId[id].nombre : id + " (otra asignatura)";
}

document.getElementById("resumen").textContent =
  nodos.length + " nodos · " +
  nodos.reduce((a, n) => a + (n.prerequisitos || []).length, 0) + " aristas de prerrequisito · " +
  Object.keys(GRAFO.temas).length + " temas · guía docente " + GRAFO.codigo_uva + " (UVa)";

const contTemas = document.getElementById("temas");
Object.keys(GRAFO.temas).sort((a, b) => +a - +b).forEach(t => {
  const sec = document.createElement("section");
  sec.className = "tema";
  const nds = nodos.filter(n => String(n.tema) === t);
  sec.innerHTML = "<h2>" + GRAFO.temas[t] + "<small>" + nds.length + " nodos</small></h2>";
  const pills = document.createElement("div");
  pills.className = "pills";
  nds.forEach(n => {
    const b = document.createElement("button");
    b.className = "pill";
    b.dataset.id = n.id;
    b.innerHTML = '<span class="nid">' + n.id.replace("em.", "") + "</span>" + n.nombre;
    b.addEventListener("click", () => seleccionar(n.id));
    pills.appendChild(b);
  });
  sec.appendChild(pills);
  contTemas.appendChild(sec);
});

function ancestros(id) {
  const res = new Set();
  const cola = [id];
  while (cola.length) {
    const actual = porId[cola.pop()];
    if (!actual) continue;
    (actual.prerequisitos || []).forEach(p => {
      if (!res.has(p.id)) { res.add(p.id); cola.push(p.id); }
    });
  }
  return res;
}

let seleccionado = null;

function seleccionar(id) {
  const n = porId[id];
  if (!n) return; // prerrequisito de otra asignatura: no está en este visor
  seleccionado = id;
  const directos = new Map((n.prerequisitos || []).map(p => [p.id, p.peso]));
  const anc = ancestros(id);
  const deps = dependientes[id] || [];

  document.querySelectorAll("button.pill").forEach(b => {
    const bid = b.dataset.id;
    b.classList.remove("sel", "pre", "anc", "dep", "blanda");
    if (bid === id) b.classList.add("sel");
    else if (directos.has(bid)) {
      b.classList.add("pre");
      if (directos.get(bid) < 1) b.classList.add("blanda");
    }
    else if (anc.has(bid)) b.classList.add("anc");
    else if (deps.includes(bid)) b.classList.add("dep");
  });

  const fuentes = Object.entries(n.fuentes || {}).map(([k, v]) =>
    "<li><span class='libro'>" + (NOMBRES_LIBROS[k] || k) + ":</span> " + v + "</li>").join("");

  const chipsPre = (n.prerequisitos || []).map(p =>
    "<button class='chip cPre' data-go='" + p.id + "'>" + nombreDe(p.id) +
    (p.peso < 1 ? " <span class='peso'>(" + p.peso + ")</span>" : "") + "</button>").join("") ||
    "<span class='vacio'>Ninguno — nodo raíz.</span>";

  const chipsDep = deps.map(d =>
    "<button class='chip cDep' data-go='" + d + "'>" + porId[d].nombre + "</button>").join("") ||
    "<span class='vacio'>Ninguno (final de rama).</span>";

  document.getElementById("panel").innerHTML =
    "<div class='meta'>" + n.id + "</div>" +
    "<h3>" + n.nombre + "</h3>" +
    "<div class='temaLbl'>" + GRAFO.temas[String(n.tema)] + "</div>" +
    "<p class='desc'>" + n.descripcion + "</p>" +
    "<h4>Prerrequisitos directos</h4><div class='chips'>" + chipsPre + "</div>" +
    "<h4>Lo necesitan</h4><div class='chips'>" + chipsDep + "</div>" +
    "<h4>Dónde estudiarlo</h4><ul class='fuentes'>" + fuentes + "</ul>" +
    "<div class='stats'>" + anc.size + " nodos en su cadena de prerrequisitos · desbloquea " +
    deps.length + " directamente</div>";

  document.querySelectorAll("#panel button.chip").forEach(c =>
    c.addEventListener("click", () => {
      seleccionar(c.dataset.go);
      const pill = document.querySelector("button.pill[data-id='" + c.dataset.go + "']");
      if (pill) pill.scrollIntoView({ block: "center", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }));
}

document.getElementById("buscar").addEventListener("input", e => {
  const q = e.target.value.trim().toLowerCase();
  document.querySelectorAll("button.pill").forEach(b => {
    const n = porId[b.dataset.id];
    const texto = (n.id + " " + n.nombre + " " + n.descripcion).toLowerCase();
    b.classList.toggle("apagado", q !== "" && !texto.includes(q));
  });
});
</script>
"""


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_visor.py <grafo.json>")
        sys.exit(1)
    ruta = sys.argv[1]
    with open(ruta, "r", encoding="utf-8") as f:
        grafo = json.load(f)

    html = PLANTILLA.replace("__GRAFO_JSON__", json.dumps(grafo, ensure_ascii=False))
    html = html.replace("__MATERIA__", grafo["materia"])
    salida = os.path.join(
        os.path.dirname(os.path.abspath(ruta)),
        f"visor_{grafo['materia'].lower().replace(' ', '_')}.html",
    )
    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Visor generado: {salida}")


if __name__ == "__main__":
    main()
