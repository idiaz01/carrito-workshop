# S1 · Qué está medido y qué es ilustrativo

`tokenization.json` contiene tokenización medida de seis textos originales con **tiktoken 0.14.0 / cl100k_base**, el 20 de septiembre de 2026. Se obtuvieron IDs mediante `get_encoding(...).encode(text)` y piezas mediante `decode_single_token_bytes(id)`. No hubo inferencia, llamada API ni descarga de pesos de un modelo. La preparación leyó el vocabulario del tokenizer; el notebook solo lee este JSON y no requiere tiktoken instalado ni acceso a red.

El nombre de la codificación está fijado: no se afirma que corresponda al modelo configurable de la clase. Un token puede ser un fragmento de palabra, puntuación, espacio o cifra. `bytes_hex` permite reconstruir el texto completo sin perder bytes; `display` facilita inspeccionarlo. Los IDs no representan cercanía semántica. Referencia: [repositorio oficial de tiktoken](https://github.com/openai/tiktoken).

`carrito.foundations` contiene un **toy de ocho palabras**, con logits manuales. Enseña probabilidad condicional y generación autoregresiva mediante «El pedido llega mañana». No es un modelo entrenado ni predice una entrega real. El experimento separado de temperatura normaliza `[2,1,0]` entre tres candidatos: mañana, hoy, tarde. Todos esos números son ilustrativos.

`uv run python examples/foundations.py` muestra ambas demos offline. El notebook añade una atención causal escalar ilustrativa, objetivos de entrenamiento desplazados y el contraste de precio en contexto. Ninguna celda entrena pesos.
