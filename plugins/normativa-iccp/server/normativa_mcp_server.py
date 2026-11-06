"""
normativa_mcp_server.py — MCP server (stdio) para búsqueda en corpus normativo.

Herramientas expuestas:
  query_normativa          búsqueda BM25 full-text (con aviso de vigencia y procedencia)
  get_knowledge_ficha      ficha de conocimiento operativo por dominio
  list_available_normas    listado de documentos indexados
  get_norma_excerpt        extracto de un documento específico

Registro directo (claude_desktop_config.json / uso fuera de un plugin):
  "normativa-mcp": {
    "command": "python",
    "args": ["<ruta_toolkit>/mcp/normativa/normativa_mcp_server.py"],
    "env": {}
  }

Registro como plugin (.mcp.json), fuente unica que se empaqueta hacia
plugins/normativa-iccp/server/ vía tools/producto/empaquetar_marketplace.py:
  {
    "mcpServers": {
      "normativa": {
        "command": "python",
        "args": ["${CLAUDE_PLUGIN_ROOT}/server/normativa_mcp_server.py"],
        "env": {
          "CORE_NORMATIVA_ROOT": "${user_config.corpus_root}",
          "NORMATIVA_LOG_LEVEL": "${user_config.log_level}"
        }
      }
    }
  }

Variables de entorno:
  CORE_NORMATIVA_ROOT    obligatoria al ejecutar como plugin instalado.
                         Apunta a la carpeta que contiene 01_texto_extraido/,
                         04_conocimiento/, _registry/ y 05_vigencia/. Si esta
                         sin definir, usa el layout legacy del toolkit.
  NORMATIVA_LOG_LEVEL    INFO (default) o DEBUG. DEBUG vuelca consultas e
                         indexacion al stderr.
"""

import json
import logging
import os
import sys
from pathlib import Path

# Logger por stderr (stdout esta reservado al protocolo MCP)
_log_level = os.environ.get("NORMATIVA_LOG_LEVEL", "INFO").upper()
if _log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
    _log_level = "INFO"
logging.basicConfig(
    stream=sys.stderr,
    level=getattr(logging, _log_level),
    format="[normativa-mcp] %(levelname)s %(message)s",
)
log = logging.getLogger("normativa-mcp")

# Añadir el directorio del servidor al path para importar search_engine
sys.path.insert(0, str(Path(__file__).parent))
from search_engine import BM25Index, CORPUS_ROOTS
from procedencia_index import procedencia_de
from vigencia_index import estado_de

log.info("Corpus roots resueltos: %s", [str(r) for r in CORPUS_ROOTS])

# Instancia global — se construye en el primer uso (lazy)
_index: BM25Index | None = None


def _get_index() -> BM25Index:
    global _index
    if _index is None:
        log.info("Construyendo indice BM25 (primer uso)...")
        _index = BM25Index()
        _index.build()
        log.info("Indice listo.")
    return _index


# ── Herramientas ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "query_normativa",
        "description": (
            "Busca en el corpus normativo local (Instrucciones IC, PG-3, normativa EMASA, "
            "decretos de accesibilidad, etc.) usando BM25 full-text. "
            "Devuelve los fragmentos más relevantes con su fuente y dominio. "
            "Usar para responder preguntas técnicas sobre normativa de obra civil, "
            "urbanización y saneamiento aplicable en España (Andalucía)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Texto de búsqueda en español",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Número máximo de resultados (por defecto 5, máximo 20)",
                    "default": 5,
                },
                "domain_filter": {
                    "type": "string",
                    "description": (
                        "Filtrar por dominio: trazado, firmes, drenaje, agua, saneamiento, "
                        "accesibilidad, senalizacion, residuos, bc3, geotecnia... "
                        "Dejar vacío para buscar en todo el corpus."
                    ),
                    "default": "",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_knowledge_ficha",
        "description": (
            "Devuelve la ficha de conocimiento operativo completa para un dominio técnico. "
            "Las fichas contienen checklists, valores de referencia, reglas de redacción "
            "y artículos aplicables. Dominios disponibles: trazado, firmes, drenaje, agua, "
            "saneamiento, accesibilidad, senalizacion."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": (
                        "Nombre del dominio: trazado | firmes | drenaje | agua | "
                        "saneamiento | accesibilidad | senalizacion"
                    ),
                }
            },
            "required": ["domain"],
        },
    },
    {
        "name": "list_available_normas",
        "description": (
            "Lista todos los documentos normativos indexados en el corpus local, "
            "con su dominio y número de fragmentos. Usar para saber qué normativa "
            "está disponible antes de hacer una búsqueda."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_norma_excerpt",
        "description": (
            "Extrae un fragmento relevante de un documento normativo específico "
            "buscando dentro de él. Útil cuando ya se conoce la fuente y se quiere "
            "localizar un artículo o sección concreta."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Nombre del documento (sin extensión) tal como aparece en list_available_normas",
                },
                "query": {
                    "type": "string",
                    "description": "Texto a buscar dentro del documento",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Número de fragmentos a devolver (por defecto 3)",
                    "default": 3,
                },
            },
            "required": ["source", "query"],
        },
    },
]


