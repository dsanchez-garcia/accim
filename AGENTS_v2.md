# AGENTS.md (v2)

Este documento define cómo diseñar, implementar y operar agentes para la librería **accim**.

> Alcance: estas pautas están orientadas a mantener consistencia, trazabilidad y calidad en agentes basados en LLM.

## 1. Objetivo

Los agentes de `accim` deben:

- Resolver tareas de forma fiable y repetible.
- Minimizar alucinaciones mediante validación y uso controlado de herramientas.
- Exponer salidas estructuradas y auditables.
- Ser fáciles de mantener (prompts versionados, contratos claros, pruebas).

## 2. Principios de diseño

1. **Instrucciones claras y acotadas**
   - Define rol, alcance, entradas, salidas y límites.
2. **Herramientas con contratos estrictos**
   - Cada tool debe tener esquema de entrada/salida validable.
3. **Separación entre razonamiento y salida**
   - La salida pública debe ser limpia, estructurada y sin trazas internas.
4. **Idempotencia cuando sea posible**
   - Mismas entradas → mismo comportamiento esperado (dentro de la variabilidad del modelo).
5. **Observabilidad**
   - Logging de prompts, llamadas a herramientas, errores y métricas.
6. **Seguridad por defecto**
   - No exponer secretos, aplicar mínimo privilegio y sanitizar entradas.

## 3. Tipos de agentes recomendados

- **Router/Dispatcher**
  - Clasifica intención y deriva a un agente especializado.
- **Task Agent**
  - Ejecuta tareas concretas (p. ej., extracción, resumen, generación guiada).
- **Reviewer/Critic**
  - Verifica calidad, consistencia y cumplimiento de políticas.
- **Tool-using Agent**
  - Orquesta llamadas a APIs, DBs o servicios internos.

## 4. Contrato mínimo de un agente

Cada agente debería definir explícitamente:

- `name`: identificador único.
- `purpose`: objetivo funcional.
- `inputs`: esquema de entrada (tipos, obligatorios, validaciones).
- `outputs`: esquema de salida (JSON recomendado si aplica).
- `tools`: herramientas permitidas y condiciones de uso.
- `constraints`: límites (dominio, tono, seguridad, compliance).
- `failure_mode`: comportamiento en error o falta de contexto.

## 5. Plantilla de prompt del sistema

Usa una plantilla consistente (ajústala a tu caso):

```text
Eres el agente <name> de accim.
Objetivo: <purpose>.
Debes cumplir:
- Entradas válidas: <inputs>
- Salida esperada: <outputs>
- Herramientas permitidas: <tools>
- Restricciones: <constraints>
Si falta información crítica, solicita aclaración de forma breve.
Si no puedes completar la tarea con seguridad, responde con <failure_mode>.
```

## 6. Uso de herramientas (Tooling)

Buenas prácticas:

- Define **allowlist** de herramientas por agente.
- Valida parámetros antes de invocar herramientas.
- Maneja reintentos con backoff en errores transitorios.
- Limita número de llamadas por solicitud (coste y latencia).
- Registra latencia, éxito/fallo y payloads redaccionados.

## 7. Gestión de contexto

- Prioriza contexto relevante y reciente.
- Aplica truncado inteligente (no recortar instrucciones críticas).
- Añade citas/referencias cuando la respuesta dependa de fuentes.
- Distingue datos de usuario, sistema y herramientas.

## 8. Evaluación y calidad

Define una batería mínima:

- **Unit tests de prompt**: casos felices + casos borde.
- **Evaluación offline**: exactitud, cobertura, formato, groundedness.
- **Regression suite**: evitar degradaciones en cambios de prompt/modelo.
- **Human review** para tareas de alto riesgo.

Métricas sugeridas:

- Tasa de éxito por tarea.
- Tasa de error de herramientas.
- Latencia p50/p95.
- Coste por solicitud.
- Tasa de respuestas no accionables.

## 9. Seguridad y cumplimiento

- Nunca incluir secretos en prompts o logs.
- Enmascarar PII en telemetría.
- Añadir filtros para prompt injection y data exfiltration.
- Restringir herramientas sensibles por rol/entorno.
- Mantener auditoría de cambios de prompts y políticas.

## 10. Versionado y cambios

- Versiona prompts (`agent_name@vMAJOR.MINOR`).
- Usa changelog por agente.
- Cambios breaking → incrementar MAJOR.
- Ejecuta regression suite antes de desplegar.

## 11. Estructura de archivos recomendada

```text
agents/
  router/
    system_prompt.md
    schema.input.json
    schema.output.json
  task_<name>/
    system_prompt.md
    examples.md
    schema.input.json
    schema.output.json
  reviewer/
    system_prompt.md
    checklist.md

evals/
  datasets/
  regression/
  reports/
```

## 12. Checklist antes de producción

- [ ] Prompt con objetivo, límites y formato de salida claros.
- [ ] Esquemas de entrada/salida validados.
- [ ] Herramientas restringidas y testeadas.
- [ ] Manejo de errores y mensajes de fallback definidos.
- [ ] Métricas y logs activos.
- [ ] Regression suite en verde.
- [ ] Revisión de seguridad/compliance completada.

## 13. Ejemplo de salida estructurada

```json
{
  "status": "ok",
  "result": {
    "summary": "...",
    "actions": ["..."],
    "risks": ["..."]
  },
  "confidence": 0.86,
  "sources": ["tool:x", "doc:y"]
}
```

---

Si este documento se usa como estándar interno de `accim`, se recomienda revisarlo trimestralmente y actualizarlo cuando cambien modelos, herramientas o requisitos de seguridad.
