# Setup · Carrito

## Un entorno preparado antes de clase

Python 3.13 y [uv](https://docs.astral.sh/uv/getting-started/installation/). Clona [el repositorio del curso](https://github.com/idiaz01/carrito-workshop) y entra en su carpeta. En macOS/Linux y PowerShell funcionan los siguientes comandos:

```bash
git clone https://github.com/idiaz01/carrito-workshop.git
cd carrito-workshop
uv sync --locked
uv run carrito doctor
uv run carrito demo --mode fixture
uv run jupyter lab
```

`uv` usa la versión de `.python-version` y las dependencias de `uv.lock`. El primer `sync` necesita red. El modo fixture posterior funciona sin clave ni una base de datos externa. En Jupyter, selecciona el kernel del entorno del proyecto; el diagnóstico al principio del notebook muestra el intérprete y los imports.

Si no aparece el kernel:

```bash
uv run python -m ipykernel install --user --name carrito --display-name "Carrito · Python 3.13"
```

Abre `sessions/01_models/starter.ipynb`. Cada sesión incluye un checkpoint inicial funcional. Completa los ejercicios y documenta tus resultados.

## Llamadas reales

Copia `.env.example` a `.env` con tu editor, sin sobrescribir una configuración existente. Introduce `OPENAI_API_KEY` y un `OPENAI_MODEL` disponible en tu cuenta. El modelo debe admitir las capacidades usadas en el ejercicio: Responses, tools o structured outputs, según corresponda. El identificador es configurable; comprueba acceso y coste con el proveedor antes de clase.

Antes de ejecutar una comparación live, comprueba acceso al modelo, usage y latencia con una llamada corta. Las credenciales no se pegan en notebooks ni se guardan en Git. Los notebooks mantienen `RUN_LIVE = False` hasta que se activa el modo real conscientemente. Tener una clave no activa por sí solo llamadas de pago en los tests o checks offline.

```bash
uv run carrito demo --mode live
```

El modo `fixture` es una secuencia preparada con formato similar a la API. No es un modelo local ni una predicción del comportamiento del modelo elegido. Si falla la API, se continúa con las fixtures y se registra esa limitación.

## Conversación interactiva

```bash
uv run carrito chat --mode fixture
# Con API configurada:
uv run carrito chat --mode live
```

El modo fixture usa escenarios preparados, no interpreta lenguaje libre como un LLM. En modo live la conversación conserva el historial. El comando `/confirm` del host confirma el pedido y motivo mostrados; escribir «sí» en un prompt no concede por sí solo permisos al modelo. `/quit` termina la sesión. Las trazas locales permiten revisar qué ocurrió.

## S3: comparación opcional con LangChain

Instala este extra antes de clase si vas a seguir la demo:

```bash
uv sync --locked --extra langchain
uv run --extra langchain python examples/langchain_comparison.py --mode fixture
```

El comando muestra la recuperación local, una tool real de catálogo y mensajes LangChain con respuestas del modelo preescritas. No requiere cuenta de LangSmith. `--mode live` usa la misma clave y modelo de `.env`, y consume API. Los notebooks funcionan también sin este extra; la comparación con LangChain es opcional. Mantén `--extra langchain` en los comandos `uv run` de esta demo para conservar el entorno opcional.

Consulta la [tabla API nativa / LangChain](../examples/langchain-comparison.md). Las versiones están bloqueadas y la integración tiene sus propias pruebas offline.

## MCP en S3 y Skills en S5: demos suministradas

```bash
uv run carrito mcp-smoke
uv run carrito skill-demo
```

MCP usa un proceso local por stdio. No exige Docker, un despliegue remoto ni OAuth. La Skill es un procedimiento de ejemplo con carga explícita; no concede permisos ni reemplaza la confirmación del host.

## Si algo falla

| Síntoma | Qué comprobar |
|---|---|
| `ModuleNotFoundError: carrito` | Ejecutar `uv sync --locked` desde la raíz y elegir el kernel correcto |
| Falta `OPENAI_MODEL` | Configurar `.env` o continuar con fixture |
| API rechaza acceso o modelo | Verificar cuenta, modelo y clave; no cambiar código de negocio |
| Se agotó cuota / no hay red | Trabajar con fixture y etiquetar el informe |
| Estado inesperado | Reiniciar el store del notebook; los casos independientes usan stores nuevos |
| Una sesión anterior está incompleta | Abrir el starter de la sesión actual; no requiere sus artefactos |

Las confirmaciones pendientes son de la sesión en memoria. No se promete reanudar una aprobación tras reiniciar un proceso. Una SQLite con archivo conserva solicitudes registradas; una base `:memory:` desaparece al cerrar.

## Verificación del entorno

```bash
uv run ruff check .
uv run pytest -q
uv run carrito eval --split dev --mode fixture
uv run python scripts/check_notebooks.py
uv run python scripts/check_student_repo.py
```


## Experimentos compartidos de S2–S5

```bash
uv run python examples/learning_labs.py --output runtime/learning-evidence.json
```

Ejecuta contexto, retrieval y comparación del contrato del agente. No requiere API. [Guía de los labs](../examples/learning-labs.md). En S5 `RUN_LIVE=True` permite comparar el contrato con decisiones reales del modelo y usar el judge real: puede generar varias llamadas de pago. Los resultados no se garantizan iguales a los fixtures y deben diagnosticarse.