# ── Implementación de herramientas ────────────────────────────────────────────

def handle_query_normativa(args: dict) -> dict:
    query        = args.get("query", "").strip()
    top_k        = min(int(args.get("top_k", 5)), 20)
    domain_filter = args.get("domain_filter", "").strip()

    if not query:
        return {"isError": True, "content": [{"type": "text", "text": "ERROR: query no puede estar vacío"}]}

    idx     = _get_index()
    results = idx.search(query, top_k=top_k, domain_filter=domain_filter)

    if not results:
        return {
            "content": [{
                "type": "text",
                "text": f"Sin resultados para: '{query}'" + (f" (dominio: {domain_filter})" if domain_filter else ""),
            }]
        }

    # Vigencia (2026-08-19). El indice es texto y solo texto: no sabe si una
    # norma sigue en vigor. Sin esto, "cuantia minima de armadura" devolvia
    # EHE-08 -derogada- en tres de los seis primeros y por encima del Codigo
    # Estructural, sirviendo de primera mano el criterio que ya no rige.
    # No se filtra: se etiqueta y se posterga. Una norma derogada sigue
    # haciendo falta para leer un proyecto antiguo; lo que no vale es
    # entregarla sin decir lo que es.
    # Procedencia (2026-08-20). El mismo fallo, en el otro eje: un documento
    # rotulado 'UNE_EN_933_1' cuyo texto es un Prontuario de hormigon armado.
    # Cada fichero lo declara en su cabecera, pero la declaracion se quedaba en
    # el fichero y no llegaba a la respuesta, asi que se podia citar en un anejo
    # una UNE que nadie ha abierto. Se etiqueta igual: marcar y postergar.
    marcados = [(r, estado_de(r.chunk.source), procedencia_de(r.chunk.source))
                for r in results]
    marcados.sort(key=lambda par: (par[1] is not None
                                   or (par[2] or ("",))[0] == "SUPLANTADO",
                                   -par[0].score))

    lines = [f"## Resultados para: '{query}'\n"]
    n_fuera = sum(1 for _, e, _p in marcados if e is not None)
    n_supl = sum(1 for _, _e, p in marcados if p is not None and p[0] == "SUPLANTADO")
    if n_fuera:
        lines.append(
            f"> AVISO: {n_fuera} de {len(marcados)} resultado(s) NO estan "
            f"vigentes. Van al final y marcados. NO sirven para justificar "
            f"proyecto nuevo.\n")
    if n_supl:
        lines.append(
            f"> AVISO: {n_supl} de {len(marcados)} resultado(s) NO contienen el "
            f"texto de la norma que dan por titulo -su PDF de origen sostiene a "
            f"varias normas a la vez-. Valen como apoyo tecnico; NO se pueden "
            f"citar como esa norma.\n")
    for i, (r, est, proc) in enumerate(marcados, 1):
        sello = ""
        if est is not None:
            etiqueta, sucesora = est
            sello = f"  [!] **{etiqueta}**"
            if sucesora:
                sello += f" - la sustituye {sucesora}"
        if proc is not None:
            clase, detalle = proc
            if clase == "SUPLANTADO":
                sello += ("  [!] **NO ES EL TEXTO DE ESTA NORMA** - el fichero "
                          f"sale de {detalle}")
            elif clase == "APOYO_LOCAL":
                sello += "  [apoyo local: copia del despacho, no el texto oficial]"
        lines.append(f"### [{i}] {r.chunk.source}  (dominio: {r.chunk.domain}, "
                     f"score: {r.score}){sello}")
        lines.append(f"**Archivo:** `{r.chunk.path}`")
        lines.append(f"\n{r.snippet}\n")


    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


