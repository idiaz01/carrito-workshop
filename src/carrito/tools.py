"""Cuatro tools: validación, identidad y permisos residen en Python."""

import json
import re
import sqlite3
import unicodedata
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from carrito.store import REFERENCE_DATE, ROOT


def words(text: str) -> set[str]:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    stop = {"de", "la", "el", "los", "las", "un", "una", "por", "para", "que", "puedo"}
    return set(re.findall(r"[a-z0-9]+", text)) - stop


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProductArgs(Arguments):
    query: str = Field(max_length=500)
    max_price_eur: float | None = Field(default=None, ge=0, le=100000)


class OrderArgs(Arguments):
    order_id: str = Field(min_length=1, max_length=30)


class PolicyArgs(Arguments):
    query: str = Field(max_length=500)


class NoArgs(Arguments):
    pass


class ReturnArgs(OrderArgs):
    reason: str = Field(min_length=1, max_length=500, pattern=r"\S")


ARGUMENTS = {
    "search_products": ProductArgs,
    "get_order": OrderArgs,
    "search_policies": PolicyArgs,
    "request_return": ReturnArgs,
}
# Tools the student adds from S3 on. They are offered only when the agent asks for them.
EXTRA_ARGUMENTS = {"plazo_devolucion": OrderArgs, "mis_pedidos": NoArgs}
DESCRIPTIONS = {
    "search_products": "Search the catalog. Prices in cents; optional budget in euros.",
    "get_order": "Read one order belonging to the host's active user.",
    "search_policies": "Retrieve short policy documents with source IDs.",
    "request_return": "Prepare a return request; only host-confirmed exact payloads can write.",
    "plazo_devolucion": "Return deadline of one order of the active user.",
    "mis_pedidos": (
        "Lista los pedidos del cliente activo: número, producto, estado y fecha de entrega. "
        "Úsala cuando el cliente pregunte por sus pedidos sin dar un número. Sin argumentos."
    ),
}


def tool_definitions(descriptions: dict | None = None, extra=()) -> list[dict]:
    """Native tool definitions. `descriptions` overrides the text the model reads.
    `extra` adds student tools (S3+) by name, for example ("plazo_devolucion",)."""
    definitions = []
    schemas = {**ARGUMENTS, **{name: EXTRA_ARGUMENTS[name] for name in extra}}
    for name, schema in schemas.items():
        parameters = schema.model_json_schema()
        # Strict native tools require every property, including nullable fields.
        parameters["required"] = list(parameters["properties"])
        for prop in parameters["properties"].values():
            prop.pop("default", None)
        definitions.append(
            {
                "type": "function",
                "name": name,
                "description": (descriptions or {}).get(name) or DESCRIPTIONS[name],
                "parameters": parameters,
                "strict": True,
            }
        )
    return definitions


