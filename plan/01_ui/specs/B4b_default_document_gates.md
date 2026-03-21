# Spec: Document Generation Gates — DEFAULT Pipeline (HITL C.1/C.2/C.3)

> **Estado pipeline:** NO IMPLEMENTADO ⚠️ — Los nodos `generate_motivation_letter`,
> `review_motivation_letter`, `tailor_cv`, `review_cv`, `draft_email`, `review_email`
> están definidos en `src/graph.py` pero sin implementación.
>
> **Relación con B4:** El spec B4 describe la vista unificada de PREP_MATCH (3 tabs en una sola
> view). Este spec describe cómo el DEFAULT pipeline los separa en 3 gates HITL independientes.
> La UI puede ser la **misma** — solo cambia cuántos tabs están activos a la vez y el routing.

---

## Contexto: PREP_MATCH vs DEFAULT

| Aspecto | PREP_MATCH | DEFAULT |
|---------|------------|---------|
| Nodos LLM | 1 (`generate_documents`) | 3 separados |
| Gates HITL | 1 (los 3 docs a la vez) | 3 consecutivos |
| View UI | B4 (3 tabs simultáneos) | B4b (un tab por gate, con otros en "pending") |
| Ventaja | Más rápido, menos latencia | Más control, regenera solo el doc que falló |
| Input del LLM | `matched_data` directamente | `application_context` (via B3b) |

