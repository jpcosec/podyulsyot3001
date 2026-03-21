# Spec B4b — Default Document Gates (HITL C.1 / C.2 / C.3)

**Feature:** `src/features/job-pipeline/`
**Page:** `src/pages/job/GenerateDocuments.tsx` (reutiliza el mismo componente que B4)
**Librerías:** `react-resizable-panels` · `@uiw/react-codemirror` · `@tanstack/react-query` · `lucide-react`
**Fase:** 8 (**backend no implementado — spec especulativo**)

> **Estado:** Los nodos `generate_motivation_letter`, `review_motivation_letter`, `tailor_cv`,
> `review_cv`, `draft_email`, `review_email` están definidos en `src/graph.py` pero sin
> implementación. Este spec documenta el intent inferido. No implementar hasta que el backend exista.

> **Relación con B4:** B4 describe la vista de PREP_MATCH (3 tabs simultáneos). Este spec
> describe cómo el DEFAULT pipeline usa la **misma página** `GenerateDocuments.tsx` con un
> solo tab activo a la vez — los demás en estado `pending` o `approved`.

---

## 1. Objetivo del Operador

Hay tres gates HITL consecutivos en el DEFAULT pipeline:

- **Gate C.1** (LETTER_GATE): Revisar y aprobar la motivation letter generada
- **Gate C.2** (CV_GATE): Revisar y aprobar el CV adaptado
- **Gate C.3** (EMAIL_GATE): Revisar y aprobar el email de aplicación (último gate antes de render)

En cada gate el operador edita el documento activo, puede pedir regeneración con feedback, y
aprueba para avanzar al siguiente gate. Los tabs de los otros documentos son visibles pero
están bloqueados (`pending`) o ya resueltos (`approved ✓`).

---

## 2. Contrato de Datos (API I/O)

> **⚠️ DUDAS ABIERTAS — no existe endpoint real todavía**

**Lectura (propuesto):**
- `GET /api/v1/jobs/:source/:jobId/documents/motivation_letter` → `{ content: string }`
- `GET /api/v1/jobs/:source/:jobId/documents/cv` → `{ content: string }`
- `GET /api/v1/jobs/:source/:jobId/documents/application_email` → `{ content: string }`
- Reutiliza `GET /api/v1/jobs/:source/:jobId/view3` si devuelve los 3 docs individuales

**Escritura (propuesto):**
- `PUT /api/v1/jobs/:source/:jobId/editor/review_motivation_letter/state`
- `PUT /api/v1/jobs/:source/:jobId/editor/review_cv/state`
- `PUT /api/v1/jobs/:source/:jobId/editor/review_email/state`
- Payload: `{ decision: "approve" | "request_regeneration" | "reject", feedback?: string }`

**Dudas abiertas:**
- ¿`generate_motivation_letter` produce texto completo o deltas sobre un template base?
- ¿`tailor_cv` genera CV completo en markdown o solo `cv_injections` para merge con base CV?
- ¿El email tiene subject + body separados o un solo campo texto?

---

## 3. Composición de la UI y Layout

La UI es idéntica a B4. Solo cambia el estado de cada tab según el gate activo.

### Gate C.1 — Motivation Letter

```
┌─ [COVER_LETTER*] [CV — pending] [EMAIL — pending] ─┬── Context (w-72) ──┐
│────────────────────────────────────────────────────  │                    │
│                                                       │ PHASE: LETTER_GATE │
│  CodeMirror — motivation_letter content (editable)   │                    │
│                                                       │ Evidence usada:    │
│                                                       │ [P_EXP_005] ...    │
│                                                       │                    │
│                                                       │ [REQUEST_REGEN]    │
│                                                       │ [APPROVE_LETTER]   │
└───────────────────────────────────────────────────────┴────────────────────┘
```

### Gate C.2 — Tailored CV

```
┌─ [✓ COVER_LETTER] [CV*] [EMAIL — pending] ─┬── Context (w-72) ──┐
│────────────────────────────────────────────  │                    │
│                                              │ PHASE: CV_GATE     │
│  CodeMirror — tailored CV (editable)         │                    │
│  [Education / Experience / Skills]           │ [REQUEST_REGEN]    │
│                                              │ [APPROVE_CV]       │
└──────────────────────────────────────────────┴────────────────────┘
```