class StoreTools:
    def __init__(
        self,
        db: sqlite3.Connection,
        user_id: str = "user1",
        policy_retriever=None,
        deadline_function=None,
    ):
        if user_id not in {"user1", "user2"}:
            raise ValueError("Unknown host user")
        self.db = db
        self.policy_retriever = policy_retriever
        # S3: the student's plazo_devolucion(pedido, producto, hoy) from mi_agente/herramientas.py
        self.deadline_function = deadline_function
        self.user_id = user_id
        self.pending: tuple[str, str] | None = None
        self._confirmed: tuple[str, str] | None = None

    def search_products(self, query: str, max_price_eur: float | None = None) -> list[dict]:
        args = ProductArgs(query=query, max_price_eur=max_price_eur)
        tokens = words(args.query)
        rows = [dict(r) for r in self.db.execute("SELECT * FROM products ORDER BY product_id")]
        return [
            r
            for r in rows
            if (not tokens or tokens & words(r["name"] + " " + r["description"]))
            and (
                args.max_price_eur is None
                or r["price_cents"] <= Decimal(str(args.max_price_eur)) * 100
            )
        ]

    def get_order(self, order_id: str) -> dict:
        OrderArgs(order_id=order_id)
        row = self.db.execute(
            "SELECT * FROM orders WHERE order_id=? AND user_id=?", (order_id, self.user_id)
        ).fetchone()
        return dict(row) if row else {"error": "order_not_found"}

    def search_policies(self, query: str) -> list[dict]:
        PolicyArgs(query=query)
        if self.policy_retriever is not None:
            return self.policy_retriever(query)
        tokens = words(query)
        documents = []
        for path in sorted((ROOT / "data" / "policies").glob("*.md")):
            body = path.read_text(encoding="utf-8")
            score = len(tokens & words(body))
            if score or not tokens:
                documents.append({"source_id": path.stem, "text": body, "score": score})
        return sorted(documents, key=lambda r: (-r["score"], r["source_id"]))

    def mis_pedidos(self) -> list[dict]:
        """S4 host tool: the active user's orders (PER-1), with the product name."""
        rows = self.db.execute(
            "SELECT o.order_id, o.product_id, p.name, o.status, o.delivered_at "
            "FROM orders o JOIN products p ON p.product_id = o.product_id "
            "WHERE o.user_id = ? ORDER BY o.order_id",
            (self.user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def plazo_devolucion(self, order_id: str) -> dict:
        """S3 student tool. The host reads the order (identity, PER-1); the student computes."""
        order = self.get_order(order_id)
        if "error" in order or self.deadline_function is None:
            return order if "error" in order else {"error": "tool_unavailable"}
        product = self.db.execute(
            "SELECT * FROM products WHERE product_id=?", (order["product_id"],)
        ).fetchone()
        return self.deadline_function(order, dict(product), REFERENCE_DATE)

    def confirm_pending(self) -> dict:
        """Trusted host/UI action. Never expose this method as a model tool."""
        if self.pending is None:
            return {"error": "nothing_to_confirm"}
        self._confirmed = self.pending
        return {"status": "confirmed", "order_id": self.pending[0], "reason": self.pending[1]}

    def request_return(self, order_id: str, reason: str) -> dict:
        ReturnArgs(order_id=order_id, reason=reason)
        order = self.get_order(order_id)
        if "error" in order:
            return order
        existing = self.db.execute(
            "SELECT * FROM return_requests WHERE order_id=? AND user_id=?", (order_id, self.user_id)
        ).fetchone()
        if existing:
            return {"status": "requested", **dict(existing), "duplicate": True}
        if order["status"] != "delivered":
            return {"error": "not_delivered"}
        if (REFERENCE_DATE - date.fromisoformat(order["delivered_at"])).days > 30:
            return {"error": "return_window_expired", "source_id": "POL-DEV"}
        product = self.db.execute(
            "SELECT returnable FROM products WHERE product_id=?", (order["product_id"],)
        ).fetchone()
        if not product[0]:
            return {"error": "non_returnable", "source_id": "POL-EXC"}
        payload = (order_id, reason)
        if self.pending != payload or self._confirmed != payload:
            self.pending = payload
            self._confirmed = None
            return {"status": "confirmation_required", "order_id": order_id, "reason": reason}
        with self.db:
            cursor = self.db.execute(
                "INSERT INTO return_requests(order_id,user_id,reason,requested_at) VALUES(?,?,?,?)",
                (order_id, self.user_id, reason, REFERENCE_DATE.isoformat()),
            )
        self.pending = self._confirmed = None
        return {
            "status": "requested",
            "request_id": cursor.lastrowid,
            "order_id": order_id,
            "reason": reason,
            "duplicate": False,
        }

    def return_count(self) -> int:
        return self.db.execute("SELECT count(*) FROM return_requests").fetchone()[0]

    def dispatch(self, name: str, arguments: dict) -> dict | list:
        schemas = {**ARGUMENTS, **EXTRA_ARGUMENTS}
        if name not in schemas:
            return {"error": "unknown_tool", "tool": name}
        try:
            validated = schemas[name].model_validate(arguments)
            return getattr(self, name)(**validated.model_dump())
        except ValidationError as exc:
            return {
                "error": "invalid_arguments",
                "details": json.loads(exc.json(include_url=False)),
            }
        except sqlite3.Error:
            return {
                "error": "storage_error",
                "message": "Local store unavailable; no success assumed.",
            }
