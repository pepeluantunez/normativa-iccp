# -*- coding: utf-8 -*-
"""Vigencia de cada documento del indice de busqueda.

POR QUE EXISTE (2026-08-19). El indice BM25 no sabia si una norma esta en vigor:
es texto y solo texto. El registro SI lo sabe -core_normativa/_registry y
05_vigencia/vigencia.csv- pero nadie se lo preguntaba en el momento de buscar.

Con eso, la consulta "cuantia minima de armadura de traccion en flexion"
devolvia EHE-08 en TRES de los seis primeros resultados, por encima del Codigo
Estructural, y el segundo era literalmente el art. 42.3.5: la cuantia geometrica
que el Codigo Estructural suprimio y que ese mismo dia se estaba retirando de los
motores de calculo. O sea que el corpus servia de primera mano el criterio
derogado, sin una sola palabra que lo advirtiera, a quien preguntaba de buena fe.

Criterio: NO se oculta ni se filtra nada. Una norma derogada sigue haciendo falta
-para justificar un proyecto anterior, para leer un documento antiguo, para saber
que decia antes-. Lo que no puede pasar es entregarla SIN ETIQUETA. Se marca y se
posterga; quien la quiera, la ve y sabe lo que tiene en la mano.

Ordenar por relevancia a secas es lo que convierte 4.511 fragmentos de una norma
muerta en la respuesta mas probable a cualquier pregunta de hormigon.

MODO PLUGIN (2026-08-26). REGISTRY y VIGENCIA se resuelven bajo la misma raiz
que search_engine.py (env CORE_NORMATIVA_ROOT, o el layout legacy del toolkit
si no esta definida). Si cualquiera de los dos falta bajo esa raiz -un corpus
de muestra ajeno puede no traerlos- se avisa una vez por stderr y estado_de()
devuelve siempre None: nunca se lanza excepcion por no tener el dato.
"""
from __future__ import annotations

import csv
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from search_engine import resolve_corpus_base  # noqa: E402

_BASE = resolve_corpus_base()
REGISTRY = _BASE / "_registry" / "normativa_registry.yml"
VIGENCIA = _BASE / "05_vigencia" / "vigencia.csv"

log = logging.getLogger("normativa-mcp")

# Estados que NO son "aplicable hoy sin matices". Se marcan todos, cada uno con
# su palabra: 'derogada' y 'anulada' no son lo mismo, y 'tramitacion' menos aun.
NO_VIGENTES = {
    "derogada":            "DEROGADA",
    "anulada":             "ANULADA",
    "tramitacion":         "EN TRAMITACION",
    "vigente_condicionada": "VIGENTE CON CONDICIONES",
}

_cache: dict[str, tuple[str, str]] | None = None


def _leer_vigencia_csv() -> dict[str, tuple[str, str]]:
    """codigo CORE-NOR -> (estado, sucesora)."""
    fuera: dict[str, tuple[str, str]] = {}
    if not VIGENCIA.is_file():
        return fuera
    with VIGENCIA.open(encoding="utf-8", newline="") as fh:
        for fila in csv.DictReader(fh):
            estado = (fila.get("estado") or "").strip()
            if estado and estado != "vigente":
                fuera[(fila.get("core_nor") or "").strip()] = (
                    estado, (fila.get("norma_sucesora") or "").strip())
    return fuera


def _mapa() -> dict[str, tuple[str, str]]:
    """stem del fichero de texto -> (estado, sucesora). Solo los NO vigentes.

    Se cruza por la RUTA del texto que declara el registro, no por el titulo:
    el indice nombra los documentos por el stem del fichero y cualquier cruce
    por nombre legible falla en cuanto una norma tiene dos denominaciones -que
    era lo normal: '6.1-IC' e 'IC_6_1_Secciones_Firme' fueron el mismo texto
    en dos formatos hasta que el .txt se retiro el 31/08/2026-.
    """
    global _cache
    if _cache is not None:
        return _cache
    _cache = {}
    try:
        import yaml
    except ImportError:
        return _cache          # sin yaml no se puede afirmar nada: no se marca
    faltan = [p for p in (REGISTRY, VIGENCIA) if not p.is_file()]
    if faltan:
        log.warning(
            "Vigencia sin datos: falta %s bajo la raiz activa (corpus externo "
            "sin ese dato). Resultados sin etiqueta de vigencia.",
            ", ".join(str(p) for p in faltan))
        return _cache

    fuera = _leer_vigencia_csv()
    reg = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    normas = reg.get("normas") or {}
    # El registro ha viajado entre lista y mapa; se aceptan las dos formas
    # porque un AttributeError aqui deja el indice SIN marcar y en silencio.
    entradas = normas.values() if isinstance(normas, dict) else normas
    for norma in entradas:
        if not isinstance(norma, dict):
            continue
        codigo = str(norma.get("codigo") or "")
        estado = str(norma.get("estado_vigencia") or "")
        sucesora = ""
        if codigo in fuera:                    # el CSV manda sobre el yml
            estado, sucesora = fuera[codigo]
        if estado in NO_VIGENTES:
            ruta = (norma.get("rutas") or {}).get("texto_extraido")
            if ruta:
                _cache[Path(str(ruta)).stem] = (estado, sucesora)
    return _cache


def estado_de(source: str) -> tuple[str, str] | None:
    """(etiqueta, sucesora) si el documento NO esta vigente; None si lo esta.

    Devolver None tambien cuando NO CONSTA es deliberado: marcar de dudoso lo
    que no se ha podido comprobar entrenaria a ignorar la etiqueta, que es la
    forma mas rapida de que un aviso deje de avisar.
    """
    m = _mapa().get(source)
    if m is None:
        return None
    return NO_VIGENTES.get(m[0], m[0].upper()), m[1]
