"""Judge demo with the session model. Uses the API."""

import json

from carrito.judge import judge_demo

print(json.dumps(judge_demo("live"), ensure_ascii=False, indent=2))