La UI puede **reusar el mismo componente** `<DocumentEditor>` (ya spec'd en B4) — la diferencia
está en qué tabs están unlocked en cada gate y qué endpoint dispara el approve.

---

## Gate C.1 — Motivation Letter

### Nodos: `generate_motivation_letter` → `review_motivation_letter`

**Estado pipeline:** Planeado — sin implementar.

**Objetivo del operador:**
- Leer la cover letter generada por el LLM
- Editar libremente el texto (tono, estructura, longitud)
- Aprobar o pedir regeneración con feedback específico a la carta

**Contrato de datos (propuesto):**
```ts
// Lectura — misma ViewThreePayload, pero solo motivation_letter tiene contenido
GET /api/v1/jobs/:source/:jobId/view3
// O endpoint dedicado:
GET /api/v1/jobs/:source/:jobId/documents/motivation_letter

// Escritura
PUT /api/v1/jobs/:source/:jobId/editor/review_motivation_letter/state
// payload: { decision: "approve" | "request_regeneration" | "reject", feedback?: string }
```

**Layout:** B4 con tab COVER_LETTER activo. Tabs CV y EMAIL aparecen en estado `pending`:

```
┌─ LeftNav ─┬── [COVER_LETTER*] [CV — pending] [EMAIL — pending] ─┬── Context (w-72) ──┐
│           ├────────────────────────────────────────────────────  │                    │
│           │                                                       │ PHASE: LETTER_GATE │
│           │  Rich Text Editor — motivation_letter content         │                    │
│           │                                                       │ Evidence usada     │
│           │                                                       │ [P_EXP_005] ...    │
│           │                                                       │                    │
│           │                                                       │ [REQUEST_REGEN]    │
│           │                                                       │ [APPROVE_LETTER]   │
└───────────┴───────────────────────────────────────────────────────┴────────────────────┘
```

**Tab states:**
- `COVER_LETTER*` → activo, editable, tiene contenido
- `CV — pending` → visible pero locked, tooltip `"approve letter first"`
- `EMAIL — pending` → visible pero locked, tooltip `"approve letter first"`

**Routing:**
- `approve` → `tailor_cv`
- `request_regeneration` → `generate_motivation_letter`
- `reject` → END

**Dudas abiertas:**
- ¿El output de `generate_motivation_letter` es texto completo o `MotivationLetterDeltas` (como PREP_MATCH)?
- Si son deltas, ¿la UI los renderiza a texto completo o muestra el diff sobre el base template?
- ¿El context panel del DEFAULT puede enlazar texto → evidencia (anotación)? ¿O es solo lectura de refs?

---

## Gate C.2 — Tailored CV

### Nodos: `tailor_cv` → `review_cv`

**Estado pipeline:** Planeado — sin implementar.

**Objetivo del operador:**
- Leer el CV adaptado generado por el LLM
- Verificar que los bullets añadidos/modificados son coherentes con el perfil real
- Editar directamente en el editor (reordenar, completar, eliminar huecos)
- Aprobar o pedir regeneración

**Contrato de datos (propuesto):**
```ts
GET /api/v1/jobs/:source/:jobId/documents/cv
PUT /api/v1/jobs/:source/:jobId/editor/review_cv/state
```

**Dudas abiertas:**
- ¿`tailor_cv` genera un CV completo en markdown o solo deltas (`cv_injections` como PREP_MATCH)?
- Si son deltas, ¿cómo se aplican al base CV? ¿Jinja2 rendering o merge programático?
- ¿La UI muestra el CV base con highlights de lo que cambió vs. lo que dejó igual?
- ¿El base CV viene de `reference_data/cv_profile_graph_saved.json` o de otro artefacto?

**Layout:** Tab CV activo, tabs COVER_LETTER (approved ✓) y EMAIL (pending):

```
┌─ LeftNav ─┬── [✓ COVER_LETTER] [CV*] [EMAIL — pending] ─┬── Context (w-72) ──┐
│           ├─────────────────────────────────────────────  │                    │
│           │                                               │ PHASE: CV_GATE     │
│           │  Rich Text Editor — tailored CV content       │                    │
│           │  [secciones: Education / Experience / Skills] │ [diff view toggle] │
│           │                                               │  ↑ future feature  │
│           │                                               │ [REQUEST_REGEN]    │
│           │                                               │ [APPROVE_CV]       │
└───────────┴───────────────────────────────────────────────┴────────────────────┘
```

**Routing:**
- `approve` → `draft_email`
- `request_regeneration` → `tailor_cv`
- `reject` → END

---

## Gate C.3 — Application Email

### Nodos: `draft_email` → `review_email`

**Estado pipeline:** Planeado — sin implementar.

**Objetivo del operador:**
- Leer el email de aplicación generado (corto — 2-3 líneas)
- Verificar subject y body, ajustar tono
- Aprobar — este es el último gate antes de `render`

**Contrato de datos (propuesto):**
```ts
GET /api/v1/jobs/:source/:jobId/documents/application_email
PUT /api/v1/jobs/:source/:jobId/editor/review_email/state
```

**Layout:** Tab EMAIL activo, otros dos approved:

```
┌─ LeftNav ─┬── [✓ COVER_LETTER] [✓ CV] [EMAIL*] ─┬── Context (w-72) ──┐
│           ├──────────────────────────────────────  │                    │
│           │                                        │ PHASE: EMAIL_GATE  │
│           │  To: [contact_info.email]              │                    │
│           │  Subject: [generated subject]          │ Contacto detectado │
│           │  ─────────────────────────────         │  Dr. Müller        │
│           │  [email body — 2-3 líneas]             │  hr@tu-berlin.de   │
│           │                                        │                    │
│           │                                        │ [REQUEST_REGEN]    │
│           │                                        │ [APPROVE — RENDER] │
└───────────┴────────────────────────────────────────┴────────────────────┘
```

**Diferencia con letter/CV:**
- Email es corto — el editor puede ser un simple textarea vs. Slate richtext
- Muestra el contact_info detectado por el scraper (email + nombre) para confirmación visual
- El `APPROVE — RENDER` es el CTA final de toda la pipeline — debe ser más prominente (color primario)

**Routing:**
- `approve` → `render` (luego automático a `package`)
- `request_regeneration` → `draft_email`
- `reject` → END

**Dudas abiertas:**
- ¿`draft_email` genera subject + body juntos o solo body?
- ¿El email tiene formato HTML o texto plano?
- ¿Se puede editar el contact email si el scraper detectó uno incorrecto?

---

## 6. Estilos Compartidos (Hereda de B4)

Todos los gates reusan los estilos definidos en B4:
- Tab bar con estado visual: `approved ✓` / `active *` / `pending (locked)`
- `<DocumentEditor>` con Slate (letter/CV) o textarea simple (email)
- `<ContextPanel>` derecho con evidence refs
- `<RegenModal>` con textarea de feedback
- Bottom bar con Save (Ctrl+S) + Approve (Ctrl+Enter)

**Diferencia visual por gate:**
- `pending` tabs: `opacity-40 cursor-not-allowed` + tooltip `"complete previous gate first"`
- `approved` tabs: `border-b-2 border-primary text-primary` + `✓` prefix
- CTA final (approve email): `bg-primary text-[#0c0e10] font-bold` (más prominente que los anteriores)

---

## Notas de Implementación

- **El componente B4 (`ViewThree`) ya existe** — el DEFAULT puede reusar el mismo componente con props que controlan qué tabs están activos/locked
- La prop `mode: "prep_match" | "default_gate"` + `activeDoc: "cv" | "motivation_letter" | "email"` + `approvedDocs: string[]` daría control completo
- Alternativamente, el routing en el Job Flow Inspector navega a la misma URL `/jobs/:source/:jobId?view=view-3&doc=motivation_letter` con el tab correspondiente preseleccionado
- **Prioridad:** Implementar después de que los nodos backend existan — el componente UI está prácticamente listo via B4
- Los estados `pending` en tabs son la única adición de componentes necesaria

---

## Relación con B4

Actualización pendiente en B4: añadir nota que indica que la vista de 3 tabs simultáneos
es específica de PREP_MATCH, y que en el DEFAULT pipeline cada gate abre la misma view
con un solo tab activo y los demás en pending/approved según el progreso del pipeline.
