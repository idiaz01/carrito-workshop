"""Offline S1 teacher demo: measured tokenization and a hand-written probability toy."""

import json

from carrito.foundations import (
    conditional_probabilities,
    greedy_demo,
    load_tokenization_examples,
    softmax,
)


def main():
    print(json.dumps(load_tokenization_examples(), ensure_ascii=False, indent=2))
    print("TOY ONLY: fixed logits [2, 1, 0]; these are not measured LLM probabilities.")
    for temperature in [0.5, 1, 2]:
        print("temperature", temperature, "probabilities", softmax([2, 1, 0], temperature))
    for prefix in ["El pedido llega", "El pedido sale"]:
        print(prefix, conditional_probabilities(prefix))
    print(json.dumps(greedy_demo(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