### Gate C.3 — Application Email

```
┌─ [✓ COVER_LETTER] [✓ CV] [EMAIL*] ─┬── Context (w-72) ──┐
│────────────────────────────────────  │                    │
│  To: [contact.email]                 │ PHASE: EMAIL_GATE  │
│  Subject: [generated subject]        │                    │
│  ─────────────────────────           │ Contacto detectado │
│  [email body — 2-3 líneas]           │  Dr. Müller        │
│                                      │  hr@tu-berlin.de   │
│                                      │ [REQUEST_REGEN]    │
│                                      │ [APPROVE — RENDER] │
└──────────────────────────────────────┴────────────────────┘
```

**Tab states por gate:**

| Tab | C.1 (Letter) | C.2 (CV) | C.3 (Email) |
|-----|-------------|----------|-------------|
| COVER_LETTER | activo `*` | `✓ approved` | `✓ approved` |
| CV | `pending 🔒` | activo `*` | `✓ approved` |
| EMAIL | `pending 🔒` | `pending 🔒` | activo `*` |

**Componentes Core (todos reutilizados de B4):**
- `<DocumentTabs>` — mismo componente, prop `activeDoc` + `approvedDocs` + `lockedDocs`
- `<DocumentEditor>` — CodeMirror markdown (letter/CV) o textarea compacta (email)
- `<ContextPanel>` — mismo, con `PHASE: LETTER_GATE | CV_GATE | EMAIL_GATE`
- `<DocApproveBar>` — mismo, botón cambia de label según gate
- `<RegenModal>` — mismo patrón

---

## 4. Estilos (Terran Command)

Hereda todos los estilos de B4. Adiciones:

- `pending` tabs: `opacity-40 cursor-not-allowed` + tooltip `"complete previous gate first"`
- `approved` tabs: `border-b-2 border-primary text-primary` + `✓` prefix
- CTA final (approve email C.3): `bg-primary text-[#0c0e10] font-bold tactical-glow` — más prominente que los anteriores gates

---

## 5. Archivos a crear (cuando el backend exista)

```
src/features/job-pipeline/
  api/
    useDocumentGate.ts            useQuery(['document-gate', source, jobId, docKey])
    useGateDecision.ts            useMutation para approve/regen por gate
  (reutiliza DocumentTabs, DocumentEditor, ContextPanel, DocApproveBar, RegenModal de B4)
src/pages/job/
  GenerateDocuments.tsx           YA EXISTE en B4 — añadir prop mode="default_gate"
                                  + activeDoc: "motivation_letter" | "cv" | "email"
                                  + approvedDocs: string[]
```

> **Nota:** No se necesitan páginas separadas para C.1/C.2/C.3. La misma
> `GenerateDocuments.tsx` recibe la ruta actual del pipeline (desde `JobTimeline`) y
> determina qué tab activar y cuáles están locked/approved.

---

## 6. Definition of Done

```
[ ] (BLOQUEADO — requiere backend implementado)
[ ] GenerateDocuments renderiza con tab COVER_LETTER activo en Gate C.1
[ ] Tab CV y EMAIL aparecen como "pending" con opacity-40 y cursor-not-allowed
[ ] Tooltip en tab pending muestra "complete previous gate first"
[ ] APPROVE_LETTER navega al Gate C.2 (tab CV activo, COVER_LETTER con ✓)
[ ] Gate C.3: CTA "APPROVE — RENDER" tiene estilo bg-primary más prominente
[ ] REQUEST_REGEN abre RegenModal con textarea de feedback
[ ] Sin datos hardcodeados — todo dato proviene del mock/API, nunca de literales en el componente
```

---

## 7. E2E (TestSprite)

> **Bloqueado hasta que el backend esté implementado.**

**URL:** `/jobs/tu_berlin/999001/motivation_letter` (ruta pendiente de definir por gate)

1. Verificar que `<DocumentTabs>` muestra COVER_LETTER activo, CV y EMAIL como pending
2. Verificar que click en tab pending no cambia el documento activo
3. Verificar que tooltip en tab pending es visible al hover
4. Click en APPROVE_LETTER → verificar navegación al Gate C.2 con tab CV activo
5. En Gate C.3: verificar que el CTA tiene clase `bg-primary` y es visualmente más prominente
