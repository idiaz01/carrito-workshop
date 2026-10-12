"""Fake OpenAI client for CI and tests. Not a model: it returns empty answers.

It is active only when CARRITO_OFFLINE_CHECK=1. The class never uses it.
"""

from types import SimpleNamespace
from typing import Literal, get_args, get_origin

TEXT = "[comprobación offline] Sin modelo."


def _usage():
    return SimpleNamespace(model_dump=lambda: {"input_tokens": 0, "output_tokens": 0})


def _placeholder(model_class):
    values = {}
    for name, field in model_class.model_fields.items():
        kind = field.annotation
        if get_origin(kind) is Literal:
            options = get_args(kind)
            values[name] = "no_match" if "no_match" in options else options[0]
        elif kind is bool:
            values[name] = False
        elif kind is str:
            values[name] = TEXT
        elif get_origin(kind) is list:
            values[name] = []
        elif kind in {int, float}:
            values[name] = 0
        else:
            values[name] = None
    return model_class.model_validate(values)


class _Responses:
    def create(self, **kwargs):
        message = {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": TEXT}],
        }
        return SimpleNamespace(
            output=[message],
            output_text=TEXT,
            usage=_usage(),
            status="completed",
            model="offline-check",
        )

    def parse(self, text_format=None, **kwargs):
        response = self.create(**kwargs)
        response.output_parsed = _placeholder(text_format) if text_format else None
        return response


class OfflineClient:
    def __init__(self):
        self.responses = _Responses()
