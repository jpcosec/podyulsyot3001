# Spec B3b — Application Context Gate (HITL B.5)

**Feature:** `src/features/job-pipeline/`
**Page:** `src/pages/job/ApplicationContext.tsx`
**Librerías:** `@tanstack/react-query` · `lucide-react`
**Fase:** 10 (**backend no implementado — spec especulativo**)

> **Estado:** Los nodos `build_application_context` y `review_application_context` están
> definidos en `src/graph.py` pero sin implementación. Este spec documenta el intent inferido
> y marca explícitamente las dudas abiertas. No implementar hasta que el backend exista.

---

## 1. Objetivo del Operador

Después de aprobar el match, el LLM construye un "application brief" — texto narrativo que
sintetiza cómo el candidato encaja con el job. Este brief alimenta los 3 generadores de
documentos (letter, CV, email). El operador:
- Lee el brief narrativo generado
- Confirma que el framing es correcto
- Ajusta énfasis si el LLM malinterpretó algún requisito
- Aprueba o pide regeneración antes de iniciar la costosa generación de documentos

---

## 2. Contrato de Datos (API I/O)

> **⚠️ DUDAS ABIERTAS — no existe endpoint real todavía**

**Lectura (propuesto):**
- `GET /api/v1/jobs/:source/:jobId/context` → `ApplicationContextPayload`
  ```ts
  {
    source, job_id,
    // Opción A: narrativa plana
    narrative: string,
    // Opción B: dict por req_id
    framing: Record<string, { req_id: string, narrative: string, evidence_ids: string[] }>,
    metadata: { generated_at: string, model: string, round: number }
  }
  ```

**Escritura (propuesto):**
- `PUT /api/v1/jobs/:source/:jobId/editor/application_context/state`

**Dudas abiertas:**
- ¿Narrativa plana o dict por req_id?
- ¿Tiene rounds de regeneración como match (RoundManager)?
- ¿El nodo se mantiene o se elimina del pipeline final?

---

## 3. Composición de la UI y Layout

**Layout:** Panel central + match reference sidebar (w-72).

```
┌──── Application Context (flex-1) ──────┬── Match Reference (w-72) ──┐
│ [PHASE: CONTEXT_GATE]                  │ [EVIDENCE_MAP]             │
│                                        │                            │
│ ┌─ NARRATIVE BRIEF ─────────────────┐  │ Scores del match:          │
│ │ Para el puesto de Research        │  │ [R001] CV ●●●              │
│ │ Associate en TU Berlin...         │  │ [R002] Python ●●●○         │
│ │ [texto editable en contexto]      │  │ [R003] Teaching ●●○○       │
│ └───────────────────────────────────┘  │                            │
│                                        │ (reutiliza datos de view1) │
│ Metadata: model · round · timestamp    │                            │
│                                        │ [REQUEST_REGEN]            │
│                                        │ [APPROVE_CONTEXT]          │
└────────────────────────────────────────┴────────────────────────────┘
```

**Componentes Core:**
- `<ContextBrief>` — panel de lectura del narrative
- `<MatchReferencePanel>` — resumen del match aprobado con scores
- `<ContextDecisionBar>` — REQUEST_REGEN + APPROVE_CONTEXT
- `<RegenModal>` — mismo patrón que B2/B3/B4

---

## 4. Estilos (Terran Command)

Hereda estilos de B2/B3. Sin cambios estructurales de paleta.

---

## 5. Archivos a crear (cuando el backend exista)

```
src/features/job-pipeline/
  api/
    useApplicationContext.ts      useQuery(['context', source, jobId])
    useContextDecision.ts         useMutation
  components/
    ContextBrief.tsx              panel narrative
    MatchReferencePanel.tsx       scores del match
    ContextDecisionBar.tsx        botones de decisión
src/pages/job/
  ApplicationContext.tsx          TONTO: useParams + hooks + render
```

---

## 6. Definition of Done

```
[ ] (BLOQUEADO — requiere backend implementado)
[ ] ApplicationContext renderiza narrative del mock sin errores
[ ] MatchReferencePanel muestra scores del match aprobado
[ ] APPROVE_CONTEXT navega a /motivation_letter (DEFAULT) o /sculpt (PREP_MATCH)
[ ] REQUEST_REGEN abre RegenModal con feedback textarea
[ ] Sin datos hardcodeados — todo dato proviene del mock/API, nunca de literales en el componente
```

---

## 7. E2E (TestSprite)

> **Bloqueado hasta que el backend esté implementado.**

**URL:** `/jobs/tu_berlin/201397/context` (ruta pendiente de definir)

1. Verificar que `<ContextBrief>` muestra el narrative del mock
2. Verificar que `<MatchReferencePanel>` muestra scores de los reqs
3. Click APPROVE_CONTEXT → verificar navegación al siguiente gate