def handle_get_knowledge_ficha(args: dict) -> dict:
    domain = args.get("domain", "").strip().lower()
    if not domain:
        return {"isError": True, "content": [{"type": "text", "text": "ERROR: domain es obligatorio"}]}

    idx  = _get_index()
    text = idx.get_ficha(domain)

    if text is None:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Ficha de conocimiento no encontrada para dominio: '{domain}'"}],
        }

    return {"content": [{"type": "text", "text": text}]}


def handle_list_available_normas(_args: dict) -> dict:
    idx     = _get_index()
    sources = idx.list_sources()

    if not sources:
        return {"content": [{"type": "text", "text": "Corpus vacío — no hay documentos indexados."}]}

    # Agrupar por dominio
    by_domain: dict[str, list] = {}
    for s in sources:
        by_domain.setdefault(s["domain"], []).append(s)

    lines = [f"## Corpus normativo — {len(sources)} documentos indexados\n"]
    for domain in sorted(by_domain):
        lines.append(f"### {domain}")
        for s in by_domain[domain]:
            lines.append(f"- `{s['source']}` ({s['chunks']} fragmentos)")
        lines.append("")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


def handle_get_norma_excerpt(args: dict) -> dict:
    source = args.get("source", "").strip()
    query  = args.get("query", "").strip()
    top_k  = min(int(args.get("top_k", 3)), 10)

    if not source or not query:
        return {"isError": True, "content": [{"type": "text", "text": "ERROR: source y query son obligatorios"}]}

    idx = _get_index()

    # Filtrar chunks del documento específico
    matching_chunks = [c for c in idx.chunks if c.source == source]
    if not matching_chunks:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Documento no encontrado en el índice: '{source}'"}],
        }

    # BM25 local sobre los chunks del documento
    tokens = idx._tokenize(query)
    from collections import Counter

    # Construir índice local
    local_scores: list[tuple[float, object]] = []
    for chunk in matching_chunks:
        chunk_tokens = idx._tokenize(chunk.text)
        count = Counter(chunk_tokens)
        dl    = len(chunk_tokens)
        score = 0.0
        for t in set(tokens):
            tf = count.get(t, 0)
            if tf == 0:
                continue
            denom  = tf + idx.k1 * (1 - idx.b + idx.b * dl / max(idx._avgdl, 1))
            score += tf * (idx.k1 + 1) / denom
        local_scores.append((score, chunk))

    local_scores.sort(key=lambda x: x[0], reverse=True)

    lines = [f"## Extractos de '{source}' para: '{query}'\n"]
    shown = 0
    for score, chunk in local_scores:
        if score <= 0:
            break
        snippet = idx._make_snippet(chunk.text, tokens)
        lines.append(f"### Fragmento (offset {chunk.offset}, score {round(score,3)})")
        lines.append(snippet)
        lines.append("")
        shown += 1
        if shown >= top_k:
            break

    if shown == 0:
        lines.append("Sin coincidencias relevantes en ese documento para la consulta.")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


HANDLERS = {
    "query_normativa":      handle_query_normativa,
    "get_knowledge_ficha":  handle_get_knowledge_ficha,
    "list_available_normas": handle_list_available_normas,
    "get_norma_excerpt":    handle_get_norma_excerpt,
}


# ── Protocolo MCP stdio (JSON-RPC 2.0) ───────────────────────────────────────

def send(obj: dict):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def handle_request(req: dict) -> dict | None:
    method = req.get("method", "")
    req_id = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "normativa-mcp", "version": "1.0.0"},
            },
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        params     = req.get("params", {})
        tool_name  = params.get("name", "")
        tool_args  = params.get("arguments", {})
        handler    = HANDLERS.get(tool_name)
        if handler is None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
            }
        try:
            result = handler(tool_args)
        except Exception as exc:
            result = {"isError": True, "content": [{"type": "text", "text": f"ERROR interno: {exc}"}]}
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "notifications/initialized":
        return None  # notificación, sin respuesta

    # Método desconocido
    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    return None


def main():
    # Forzar UTF-8 en stdin/stdout para que acentos y ñ lleguen bien
    # independientemente del locale del sistema (Windows/Linux). A nivel de
    # funcion (no de import): reconfigurar stdin/stdout al importar el modulo
    # rompe la captura de stdout de pytest y se dispara aunque el modulo se
    # importe solo para probar los handlers, no para correr como servidor.
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle_request(req)
        if response is not None:
            send(response)


if __name__ == "__main__":
    main()
