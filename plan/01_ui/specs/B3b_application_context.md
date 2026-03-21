# Spec: Application Context (HITL B.5 — Context Gate)

> **Estado pipeline:** NO IMPLEMENTADO ⚠️ — nodos `build_application_context` y
> `review_application_context` definidos en `src/graph.py` pero sin lógica implementada.
> Este spec es especulativo — documenta el intent inferido y deja dudas explícitas para
> cuando se implemente.

---

## 1. Objetivo del Operador

Después de aprobar el match, el LLM construye un "application brief" — un texto narrativo
que sintetiza cómo el candidato encaja con el job posting. Este brief es el contexto que
alimenta los tres generadores de documentos (letter, CV, email).

El operador debe:
- Leer el brief narrativo generado
- Confirmar que el framing es correcto y no hay errores de interpretación
- Ajustar énfasis si el LLM malinterpretó la prioridad de algún requisito
- Aprobar o pedir regeneración antes de iniciar la costosa generación de documentos

Esta puerta existe para evitar desperdiciar tokens de generación si el contexto base está mal.

---

## 2. Contrato de Datos (API I/O)

> ⚠️ **DUDAS ABIERTAS — no existe endpoint real todavía**

**Lectura (propuesto):**
- `GET /api/v1/jobs/:source/:jobId/context` → `ApplicationContextPayload`
  ```ts
  {
    source: string,
    job_id: string,
    // opción A: brief narrativo plano
    narrative: string,
    // opción B: dict por req_id con framing por requerimiento
    framing: Record<string, { req_id: string, narrative: string, evidence_ids: string[] }>,
    metadata: {
      generated_at: string,
      model: string,
      round: number
    }
  }
  ```

**Escritura (propuesto):**
- `PUT /api/v1/jobs/:source/:jobId/editor/application_context/state`
  → guarda decisión (approve / regen + feedback)

**Dudas abiertas:**
- ¿Qué estructura exacta tiene `application_context`? ¿Narrativa plana o dict por req?
- ¿El endpoint se llama `context` o se integra como `view` dentro de job views?
- ¿Este nodo genera también `artifact_refs` (hashes) o es solo state?
- ¿Tiene rounds de regeneración como match (con `RoundManager`) o es más simple?

---

## 3. Composición de la UI y Layout

**Layout Base:** Panel de lectura central + sidebar de match reference + barra de decisión.

```
┌─ LeftNav ─┬──── Application Context (flex-1) ──────┬── Match Reference (w-72) ──┐
│           │ [PHASE: CONTEXT_GATE]                   │ [EVIDENCE_MAP]             │
│           │                                         │                            │
│           │ ┌─ NARRATIVE BRIEF ─────────────────┐  │ Req scores colapsados:     │
│           │ │ Para el puesto de Research         │  │                            │
│           │ │ Associate en TU Berlin...          │  │ [R001] Computer Vision ●●● │
│           │ │                                    │  │   → P_EXP_005, P_PUB_019  │
│           │ │ [texto editable en contexto]       │  │                            │
│           │ │                                    │  │ [R002] Python/ML ●●●○      │
│           │ └────────────────────────────────────┘  │   → P_SKL_001, P_SKL_003  │
│           │                                         │                            │
│           │ Si opción B (dict por req):             │ [R003] Teaching ●●○○       │
│           │ ┌─ PER-REQ FRAMING ──────────────────┐  │   → P_EXP_002             │
│           │ │ [R001] Computer Vision              │  │                            │
│           │ │   Framing: candidato tiene 3 años..│  │ Scores vienen de view1     │
│           │ │ [R002] Python/ML                   │  │ (reutiliza datos de match) │
│           │ │   Framing: experiencia directa...  │  │                            │
│           │ └────────────────────────────────────┘  │                            │
│           │                                         │ [REQUEST_REGEN]            │
│           │ Metadata: model · round_001 · timestamp │ [APPROVE_CONTEXT]          │
└───────────┴─────────────────────────────────────────┴────────────────────────────┘
```

**Componentes Core:**
- `<ContextBrief>` — panel de lectura del narrative. ¿Editable o read-only con inline suggestions?
- `<ReqFramingList>` — si el context es dict por req, lista colapsable por req_id
- `<MatchReferencePanel>` — muestra el resumen del match aprobado (scores + evidence_ids)
- `<ContextDecisionBar>` — sticky bottom: [REQUEST_REGEN] + [APPROVE_CONTEXT & PROCEED]
- `<RegenModal>` — misma pattern que otras vistas: textarea feedback + submit

**Componente a reutilizar:**
- `<EvidenceBank>` del sidebar — los evidence_ids referenciados pueden mostrarse al hover
- `<RegenModal>` — patrón idéntico a B2, B3, B4

---

## 4. Estilos y Unificación (Terran Command Theme)

**Paleta:**
- Fondo principal: `bg-[#0c0e10]`
- Panel narrative: `bg-surface-container border border-outline-variant/20`
- Header de fase: `text-primary font-headline uppercase tracking-widest text-xs`
- Framing per-req: `bg-surface-container-low border-l-2 border-primary/30 pl-3`

**Tipografía:**
- Narrative text: `font-body text-sm text-on-surface leading-relaxed`
- Req IDs: `font-mono text-[10px] text-primary/70`
- Framing labels: `font-headline uppercase text-[9px] tracking-widest text-on-surface/50`

**Interacciones:**
- `Ctrl+Enter` → aprueba contexto (APPROVE_CONTEXT)
- Hover sobre evidence_id → tooltip con preview del evidence
- Click en req_id en MatchReferencePanel → scroll al framing correspondiente (si es dict por req)

**Estado Vacío:**
- `CONTEXT_NOT_GENERATED — run pipeline to generate`

**Estado Error:**
- `MODEL_FAILURE` → banner rojo `GENERATION_FAILED`
- `INPUT_MISSING` → `match output required — approve match first`

---

## 5. Routing y Decisión

El operador tiene tres opciones (mismo patrón que todos los gates HITL):

| Acción | Estado | Siguiente nodo |
|--------|--------|----------------|
| APPROVE_CONTEXT | Escribe approved/state.json | `generate_motivation_letter` |
| REQUEST_REGEN | Escribe feedback, llama LLM | `build_application_context` |
| REJECT | Marca job como rejected | END |

La decisión debe enviarse al mismo `saveEditorState` endpoint (o un endpoint dedicado de context).

---

## Notas de Implementación

- Este view solo existe en el **DEFAULT pipeline** — en PREP_MATCH no hay puerta de contexto
- El view puede no tener un endpoint propio todavía — considerar reusar `getEditorState` con `nodeName="application_context"`
- Si `build_application_context` se elimina del pipeline final, este spec se descarta completo
- **Prioridad baja** — implementar después de que el nodo backend exista
- Reutiliza el pattern de `<RegenModal>` y la barra de decisión de B3 para consistencia

---

## Dudas Abiertas para el Backend

1. ¿El `application_context` es narrativa plana o estructura por req_id?
2. ¿Cuál es la diferencia real con pasar `matched_data` directo a `generate_documents`?
3. ¿Este nodo usa `RoundManager` (historial de rounds) o es simple override?
4. ¿La superficie de review (decision.md) tiene la misma estructura que `review_match`?
5. ¿Este nodo se mantiene en el pipeline final o se elimina por complejidad innecesaria?
