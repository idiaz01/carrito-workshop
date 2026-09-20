"""Small inspectable lexical retrieval experiment. No pretend semantic embeddings."""

import json

from carrito.store import ROOT
from carrito.tools import words

EXPANSIONS = {
    "reintegro": {"devolucion"},
    "rembolso": {"devolucion"},
    "tardar": {"envio"},
    "arrepentimiento": {"devolucion"},
}


def load_chunks():
    rows = []
    for path in sorted((ROOT / "data" / "policies").glob("*.md")):
        text = path.read_text()
        # Policies are already short semantic units: preserve each complete policy.
        rows.append(
            {
                "chunk_id": path.stem + "#1",
                "source_id": path.stem,
                "text": text,
                "metadata": {
                    "kind": "policy",
                    "language": "es",
                    "path": str(path.relative_to(ROOT)),
                },
            }
        )
    return rows


def retrieve(query, chunks, top_k=2, expand=False):
    if top_k < 1:
        raise ValueError("top_k must be positive")
    tokens = words(query)
    if expand:
        tokens |= set().union(*(EXPANSIONS.get(token, set()) for token in tokens))
    scored = [{**chunk, "score": len(tokens & words(chunk["text"]))} for chunk in chunks]
    return sorted((r for r in scored if r["score"]), key=lambda r: (-r["score"], r["chunk_id"]))[
        :top_k
    ]


def retrieval_report(chunks=None, top_k=2, expand=False):
    cases = json.loads((ROOT / "data" / "retrieval-cases.json").read_text())
    rows = []
    for case in cases:
        hits = retrieve(case["query"], chunks or load_chunks(), top_k, expand)
        actual = {hit["source_id"] for hit in hits}
        relevant = set(case["relevant_ids"])
        rows.append(
            {
                **case,
                "retrieved_ids": [hit["source_id"] for hit in hits],
                "recall": len(actual & relevant) / len(relevant),
                "precision": len(actual & relevant) / len(actual) if actual else 0,
            }
        )
    return {
        "method": "lexical overlap + explicit query expansion" if expand else "lexical overlap",
        "top_k": top_k,
        "cases": rows,
        "mean_recall": sum(row["recall"] for row in rows) / len(rows),
        "mean_precision": sum(row["precision"] for row in rows) / len(rows),
    }
