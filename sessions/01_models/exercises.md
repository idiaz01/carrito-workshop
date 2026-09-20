# 1 · Fundamentos de LLMs: de tokens a una primera aplicación

Prerrequisitos: Python y fundamentos de ML.

Explora tokens, representación, generación y contexto. Después completa `build_messages`, cambia un precio y comprueba qué ocurre cuando falta un atributo. Al terminar podrás explicar qué calcula un LLM, qué cambia durante el entrenamiento y qué aporta la aplicación que lo utiliza.

## Qué vamos a observar
¿Cómo puede un sistema producir una frase nueva sin tener esa frase guardada como respuesta?
Conserva esta pregunta. Hoy observaremos representación, predicción, generación y contexto;
construiremos una llamada pequeña solo cuando esos conceptos tengan sentido.
La celda de entorno está suministrada: no necesitas crear una base de datos ni instalar un modelo.

## Una historia de representaciones y objetivos
Un modelo de lenguaje asigna probabilidades a continuaciones. Los modelos de conteo
estiman frecuencias de secuencias cortas; las redes neuronales aprenden representaciones
y relaciones; el Transformer permite combinar posiciones mediante atención.
Escalar datos y entrenamiento mejora capacidades, y la adaptación a instrucciones cambia
cómo se usa esa capacidad. Un chat añade roles e historial a un modelo: la interfaz no es el modelo.

**Pregunta:** ¿memorizar una frase, aprender una regularidad y consultar un dato actual
son la misma operación? Mantén separadas capacidad aprendida, evidencia del contexto y acceso a tools.

## Demo 1: un token no es necesariamente una palabra
Estos IDs y fragmentos se midieron con **tiktoken / cl100k_base** y están guardados en
`data/foundations/tokenization.json`. No son una separación inventada a mano ni una llamada
a un modelo. El tokenizer del `OPENAI_MODEL` elegido puede ser distinto.
Los IDs son índices de vocabulario; no expresan significado ni cercanía semántica.
Predice cuántos tokens habrá antes de ejecutar. Compara palabra, espacio, cifra y puntuación.

## Demo 2: distribución del siguiente token, condicionada al prefijo
La expresión `P(siguiente token | tokens anteriores)` devuelve una distribución sobre un vocabulario.
**Toy de ocho palabras:** las puntuaciones de abajo están escritas a mano; no son probabilidades
medidas de un LLM ni un Transformer entrenado. El vocabulario del toy usa palabras enteras para
poder leer los números. Es distinto del tokenizer real de la demo anterior.

El prefijo cambia la distribución aunque la tabla del toy permanezca fija.
Predice qué gana después de «El pedido llega» y después de «El pedido sale».

## Transformer: de IDs a representaciones que usan contexto
Recorrido conceptual: IDs → embeddings y posición → bloques de atención causal y MLP
(con conexiones residuales y normalización) → logits sobre el vocabulario → siguiente token.
El embedding es un vector aprendido; un ID por sí solo no es ese vector.

**Miniatura de una sola cabeza:** fijamos tres puntuaciones de atención y tres valores escalares.
La fila `i` solo puede mezclar posiciones `0..i`; las posteriores quedan en cero por la máscara causal.
No implementamos Q/K/V aprendidos, proyecciones, múltiples cabezas ni bloques completos.
Una matriz de atención no es una prueba de verdad ni una explicación completa del modelo.

## Qué se aprende y qué permanece fijo al preguntar
En pretraining, el propio texto aporta objetivos del siguiente token: es aprendizaje autosupervisado.
La pérdida compara probabilidades con el token objetivo; el optimizador actualiza parámetros.
La adaptación a instrucciones y preferencias usa objetivos/datos adicionales para cambiar comportamiento.
Ninguna de estas operaciones equivale a pegar un catálogo en el prompt.

En inferencia ordinaria, los parámetros permanecen fijos y cambian entradas, activaciones y salida.
La ventana de contexto tiene un límite; recibir información en ella no demuestra que se haya guardado
en los pesos ni garantiza recordarla en otra conversación. Observa el desplazamiento input/target:

## Inferencia y decoding: temperatura sobre logits fijos
`p_i = exp(z_i / T) / sum(exp(z_j / T))`, con `T > 0`.
Comparamos **los mismos logits ilustrativos** `[2, 1, 0]` con tres temperaturas,
normalizados solo entre los tres candidatos «mañana», «hoy», «tarde». Es un vocabulario
reducido para ver las cuentas; no predice la fecha de entrega de ningún pedido.
Menor T concentra masa; mayor T la reparte. El orden de los logits no cambia.
Greedy elige el máximo; sampling extrae según la distribución. Nuestro cálculo no muestrea.
No uses temperatura como «control de alucinación»: una distribución muy concentrada también
puede favorecer una continuación falsa. No todos los modelos/API exponen este parámetro.

