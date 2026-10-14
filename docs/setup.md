# Setup · Carrito

## 1. Instalar (una vez, antes de la primera sesión)

Necesitas Python 3.13, Git y [uv](https://docs.astral.sh/uv/getting-started/installation/). Los comandos funcionan en macOS, Linux y PowerShell.

```bash
git clone https://github.com/idiaz01/carrito-workshop.git
cd carrito-workshop
uv sync --locked --extra langchain
```

`uv` instala la versión de Python de `.python-version` y las dependencias de `uv.lock`. Este paso necesita red.

Si el kernel de `.venv` no aparece en Jupyter, regístralo:

```bash
uv run python -m ipykernel install --user --name carrito --display-name "Carrito · Python 3.13"
```

## 2. Clave de la sesión (al inicio de cada sesión)

Cada sesión usa una clave de API nueva. La clave de la sesión anterior ya no funciona.

1. La primera vez, copia `.env.example` como `.env`. No subas `.env` a Git.
2. El docente comparte la clave en el canal del curso. Pégala en `OPENAI_API_KEY`.
3. No cambies `OPENAI_MODEL`. Todos usamos el mismo modelo.
4. Ejecuta `uv run carrito doctor`. Debe mostrar `"api": "OK"` y el modelo.

```text
OPENAI_API_KEY=<clave de hoy>
OPENAI_MODEL=gpt-6-luna
```

No pegues la clave en un notebook. No la compartas fuera del curso. La clave caduca al final de la sesión.

## 3. Abrir el notebook

```bash
uv run jupyter lab
```

Abre `sessions/<sesión>/starter.ipynb` y selecciona el kernel de `.venv`.
La primera celda de código hace una llamada corta a la API. Si muestra `'api': 'OK'`, la clave funciona.

Los notebooks leen `.env` en cada llamada. Si cambias la clave, repite la celda. No necesitas reiniciar el kernel.

## Si algo falla

| Mensaje | Qué hacer |
|---|---|
| `Falta OPENAI_API_KEY en .env` | Pega la clave de hoy en `.env` y repite la celda |
| `La clave no es válida o ya caducó` | Usa la clave de hoy, no la de otra sesión |
| `El modelo de OPENAI_MODEL no existe` | Copia la línea `OPENAI_MODEL` de `.env.example` |
| `Límite de uso alcanzado` | Espera un minuto y repite. Si sigue, avisa al docente |
| `No hay conexión con la API` | Revisa la red y repite |
| `ModuleNotFoundError: carrito` | Ejecuta `uv sync --locked --extra langchain` desde la raíz y elige el kernel de `.venv` |
| `Falta LangChain` (S3) | Ejecuta `uv sync --locked --extra langchain` |
| Estado inesperado en el notebook | Reinicia el kernel y ejecuta desde el principio |

Un error de la API no indica un error en tu código. Lee el mensaje y aplica la acción de la tabla.

## Comandos útiles

```bash
uv run carrito doctor        # comprueba datos, clave y modelo
uv run carrito demo          # una pregunta al agente
uv run carrito chat          # conversación con el agente; /confirm confirma, /quit sale
uv run carrito agente --debug   # S2: tu agente (mi_agente/) y lo que ve el modelo
uv run carrito casos         # S2: marcador de casos de tu agente
uv run carrito mcp-smoke     # catálogo mediante un servidor MCP local
uv run carrito skill-demo    # activación de la Skill de devoluciones
uv run carrito judge-demo    # juez LLM frente a etiquetas humanas
```

En `chat`, solo `/confirm` confirma una devolución. Escribir «sí» no da permisos al modelo.
Las trazas se guardan en `runtime/`.
