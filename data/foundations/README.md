# S1 · Qué está medido y qué es ilustrativo

**Medido.** `tokenization.json` contiene la tokenización de seis textos con **tiktoken 0.14.0 / cl100k_base** (20 de septiembre de 2026).
- IDs: `get_encoding(...).encode(text)`. Piezas: `decode_single_token_bytes(id)`.
- `bytes_hex` reconstruye el texto completo. `display` facilita la lectura.
- El tokenizer del modelo de la clase puede ser distinto. Los IDs no indican cercanía semántica.

**Ilustrativo.** `carrito.foundations` tiene un **toy de ocho palabras** con logits escritos a mano.
- Enseña probabilidad condicional y generación autoregresiva con «El pedido llega mañana».
- La demo de temperatura normaliza `[2, 1, 0]` entre «mañana», «hoy» y «tarde».
- No es un modelo entrenado. No predice entregas reales.

`uv run python examples/foundations.py` muestra las dos demos sin API. Ninguna celda entrena pesos.
Referencia: [tiktoken](https://github.com/openai/tiktoken).
