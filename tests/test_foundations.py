"""Foundations experiments are mathematical toys or measured tokenizer fixtures."""

import math

import pytest

from carrito.foundations import (
    conditional_probabilities,
    greedy_demo,
    load_tokenization_examples,
    softmax,
)


def test_softmax_matches_known_distribution_and_is_stable():
    expected = [0.66524096, 0.24472847, 0.09003057]
    assert softmax([2, 1, 0]) == pytest.approx(expected)
    assert softmax([1002, 1001, 1000]) == pytest.approx(expected)
    assert sum(softmax([2, 1, 0])) == pytest.approx(1)


def test_temperature_changes_concentration_without_changing_ranking():
    cold, normal, warm = [softmax([2, 1, 0], temperature=t) for t in [0.5, 1, 2]]
    assert cold[0] > normal[0] > warm[0]
    assert all(row[0] > row[1] > row[2] for row in [cold, normal, warm])


@pytest.mark.parametrize("temperature", [0, -1, math.nan, math.inf])
def test_softmax_rejects_undefined_temperature(temperature):
    with pytest.raises(ValueError):
        softmax([2, 1, 0], temperature)


@pytest.mark.parametrize("logits", [[], [math.nan, 0], [math.inf, 0]])
def test_softmax_rejects_invalid_logits(logits):
    with pytest.raises(ValueError):
        softmax(logits)


def test_context_changes_conditional_distribution_in_fixed_toy():
    cart = conditional_probabilities("El pedido llega")
    price = conditional_probabilities("El pedido sale")
    assert max(cart, key=cart.get) == "mañana"
    assert max(price, key=price.get) == "hoy"
    assert sum(cart.values()) == pytest.approx(1)
    assert conditional_probabilities("El pedido llega") == cart


def test_greedy_trace_recomputes_after_each_new_token():
    trace = greedy_demo()
    assert [row["next_token"] for row in trace] == ["El", "pedido", "llega", "mañana", "<fin>"]
    assert trace[1]["prefix"] == "El"
    assert trace[4]["prefix"] == "El pedido llega mañana"
    assert all(
        row["next_token"] == max(row["probabilities"], key=row["probabilities"].get)
        for row in trace
    )


def test_measured_tokenizer_fixture_is_named_and_lossless():
    fixture = load_tokenization_examples()
    assert fixture["encoding"] == "cl100k_base"
    assert fixture["kind"] == "measured_tokenization_not_model_inference"
    for row in fixture["examples"]:
        assert len(row["token_ids"]) == len(row["pieces"]) == row["token_count"]
        assert (
            b"".join(bytes.fromhex(piece["bytes_hex"]) for piece in row["pieces"]).decode()
            == row["text"]
        )
    assert any(row["token_count"] != len(row["text"].split()) for row in fixture["examples"])