## Contexto contrafactual: el mismo modelo, otro dato disponible
Las cinco fichas anteriores son evidencia, no conocimientos guardados en los pesos.
Cambiamos solo P001 de 69,90 a 89,90 €, manteniendo pregunta e instrucción.
Con presupuesto de 80 €, la respuesta sustentada debería cambiar.
Las respuestas offline de esta demo están **escritas de antemano**: muestran la comparación
esperada, no prueban que un modelo siga la evidencia. En live se conservan modelo/configuración
y se observan las salidas reales; este código nunca entrena.

En la función anterior localiza `model`, `input`, `max_output_tokens` y `store=False`.
En la respuesta distingue `output_text`, los items `output`, `status` y `usage`.
`usage=None` en nuestras fixtures significa «no medido», nunca cero tokens de un modelo real.
Si una llamada real falla por red, cuota o acceso, el error no demuestra incapacidad lingüística.
Una respuesta incompleta o un rechazo tampoco debe presentarse como éxito.

## Capacidades, límites y entrada multimodal
Generar, resumir y extraer patrones no garantiza disponer de hechos actuales, respetar un límite
o reconocer información ausente. En las fichas abreviadas no figura resistencia al agua ni conectividad.
La imagen amplía el tipo de entrada; no convierte una ilustración en prueba de stock o garantía.
Mira la tarjeta antes de ejecutar la demo preparada: ¿qué puede observarse y qué habría que consultar?

## Modelo, aplicación, workflow y agente
- **Modelo:** transforma un contexto en probabilidades y contenido generado.
- **Aplicación:** añade interfaz, instrucciones, datos, validaciones y presentación.
- **Workflow:** el software fija una secuencia; por ejemplo, leer datos → llamar → comprobar.
- **Agente:** el modelo puede elegir el siguiente paso mediante tools, dentro de límites del host.

Nuestro primer lab es una aplicación con una llamada. No permite que el modelo consulte SQLite,
elija tools ni escriba devoluciones. En S3–S4 veremos qué componentes adicionales hacen falta.
Predice quién debe comprobar un precio: ¿basta una instrucción al modelo o necesitamos evidencia y checks?

## Primera aplicación: una función y dos contrastes

1. Completa `build_messages` con dos roles, las cinco fichas y una regla ante datos ausentes.
2. Ejecuta el caso base y explica qué puede afirmarse sobre P001.
3. Cambia solo su precio en una copia del contexto y compara contra el presupuesto de 80 €.
4. Pregunta por resistencia al agua y anota qué información falta.

Los contrastes y la llamada están suministrados. Pista: usa `json.dumps(products, ensure_ascii=False)` en el mensaje de usuario. El notebook puede ejecutarse sin completar la función: los checks quedan PENDIENTE.

## Primera evaluación: cinco casos

Registra lo observado en cada caso. Sin API, etiqueta el análisis como fixture y distingue salida preparada, expectativa y explicación.

| Caso | Qué comprobar |
|---|---|
| ¿P001 cabe en 80 €? Contexto A | Precio de 69,90 € sustentado |
| Misma pregunta, contexto B | Precio de 89,90 €: cambia la conclusión |
| ¿P001 es resistente al agua? | El atributo no existe en las fichas |
| ¿Qué compro? | Faltan preferencias |
| Monitor por 20 € | No inventar producto ni descuento |

**Aceptación técnica:** pasan los tres checks de `build_messages`. **Aceptación conceptual:**
explicas token frente a palabra, generación paso a paso, parámetros frente a contexto y por qué
cambiar T no demuestra corrección. Entregas los tres contrastes del lab y las cinco notas de cierre
sobre los cinco casos, con el fallo de atributo inventado identificado.
Los checks no sustituyen esa explicación ni miden la calidad de un LLM real.

**Checkpoint siguiente:** S2 trae su catálogo y mensajes preparados; no depende de completar S1.
Fuentes: [tiktoken oficial](https://github.com/openai/tiktoken) y
[generación de texto en la API](https://developers.openai.com/api/docs/guides/text).
Las cifras del toy y de atención son ilustrativas; los IDs del tokenizer son mediciones guardadas.

## Comprobación final

Reinicia el kernel y ejecuta todo. Revisa cada mensaje PENDIENTE sin alterar los checks para que pasen. Anota qué comportamiento has comprobado y qué afirmaciones requieren revisión humana.
