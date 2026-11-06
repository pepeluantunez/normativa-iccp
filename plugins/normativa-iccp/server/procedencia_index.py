# -*- coding: utf-8 -*-
"""De donde sale de verdad el texto que el indice rotula con el nombre de una norma.

POR QUE EXISTE (2026-08-20). Seis documentos del corpus se llaman UNE-EN 933-1,
933-8, 933-9, 1097-2, 1097-6 y 12697-6, y los seis contienen el MISMO PDF: un
'Prontuario en Excel de Hormigon Armado'. Otros dos se llaman UNE-EN 17176-2 y
UNE-EN 1401-1 y contienen las normas tecnicas de EMASA. Uno se llama RD 1071/2007
y contiene un taller de georreferenciacion del COA Malaga de 2017.

Nada de eso esta oculto: cada fichero lo declara en su cabecera ("Apoyo tecnico
local para UNE-EN 933-1. No es el PDF UNE exacto"). El corpus es honrado A NIVEL
DE DOCUMENTO. Lo que no llegaba era al momento de la busqueda: el resultado sale
rotulado 'UNE_EN_933_1', con su score y su extracto, y quien lo lea de buena fe
puede citar en un anejo una UNE que nadie ha abierto. Es exactamente la misma
forma de fallo que la vigencia -un dato correcto en el sitio equivocado- y se
arregla igual: se ETIQUETA y se POSTERGA, no se filtra. El apoyo tecnico sigue
sirviendo para calcular; lo que no sirve es para citar.

TRES COSAS DISTINTAS (la tercera desde 2026-09-19):

- NO_ES_LA_NORMA. La cabecera declara `no_es_la_norma`: alguien LEYO el
  documento y comprobo que no es la norma cuyo nombre lleva o llevaba el
  fichero (Velez-Malaga servido como EMASA, un taller servido como el RD
  1071/2007). Aviso fuerte y al final, igual que el suplantado, y dice cual es
  el texto bueno. La fuente de la marca es el registry (seccion
  ficheros_mal_rotulados); la cabecera la repite para que llegue aqui tambien
  en modo plugin, sin registry.

- SUPLANTADO. El mismo PDF de origen sostiene a varias normas con item_id
  distinto. Es demostrativo: un PDF no puede ser dos normas, asi que como maximo
  una de ellas lo es. Aviso fuerte y al final de la lista.
- APOYO LOCAL. El documento declara source_kind 'support_local' y su origen no
  lo comparte con nadie: es la copia del despacho de esa misma norma, no el texto
  oficial consolidado. El PG-3, la Instruccion de Firmes de Andalucia o la IH-100
  estan asi, y son los documentos buenos. Aviso corto, sin postergar: decir "esto
  no es el PG-3" seria falso y convertiria el aviso en ruido.

MODO PLUGIN (2026-08-26). CORPUS se resuelve con la misma raiz que
search_engine.py (env CORE_NORMATIVA_ROOT, o el layout legacy del toolkit si
no esta definida). Un corpus externo sin 01_texto_extraido/ bajo esa raiz no
lanza excepcion: se avisa una vez por stderr y procedencia_de() devuelve
siempre None (nada que advertir, porque no hay nada que comprobar).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from search_engine import resolve_corpus_base  # noqa: E402

CORPUS = resolve_corpus_base() / "01_texto_extraido"

log = logging.getLogger("normativa-mcp")

_cache: dict[str, tuple[str, str]] | None = None


def _cabecera(p: Path) -> dict[str, str]:
    campos: dict[str, str] = {}
    try:
        cab = p.read_text(encoding="utf-8", errors="replace")[:1200]
    except OSError:
        return campos
    for linea in cab.splitlines():
        if not linea.startswith("- "):
            continue
        clave, sep, valor = linea[2:].partition(":")
        if sep:
            campos[clave.strip()] = valor.strip().strip("`")
    return campos


def _mapa() -> dict[str, tuple[str, str]]:
    """stem -> (clase, detalle). Solo los documentos con algo que declarar."""
    global _cache
    if _cache is not None:
        return _cache
    _cache = {}
    if not CORPUS.is_dir():
        log.warning(
            "Procedencia sin datos: no existe %s bajo la raiz activa "
            "(corpus externo sin ese dato). Resultados sin etiqueta de procedencia.",
            CORPUS)
        return _cache

    cabeceras: dict[str, dict[str, str]] = {}
    por_origen: dict[str, set[str]] = {}
    for p in sorted(CORPUS.rglob("*")):
        if p.suffix not in (".txt", ".md") or "_stubs" in p.parts:
            continue
        cab = _cabecera(p)
        if not cab:
            continue
        cabeceras[p.stem] = cab
        origen, item = cab.get("source_origin"), cab.get("item_id")
        if origen and item:
            por_origen.setdefault(origen, set()).add(item)

    for stem, cab in cabeceras.items():
        origen = cab.get("source_origin", "")
        nombre = origen.replace(chr(92), "/").rsplit("/", 1)[-1]
        if cab.get("no_es_la_norma"):
            # Marca declarada (registry, seccion ficheros_mal_rotulados, y
            # cabecera): el fichero se llama o se llamaba como una norma y su
            # texto es otro documento. Va primero porque es la afirmacion mas
            # fuerte: no es una sospecha por origen compartido, esta leido.
            _cache[stem] = ("NO_ES_LA_NORMA",
                            f"es {cab.get('title', '').strip()}; NO es "
                            f"{cab['no_es_la_norma']}; texto bueno: "
                            f"{cab.get('norma_buena', 'no consta').strip()}")
        elif origen and len(por_origen.get(origen, ())) > 1:
            _cache[stem] = ("SUPLANTADO", nombre)
        elif cab.get("source_kind") == "support_local":
            _cache[stem] = ("APOYO_LOCAL", cab.get("note", "").strip())
    return _cache


def procedencia_de(source: str) -> tuple[str, str] | None:
    """(clase, detalle) si el documento tiene algo que advertir; None si no.

    None cuando no consta es deliberado, igual que en vigencia_index: marcar de
    dudoso lo que no se ha comprobado entrena a ignorar la etiqueta.
    """
    return _mapa().get(source)


def es_suplantado(source: str) -> bool:
    """Cierto si el texto NO es el de la norma que da por titulo.

    Cubre las dos formas: SUPLANTADO (se deduce del origen compartido) y
    NO_ES_LA_NORMA (declarado tras leer el documento, ERR-NOR-011).
    """
    p = procedencia_de(source)
    return p is not None and p[0] in ("SUPLANTADO", "NO_ES_LA_NORMA")
