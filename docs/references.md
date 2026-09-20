# Documentación y lecturas


| Tema | Fuente primaria | Aplicación |
|---|---|---|
| Native API | [OpenAI Responses](https://platform.openai.com/docs/api-reference/responses) | Sesión 1, llamada visible |
| Structured outputs | [OpenAI guía](https://platform.openai.com/docs/guides/structured-outputs) | Sesión 2, schema y límites |
| Tools | [Function calling](https://platform.openai.com/docs/guides/function-calling) | Sesión 3, ejecución en el host |
| Context | [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Selección y compaction |
| Agent patterns | [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Workflow frente a loop |
| Evals | [Anthropic evals for agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | Trayectorias y resultados |
| RAG | [Contextual retrieval](https://www.anthropic.com/engineering/contextual-retrieval) | Demo, no infraestructura obligatoria |
| Graph | [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) | Ampliación tras S4 |
| Interrupts | [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) | Lectura adicional sobre persistencia y efectos |
| MCP | [Specification](https://modelcontextprotocol.io/specification) · [Python SDK v2](https://py.sdk.modelcontextprotocol.io/v2/) | Implementación de server/client en S3 |
| Gemini | [Gemini API docs](https://ai.google.dev/gemini-api/docs) | Comparación de proveedores |
| Retrieval stack | [LlamaIndex docs](https://developers.llamaindex.ai/python/framework/) | Lectura adicional |
| Local/open weights | [Hugging Face Transformers](https://huggingface.co/docs/transformers/index) | Trade-offs de despliegue |
| A2A | [A2A protocol](https://a2a-protocol.org/latest/) | Reconocer finalidad, no implementar |
| Test framework | [pytest](https://docs.pytest.org/) | Checks deterministas |
| Dependency management | [uv](https://docs.astral.sh/uv/) | Entorno reproducible |


| Tema añadido | Fuente primaria | Aplicación |
|---|---|---|
| Skills | [Agent Skills specification](https://agentskills.io/specification) | Demo de metadata y carga de una Skill en S5 |
| Harness | [Effective harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Límites, estado y ejecución en S4 |

## Fundamentos: historia y mecanismos de S1

Estas lecturas respaldan las explicaciones de la sesión; no son preparación obligatoria para el alumnado.

- [Bengio et al., 2003 — A Neural Probabilistic Language Model](https://www.jmlr.org/papers/v3/bengio03a.html): representaciones aprendidas y generalización.
- [Sutskever et al., 2014 — Sequence to Sequence Learning](https://arxiv.org/abs/1409.3215): encoder y decoder para secuencias.
- [Vaswani et al., 2017 — Attention Is All You Need](https://arxiv.org/abs/1706.03762): Transformer, attention y máscara causal.
- [GPT, 2018](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf) y [BERT, 2018](https://arxiv.org/abs/1810.04805): objetivos de pretraining y familias de arquitectura.
- [Brown et al., 2020 — GPT-3](https://arxiv.org/abs/2005.14165): ejemplos en contexto sin actualizar pesos.
- [Ouyang et al., 2022 — InstructGPT](https://arxiv.org/abs/2203.02155): demostraciones, preferencias y seguimiento de instrucciones.
- [OpenAI tiktoken](https://github.com/openai/tiktoken): implementación del tokenizer usado en la fixture medida.
- [Hugging Face — Generation strategies](https://huggingface.co/docs/transformers/main/en/generation_strategies): greedy, sampling y parámetros de decoding.
- [OpenAI — Learning to reason](https://openai.com/index/learning-to-reason-with-llms/): cómputo de razonamiento y sus compromisos.
- [Yao et al. — ReAct, preprint 2022](https://arxiv.org/abs/2210.03629): alternar decisiones, acciones y observaciones.


## Contexto, integración y estado

- [Anthropic · Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): selección, mantenimiento y compresión del contexto. Se usa como criterio de ingeniería, no como garantía de que un prompt impida injection.
- [Liu et al. · Lost in the Middle](https://arxiv.org/abs/2307.03172): evidencia de sensibilidad a posición/contexto en condiciones experimentales concretas. No se enseña como ley universal de todos los modelos de 2026.
- [MCP · Architecture overview](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture): host/client/server y responsabilidades. S3 ejecuta stdio local; no afirma desplegar todas las capacidades del protocolo.
- [Agent Skills · Overview](https://agentskills.io/home): procedimientos empaquetados, metadata y progressive disclosure. S5 contrasta Skill con tool, prompt y host; el selector del taller es deliberadamente simple.
- [LangGraph · Persistence](https://docs.langchain.com/oss/python/langgraph/persistence): checkpoints y estado. Permite contrastar un runtime con persistencia de ejecución frente al helper del workshop que solo guarda preferencias.

Las fuentes anteriores se consultaron el 20 de septiembre de 2026. Los experimentos concretos del repositorio tienen su propia evidencia en [learning-evidence.json](../examples/traces/learning-evidence.json); no se atribuyen los resultados del taller a las fuentes externas.
