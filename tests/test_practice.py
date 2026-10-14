from carrito import practice
from carrito.context import ConversationState


def test_incomplete_lab_cells_give_pendiente_and_never_raise():
    assert not practice.run("t1", practice.lab1_origin, {p: ... for p in practice.LAB1_PIECES})
    assert not practice.run("t2", practice.lab1_authority, {...})
    assert not practice.run("t3", practice.lab2_selection, [...], [], 250)
    assert not practice.run("t4", practice.lab3_rules, lambda *a: ..., {"P001": 69.9})
    assert not practice.run("t5", practice.lab4_update, lambda *a, **k: ...)
    assert not practice.run("t6", practice.lab5_state, ...)
    assert not practice.run("t7", practice.lab5_evidence, [...])


def test_lab4_rejects_mutation_of_previous_state():
    def mutate(previous, budget_eur=None, preference=None):
        previous.budget_eur = budget_eur or previous.budget_eur
        return previous

    passed, detail = practice.lab4_update(mutate)
    assert not passed and "anterior" in detail
    assert isinstance(ConversationState(), ConversationState)
