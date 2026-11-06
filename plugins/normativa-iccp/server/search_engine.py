"""
search_engine.py — Motor BM25 sobre el corpus normativo.
Pura stdlib Python, sin dependencias externas.

Origen del corpus (en orden de prioridad):
  1. Env var CORE_NORMATIVA_ROOT — uso como plugin instalado. Debe apuntar a la
     carpeta que contiene 01_texto_extraido/, 04_conocimiento/, _registry/ y
     05_vigencia/.
  2. Fallback al layout legacy del toolkit (mcp/normativa/ -> ../../core_normativa/).

`resolve_corpus_base()` es la raiz comun: la reusan procedencia_index.py y
vigencia_index.py para que las tres capas (busqueda, procedencia, vigencia)
resuelvan siempre la misma raiz activa.
"""

import math
import os
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


def resolve_corpus_base() -> Path:
    """Raiz que contiene 01_texto_extraido/, 04_conocimiento/, _registry/ y
    05_vigencia/: CORE_NORMATIVA_ROOT (modo plugin) o el layout legacy del
    toolkit si la env var no esta definida. No valida existencia — eso lo
    hace cada consumidor segun lo que necesite (ver _resolve_corpus_roots).
    """
    env_root = os.environ.get("CORE_NORMATIVA_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return Path(__file__).parent.parent.parent / "core_normativa"


def _resolve_corpus_roots() -> list[Path]:
    """Subcarpetas de texto indexable bajo la raiz activa.

    Lanza RuntimeError si NINGUNA de las dos existe, en lugar de fallar
    silenciosamente al indexar (defecto real del prototipo: un
    CORE_NORMATIVA_ROOT mal escrito indexaba 0 documentos sin avisar).
    """
    base  = resolve_corpus_base()
    roots = [base / "01_texto_extraido", base / "04_conocimiento"]

    existing = [r for r in roots if r.exists()]
    if not existing:
        # Las rutas se listan una por linea, NO con el repr de la lista: en
        # Windows ese repr escapa cada `\` como `\\`, asi que la ruta impresa
        # no es la que el usuario escribio y no se puede ni copiar ni buscar.
        buscadas = "".join(f"\n  - {r}" for r in roots)
        raise RuntimeError(
            f"No se encontro corpus normativo. Busque en:{buscadas}\n"
            f"Base resuelta: {base}\n"
            "Define CORE_NORMATIVA_ROOT apuntando a la carpeta que contiene "
            "01_texto_extraido/ y 04_conocimiento/."
        )
    return existing


CORPUS_ROOTS = _resolve_corpus_roots()

CHUNK_SIZE   = 600   # caracteres por chunk
CHUNK_STRIDE = 400   # solapamiento entre chunks
STUB_DIR     = "_stubs"


@dataclass
class Chunk:
    chunk_id:  str
    source:    str   # nombre del fichero sin extensión
    path:      str
    domain:    str   # sub-carpeta o "normativa"
    text:      str
    offset:    int   # posición en el documento original


@dataclass
class SearchResult:
    chunk:  Chunk
    score:  float
    snippet: str  # extracto con contexto


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b  = b
        self.chunks: list[Chunk] = []
        self._inv: dict[str, list[tuple[int, int]]] = defaultdict(list)  # term → [(chunk_idx, tf)]
        self._dl:  list[int]  = []   # longitud en tokens por chunk
        self._avgdl: float    = 0.0
        self._built = False

    # ── Tokenización ──────────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Minusculas y SIN tildes.

        Sin el plegado de tildes, "cuantia" y "cuantía" eran terminos
        distintos: la misma pregunta escrita sin acentos -que es como se
        teclea la mitad de las veces- devolvia otro conjunto de documentos, y
        ninguno util. Comprobado el 2026-08-19 con "cuantia minima de armadura
        de traccion en flexion": con tildes salia el Codigo Estructural; sin
        ellas, fichas de saneamiento y pluviales.

        Se aplica al indexar Y al consultar, asi que la simetria se mantiene.
        Efecto colateral aceptado: la ñ se pliega a n, de modo que 'año' y
        'ano' colisionan. En un corpus tecnico de obra civil eso ensucia mucho
        menos que perder la mitad de las busquedas por una tilde.
        """
        text = unicodedata.normalize("NFD", text.lower())
        text = "".join(c for c in text if unicodedata.category(c) != "Mn")
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = [t for t in text.split() if len(t) > 2]
        return tokens

    # ── Indexado ──────────────────────────────────────────────────────────────

    def _add_chunk(self, chunk: Chunk):
        idx    = len(self.chunks)
        tokens = self._tokenize(chunk.text)
        self.chunks.append(chunk)
        self._dl.append(len(tokens))
        counts = Counter(tokens)
        for term, tf in counts.items():
            self._inv[term].append((idx, tf))

    def build(self):
        """Lee el corpus completo y construye el índice."""
        for root in CORPUS_ROOTS:
            if not root.exists():
                continue
            for path in sorted(root.rglob("*.txt")) + sorted(root.rglob("*.md")):
                if STUB_DIR in path.parts:
                    continue
                self._index_file(path)

        self._avgdl = sum(self._dl) / max(len(self._dl), 1)
        self._built = True

    def _index_file(self, path: Path):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return

        # Determinar dominio
        root_names = {r.name for r in CORPUS_ROOTS}
        parts = path.parts
        domain = "normativa"
        for i, part in enumerate(parts):
            if part in root_names and i + 1 < len(parts):
                candidate = parts[i + 1]
                if candidate != path.name:
                    domain = candidate
                break

        source = path.stem

        # Chunking con solapamiento
        pos = 0
        while pos < len(text):
            chunk_text = text[pos:pos + CHUNK_SIZE]
            if chunk_text.strip():
                chunk = Chunk(
                    chunk_id=f"{source}:{pos}",
                    source=source,
                    path=str(path),
                    domain=domain,
                    text=chunk_text,
                    offset=pos,
                )
                self._add_chunk(chunk)
            pos += CHUNK_STRIDE
            if pos >= len(text):
                break

    # ── Búsqueda ──────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 5,
               domain_filter: str = "") -> list[SearchResult]:
        if not self._built:
            self.build()

        tokens  = self._tokenize(query)
        N       = len(self.chunks)
        scores  = defaultdict(float)

        for term in set(tokens):
            postings = self._inv.get(term, [])
            df = len(postings)
            if df == 0:
                continue
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
            for idx, tf in postings:
                dl    = self._dl[idx]
                denom = tf + self.k1 * (1 - self.b + self.b * dl / self._avgdl)
                tf_n  = tf * (self.k1 + 1) / denom
                scores[idx] += idf * tf_n

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in ranked:
            chunk = self.chunks[idx]
            if domain_filter and chunk.domain != domain_filter:
                continue
            snippet = self._make_snippet(chunk.text, tokens)
            results.append(SearchResult(chunk=chunk, score=round(score, 4), snippet=snippet))
            if len(results) >= top_k:
                break

        return results

    @staticmethod
    def _make_snippet(text: str, tokens: list[str], window: int = 300) -> str:
        lower = text.lower()
        best_pos = 0
        for t in tokens:
            p = lower.find(t)
            if p != -1:
                best_pos = p
                break
        start = max(0, best_pos - 100)
        end   = min(len(text), start + window)
        snippet = text[start:end].strip()
        if start > 0:
            snippet = "…" + snippet
        if end < len(text):
            snippet = snippet + "…"
        return snippet

    # ── Fichas de conocimiento ─────────────────────────────────────────────────

    def get_ficha(self, domain: str) -> str | None:
        """Devuelve el texto completo de la ficha de conocimiento para un dominio."""
        for root in CORPUS_ROOTS:
            candidates = [
                root / domain / f"{domain}_base.md",
                root / domain / f"{domain}.md",
            ]
            for c in candidates:
                if c.exists():
                    return c.read_text(encoding="utf-8", errors="replace")
        return None

    def list_sources(self) -> list[dict]:
        """Lista todos los documentos indexados con su dominio y número de chunks."""
        if not self._built:
            self.build()
        seen: dict[str, dict] = {}
        for chunk in self.chunks:
            if chunk.source not in seen:
                seen[chunk.source] = {
                    "source": chunk.source,
                    "domain": chunk.domain,
                    "path":   chunk.path,
                    "chunks": 0,
                }
            seen[chunk.source]["chunks"] += 1
        return sorted(seen.values(), key=lambda x: x["source"])
