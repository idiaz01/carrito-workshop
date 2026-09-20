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


class ReturnArgs(OrderArgs):
    reason: str = Field(min_length=1, max_length=500, pattern=r"\S")


ARGUMENTS = {
    "search_products": ProductArgs,
    "get_order": OrderArgs,
    "search_policies": PolicyArgs,
    "request_return": ReturnArgs,
}
DESCRIPTIONS = {
    "search_products": "Search the catalog. Prices in cents; optional budget in euros.",
    "get_order": "Read one order belonging to the host's active user.",
    "search_policies": "Retrieve short policy documents with source IDs.",
    "request_return": "Prepare a return request; only host-confirmed exact payloads can write.",
}


def tool_definitions() -> list[dict]:
    definitions = []
    for name, schema in ARGUMENTS.items():
        parameters = schema.model_json_schema()
        # Strict native tools require every property, including nullable fields.
        parameters["required"] = list(parameters["properties"])
        for prop in parameters["properties"].values():
            prop.pop("default", None)
        definitions.append(
            {
                "type": "function",
                "name": name,
                "description": DESCRIPTIONS[name],
                "parameters": parameters,
                "strict": True,
            }
        )
    return definitions


class StoreTools:
    def __init__(self, db: sqlite3.Connection, user_id: str = "user1", policy_retriever=None):
        if user_id not in {"user1", "user2"}:
            raise ValueError("Unknown host user")
        self.db = db
        self.policy_retriever = policy_retriever
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
            body = path.read_text()
            score = len(tokens & words(body))
            if score or not tokens:
                documents.append({"source_id": path.stem, "text": body, "score": score})
        return sorted(documents, key=lambda r: (-r["score"], r["source_id"]))

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
        if name not in ARGUMENTS:
            return {"error": "unknown_tool", "tool": name}
        try:
            validated = ARGUMENTS[name].model_validate(arguments)
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
