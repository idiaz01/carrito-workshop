"""S3 · RAG configurable. Students edit mi_agente/rag.toml; the code stays the same.

Three decisions, one file:
- fuentes:  which documents can be found (policies, help center).
- trocear:  how a document becomes searchable pieces (document, section, sentence).
- metodo:   how pieces are ranked (shared words, embeddings, or both).
"""

import hashlib
import json
import math
import os
import re
import tomllib
from pathlib import Path

from carrito.store import ROOT
from carrito.texto import normalize
from carrito.tools import words

SOURCES = {"politicas": ROOT / "data" / "policies", "ayuda": ROOT / "data" / "ayuda"}
CHUNKING = ("documento", "seccion", "frase")
METHODS = ("lexico", "embeddings", "hibrido")
DEFAULTS = {"fuentes": ["politicas"], "trocear": "documento", "metodo": "lexico", "top_k": 2}
CASES = ROOT / "evals" / "s3_rag.jsonl"
CACHE = ROOT / "runtime" / "embeddings"
EMBEDDING_MODEL = "text-embedding-3-small"
RRF_K = 60


class ConfigError(ValueError):
    pass


def load_config(path):
    """Read rag.toml. Unknown or invalid values raise ConfigError with a Spanish message."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"rag.toml no es TOML válido: {exc}") from None
    config = dict(DEFAULTS)
    for section in ("documentos", "busqueda"):
        config.update(raw.get(section, {}))
    fuentes = config["fuentes"]
    if isinstance(fuentes, str):
        fuentes = [fuentes]
    unknown = [f for f in fuentes if f not in SOURCES]
    if not fuentes or unknown:
        raise ConfigError(f"fuentes: usa una lista con {list(SOURCES)}. No conozco: {unknown}")
    if config["trocear"] not in CHUNKING:
        raise ConfigError(f"trocear: usa uno de {list(CHUNKING)}")
    if config["metodo"] not in METHODS:
        raise ConfigError(f"metodo: usa uno de {list(METHODS)}")
    top_k = config["top_k"]
    if not isinstance(top_k, int) or not 1 <= top_k <= 10:
        raise ConfigError("top_k: usa un número entero entre 1 y 10")
    config["fuentes"] = list(fuentes)
    return config


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def _parse(path):
    """A document has one '# ID · Título' line and optional '## Sección' blocks."""
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    title = lines[0].lstrip("# ").strip()
    sections, current = [], None
    intro = []
    for line in lines[1:]:
        if line.startswith("## "):
            current = {"section": line[3:].strip(), "lines": []}
            sections.append(current)
        elif current is None:
            intro.append(line)
        else:
            current["lines"].append(line)
    body = "\n".join(intro).strip()
    if body:
        sections.insert(0, {"section": None, "lines": intro})
    return title, sections


def _sentences(lines):
    """Each non-empty line of a help document is one statement."""
    return [line.strip() for line in lines if line.strip()]


def chunk_documents(fuentes, trocear):
    """Return the searchable pieces. Each piece keeps its source ID and its sections."""
    chunks = []
    for fuente in fuentes:
        for path in sorted(SOURCES[fuente].glob("*.md")):
            source_id = path.stem
            title, sections = _parse(path)
            names = [s["section"] for s in sections if s["section"]]
            if trocear == "documento" or not names:
                text = path.read_text(encoding="utf-8").strip()
                chunks.append(_chunk(source_id, title, names, text, f"{source_id}"))
                continue
            for k, section in enumerate(sections, 1):
                label = section["section"] or "Introducción"
                head = f"{title} · {label}"
                if trocear == "seccion":
                    body = "\n".join(section["lines"]).strip()
                    chunks.append(
                        _chunk(
                            source_id,
                            title,
                            [section["section"]],
                            f"{head}\n{body}",
                            f"{source_id}#{k}",
                        )
                    )
                else:
                    for p, sentence in enumerate(_sentences(section["lines"]), 1):
                        chunks.append(
                            _chunk(
                                source_id,
                                title,
                                [section["section"]],
                                f"{head}\n{sentence}",
                                f"{source_id}#{k}.{p}",
                            )
                        )
    return chunks


def _chunk(source_id, title, sections, text, chunk_id):
    return {
        "chunk_id": chunk_id,
        "source_id": source_id,
        "title": title,
        "sections": [s for s in sections if s],
        "text": text,
    }


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------
def lexical_ranking(query, chunks):
    tokens = words(query)
    scored = [(len(tokens & words(c["text"])), c) for c in chunks]
    scored = [(s, c) for s, c in scored if s > 0]
    scored.sort(key=lambda sc: (-sc[0], sc[1]["chunk_id"]))
    return [(float(s), c) for s, c in scored]


def _fake_vector(text, dims=256):
    """Offline checks only: a deterministic bag-of-words vector. Not semantic."""
    vector = [0.0] * dims
    for word in words(text):
        digest = hashlib.sha256(word.encode()).digest()
        vector[int.from_bytes(digest[:4], "big") % dims] += 1.0
    return vector


def embed(texts, client=None):
    """Embeddings with a local cache in runtime/embeddings/. Only new texts call the API."""
    from carrito.model import load_settings, make_client, offline_check

    load_settings()
    model = os.getenv("OPENAI_EMBEDDING_MODEL", EMBEDDING_MODEL)
    if offline_check() and client is None:
        return [_fake_vector(t) for t in texts]
    cache_file = CACHE / f"{model}.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    keys = [hashlib.sha256(t.encode()).hexdigest()[:16] for t in texts]
    missing = [t for t, k in zip(texts, keys) if k not in cache]
    if missing:
        client = client or make_client()
        for start in range(0, len(missing), 64):
            batch = missing[start : start + 64]
            response = client.embeddings.create(model=model, input=batch)
            for text, item in zip(batch, response.data):
                cache[hashlib.sha256(text.encode()).hexdigest()[:16]] = item.embedding
        CACHE.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cache), encoding="utf-8")
    return [cache[k] for k in keys]


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def embedding_ranking(query, chunks, client=None):
    vectors = embed([c["text"] for c in chunks] + [query], client=client)
    query_vector = vectors[-1]
    scored = [(_cosine(query_vector, v), c) for v, c in zip(vectors[:-1], chunks)]
    scored.sort(key=lambda sc: (-sc[0], sc[1]["chunk_id"]))
    return scored


def hybrid_ranking(query, chunks, client=None):
    """Reciprocal Rank Fusion: a piece ranked high by either method rises."""
    fused = {}
    for ranking in (lexical_ranking(query, chunks), embedding_ranking(query, chunks, client)):
        for position, (_, chunk) in enumerate(ranking, 1):
            entry = fused.setdefault(chunk["chunk_id"], [0.0, chunk])
            entry[0] += 1 / (RRF_K + position)
    scored = sorted(fused.values(), key=lambda sc: (-sc[0], sc[1]["chunk_id"]))
    return [(round(s, 5), c) for s, c in scored]


RANKERS = {"lexico": lexical_ranking, "embeddings": embedding_ranking, "hibrido": hybrid_ranking}


def search(query, config, chunks=None, client=None):
    chunks = chunks if chunks is not None else chunk_documents(config["fuentes"], config["trocear"])
    ranker = RANKERS[config["metodo"]]
    ranking = ranker(query, chunks) if ranker is lexical_ranking else ranker(query, chunks, client)
    return [
        {
            "source_id": c["source_id"],
            "section": ", ".join(c["sections"]) or None,
            "text": c["text"],
            "score": round(score, 4),
            "chunk_id": c["chunk_id"],
        }
        for score, c in ranking[: config["top_k"]]
    ]


# ---------------------------------------------------------------------------
# Measuring retrieval (S3 · Paso 2)
# ---------------------------------------------------------------------------
def load_cases(path=CASES):
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _hit(result, case):
    """A piece answers the question if it comes from an expected source and contains the key
    fact. Example: R2 needs the sentence «no enviamos baterías…», not only the Canarias price."""
    return result["source_id"] in case["fuentes"] and normalize(case["clave"]) in normalize(
        result["text"]
    )


def estimate_tokens(text):
    return round(len(text) / 4)


def evaluate(config, cases=None, client=None):
    chunks = chunk_documents(config["fuentes"], config["trocear"])
    rows = []
    for case in cases or load_cases():
        results = search(case["pregunta"], config, chunks, client)
        rows.append(
            {
                "id": case["id"],
                "pregunta": case["pregunta"],
                "acierto": any(_hit(r, case) for r in results),
                "encontrado": [r["chunk_id"] for r in results],
                "esperado": f"{' o '.join(case['fuentes'])} con «{case['clave']}»",
                "tokens": sum(estimate_tokens(r["text"]) for r in results),
            }
        )
    return {
        "config": config,
        "piezas": len(chunks),
        "aciertos": sum(r["acierto"] for r in rows),
        "total": len(rows),
        "tokens_medios": round(sum(r["tokens"] for r in rows) / len(rows)),
        "casos": rows,
    }


def render_evaluation(report):
    c = report["config"]
    lines = [
        f"rag.toml → fuentes={c['fuentes']} · trocear={c['trocear']} · metodo={c['metodo']}"
        f" · top_k={c['top_k']}  ({report['piezas']} piezas)",
        "",
        f"{'Caso':<5} {'':<3} {'Tokens':>6}  Pregunta → encontrado",
    ]
    for row in report["casos"]:
        mark = "✅" if row["acierto"] else "❌"
        found = ", ".join(row["encontrado"]) or "nada"
        lines.append(f"{row['id']:<5} {mark:<3} {row['tokens']:>6}  {row['pregunta']}")
        missing = "" if row["acierto"] else f"   (esperado: {row['esperado']})"
        lines.append(f"{'':<16}→ {found}{missing}")
    lines.append(
        f"\nRECUPERACIÓN: {report['aciertos']}/{report['total']} aciertos · "
        f"{report['tokens_medios']} tokens de contexto por pregunta"
    )
    return "\n".join(lines)


def render_search(query, results):
    lines = [f"Pregunta: {query}"]
    for k, r in enumerate(results, 1):
        preview = re.sub(r"\s+", " ", r["text"])[:140]
        lines.append(f"  {k}. {r['chunk_id']:<12} score={r['score']:<8} {preview}")
    if not results:
        lines.append("  (nada: ninguna pieza comparte palabras con la pregunta)")
    return "\n".join(lines)
