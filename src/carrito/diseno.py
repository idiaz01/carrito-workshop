"""S4 · Diseño del agente: límites del loop, rutas (workflows) y subagente.

Students edit mi_agente/agente.toml. Without that file the agent behaves as in S3.
"""

import tomllib
from pathlib import Path

from carrito.tools import words

LIMITS = {"max_pasos": (1, 20), "max_tools": (1, 30), "max_tokens": (1000, 100000)}
DEFAULT_LIMITS = {"max_pasos": 5, "max_tools": 12, "max_tokens": 16000}
ROUTE_TYPES = ("fija", "buscar")


class ConfigError(ValueError):
    pass


def load(path):
    """Read agente.toml. Return None if it does not exist. Invalid values raise ConfigError."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"agente.toml no es TOML válido: {exc}") from None
    limits = dict(DEFAULT_LIMITS)
    limits.update(raw.get("limites", {}))
    for name, (low, high) in LIMITS.items():
        value = limits[name]
        if not isinstance(value, int) or not low <= value <= high:
            raise ConfigError(f"limites.{name}: usa un número entero entre {low} y {high}")
    routes = raw.get("rutas", [])
    if not isinstance(routes, list):
        raise ConfigError("rutas: cada ruta empieza con [[rutas]], con dos corchetes")
    for k, route in enumerate(routes, 1):
        if route.get("tipo") not in ROUTE_TYPES:
            raise ConfigError(f"rutas #{k}: tipo tiene que ser {' o '.join(ROUTE_TYPES)}")
        palabras = route.get("palabras")
        if not isinstance(palabras, list) or not palabras:
            raise ConfigError(f'rutas #{k}: palabras tiene que ser una lista, como ["poema"]')
        if route["tipo"] == "fija" and not str(route.get("respuesta", "")).strip():
            raise ConfigError(f'rutas #{k}: una ruta fija necesita respuesta = "..."')
    subagent = raw.get("subagente", {})
    if not isinstance(subagent, dict) or not isinstance(subagent.get("activo", False), bool):
        raise ConfigError("subagente.activo tiene que ser true o false")
    return {
        "limites": limits,
        "rutas": routes,
        "subagente": {"activo": subagent.get("activo", False)},
    }


def choose_route(text, routes):
    """The first route that shares a word with the message. None means: the agent decides."""
    tokens = words(text)
    for route in routes:
        if tokens & words(" ".join(route["palabras"])):
            return route
    return None


def seen_ids(events):
    """IDs that came out of a tool in this turn: what the agent may cite."""
    seen = set()

    def walk(value):
        if isinstance(value, dict):
            for key in ("product_id", "source_id", "order_id"):
                if isinstance(value.get(key), str):
                    seen.add(value[key])
                    if key == "order_id":
                        seen.add(f"pedido {value[key]}")
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    for event in events:
        if event.get("type") == "tool_result":
            walk(event.get("result"))
    return seen


def strict_schema(model):
    """A Pydantic model as an OpenAI strict JSON schema (every field required, no extras)."""
    schema = model.model_json_schema()

    def fix(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                node["additionalProperties"] = False
                node["required"] = list(node["properties"])
            node.pop("default", None)
            if isinstance(node.get("title"), str):
                node.pop("title")
            for value in node.values():
                fix(value)
        elif isinstance(node, list):
            for value in node:
                fix(value)

    fix(schema)
    return {"type": "json_schema", "name": "respuesta", "schema": schema, "strict": True}
