"""For a charged live run, use carrito judge-demo --mode live explicitly."""

import json

from carrito.judge import judge_demo

print(json.dumps(judge_demo(), ensure_ascii=False, indent=2))
