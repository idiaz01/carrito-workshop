"""Inspectable S1 experiments. The probability table is a word-level toy, not an LLM."""

import json
import math

from carrito.store import ROOT

VOCABULARY = ("El", "pedido", "llega", "sale", "mañana", "hoy", "tarde", "<fin>")
# Fixed hand-written scores; not a delivery prediction or a trained language model.
TOY_LOGITS = {
    "": (3, 0, 0, -2, -2, -2, -2, -3),
    "El": (-2, 3, 0, -2, -2, -2, -2, -3),
    "El pedido": (-2, -2, 3, 1, -2, -2, -2, -3),
    "El pedido llega": (-3, -3, -3, -3, 2, 1, 0, -3),
    "El pedido llega mañana": (-3, -3, -3, -3, -3, -3, -3, 3),
    "El pedido sale": (-3, -3, -3, -3, 0, 3, 1, -3),
}


def softmax(logits, temperature=1.0):
    """p_i = exp(z_i/T) / sum_j exp(z_j/T), for finite logits and T > 0."""
    if not logits or not all(math.isfinite(value) for value in logits):
        raise ValueError("Provide a nonempty sequence of finite logits")
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("Temperature must be finite and strictly positive")
    maximum = max(logits)
    scores = [math.exp((value - maximum) / temperature) for value in logits]
    total = sum(scores)
    return [value / total for value in scores]


def conditional_probabilities(prefix, temperature=1.0):
    """Only the six explicit prefixes in TOY_LOGITS exist in this teaching toy."""
    return dict(zip(VOCABULARY, softmax(TOY_LOGITS[prefix], temperature), strict=True))


def greedy_demo():
    """Recompute the toy's next-token distribution after appending each chosen token."""
    prefix = ""
    trace = []
    for _ in range(5):
        probabilities = conditional_probabilities(prefix)
        token = max(probabilities, key=probabilities.get)
        trace.append({"prefix": prefix, "probabilities": probabilities, "next_token": token})
        if token == "<fin>":
            break
        prefix = (prefix + " " + token).strip()
    return trace


def load_tokenization_examples():
    """Read measured, labelled token IDs without installing a tokenizer at lesson time."""
    return json.loads((ROOT / "data/foundations/tokenization.json").read_text())
