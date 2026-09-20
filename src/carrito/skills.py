"""Small visible Skill activation, without a second agent runtime."""

from carrito.store import ROOT
from carrito.tools import words


def activate_skill(prompt: str) -> dict | None:
    if not words(prompt) & {"devolver", "devolucion", "devoluciones"}:
        return None
    path = ROOT / "examples" / "skills" / "return-help" / "SKILL.md"
    return {"name": "return-help", "path": str(path), "content": path.read_text()}
