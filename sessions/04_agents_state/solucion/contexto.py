import json
import re


def format_tool_result(name, result):
    if isinstance(result, dict) and "error" in result:
        return json.dumps(result, ensure_ascii=False)
    if name == "search_products":
        products = [
            {
                "product_id": p["product_id"],
                "name": p["name"],
                "precio": f"{p['price_cents'] / 100:.2f}".replace(".", ",") + " €",
                "description": p["description"],
            }
            for p in result
        ]
        return json.dumps(products, ensure_ascii=False)
    if name == "search_policies":
        # S3: rag.toml decide cuántas piezas llegan (top_k). Aquí no recortamos más.
        documents = [{"source_id": d["source_id"], "text": d["text"]} for d in result]
        return json.dumps(documents, ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False)


def update_state(state, user_message):
    new = dict(state)
    amount = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:€|euros)", user_message)
    if amount:
        new["presupuesto_eur"] = float(amount.group(1).replace(",", "."))
    name = re.search(r"(?:me llamo|soy)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)", user_message)
    if name:
        new["nombre"] = name.group(1)
    return new


def build_history(turns, state, max_turns=2):
    messages = []
    if state:
        summary = "; ".join(f"{k}={v}" for k, v in state.items())
        messages.append({"role": "system", "content": f"Estado de la conversación: {summary}"})
    for turn in turns[-max_turns:]:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["assistant"]})
    return messages
