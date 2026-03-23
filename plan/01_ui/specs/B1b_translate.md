# Spec B1b — Translate Diagnostics

**Feature:** `src/features/job-pipeline/`
**Page:** `src/pages/job/TranslateDiagnostics.tsx`
**Librerías:** `@tanstack/react-query` · `lucide-react`
**Fase:** 3b

---

## Migration Notes

**Legacy source:** Pipeline stage visible en `JobFlowInspector` pero sin página dedicada  
**To migrate:** crear página de diagnóstico + ficha con metadata de traducción  
**Status:** 🔲 NUEVO — requiere implementación

Este paso intermedia entre scrape y extract. Sirve para:
- Verificar si se aplicó traducción
- Ver el texto original vs traducido (si ambos están disponibles)
- Diagnosticar problemas de traducción

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v2/query/jobs/:source/:job_id/artifacts/translate_if_needed` → `ArtifactListPayload`
  ```ts
  {
    source, job_id, node_name: "translate_if_needed",
    files: { path, content_type, content, editable }[]
    // paths: approved/state.json
  }
  ```

**Estado del artifact (state.json):**
```ts
{
  translated: boolean,
  original_language: string,   // "de", "es", etc.
  target_language: string,      // "en"
  chunks_processed: number,
  char_count_original?: number,
  char_count_translated?: number
}
```

**Escritura:** Ninguna (diagnóstico solamente).

---

## 3. Composición de la UI y Layout

**Layout:** Columna única con cards + right control panel.

```
┌──────────────── Main ─────────────────────┬── Control Panel ──┐
│  [TRANSLATE_DIAGNOSTICS header]          │ [PHASE: TRANSLATE] │
│                                           │                    │
│  ┌── Translation Status ─────────────┐  │ Status: TRANSLATED│
│  │ ✓ TRANSLATED                       │  │ Languages: de→en  │
│  │                                     │  │ Chunks: 3         │
│  └─────────────────────────────────────┘  │                    │
│                                           │ [ADVANCE →]        │
│  ┌── Translation Comparison ───────────┐  │                    │
│  │ [Deutsch]      [English]            │  │                    │
│  │ original text  translated text     │  │                    │
│  └─────────────────────────────────────┘  │                    │
└───────────────────────────────────────────┴────────────────────┘
```

**Casos de uso:**

| `translated` | UI                                      |
|--------------|----------------------------------------|
| `false`      | Card "NO_TRANSLATION_NEEDED" — texto ya estaba en target language |
| `true`       | Translation Status card + Translation Comparison |

**Componentes Core:**
- `<DiagnosticCard>` (molecule) — wrapper para todas las cards
- `<ControlPanel>` (molecule) — panel de control genérico
- `<TranslationComparison>` — texto original vs traducido (side-by-side)
- `<TranslateControlPanel>` — deprecated, usar `<ControlPanel>`

---

## 4. Estilos (Terran Command)

- Cards: `bg-surface-container-low panel-border`
- Translation status badge:
  - `translated=true` → `bg-primary/10 text-primary border border-primary/30` + checkmark icon
  - `translated=false` → `bg-surface-low text-on-muted border border-outline/30`
- Character delta: `text-primary` si reducción normal, `text-error` si >20% pérdida
- Card headers: `font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]`

**Interacciones:**
- "ADVANCE" → navega a `/jobs/:source/:jobId/extract`
- EXPAND en original text → muestra texto completo

---

## 5. Archivos a crear

```
src/features/job-pipeline/
  components/
    TranslateStatusCard.tsx        badge + language info + chunks
    CharacterCountCard.tsx         before/after chars con delta
    OriginalTextPreview.tsx        texto original colapsable
    TranslateControlPanel.tsx      advance button
src/pages/job/
  TranslateDiagnostics.tsx         TONTO: useParams + hook + render
```

---

## 6. Definition of Done

```
[ ] TranslateDiagnostics renderiza sin errores para job 201397 (mock)
[ ] TranslateStatusCard muestra "TRANSLATED" con languages correctos
[ ] CharacterCountCard muestra counts + delta
[ ] "ADVANCE" navega a /jobs/tu_berlin/201397/extract
[ ] Estado loading muestra Spinner
[ ] Estado translated=false muestra "NO_TRANSLATION_NEEDED"
[ ] Sin datos hardcodeados — todo dato proviene del mock/API
```

---

## 7. E2E (TestSprite)

**URL:** `/jobs/tu_berlin/201397/translate`

1. Verificar que `<TranslateStatusCard>` muestra "TRANSLATED"
2. Verificar que languages son "de → en"
3. Verificar que CharacterCountCard muestra los counts del mock
4. Click en ADVANCE → verificar navegación a `/jobs/tu_berlin/201397/extract`

---

## 8. Git Workflow

### Commit al cerrar la fase

```
feat(ui): implement translate diagnostics (B1b)

- TranslateStatusCard with language info and translation status
- CharacterCountCard with before/after comparison
- OriginalTextPreview collapsible component
- TranslateControlPanel with advance action
- Connected to useArtifacts hook
```

### Changelog entry (changelog.md)

```markdown
## YYYY-MM-DD

- Implemented B1b Translate Diagnostics: translation status card,
  character count comparison, and translate control panel.
```

### Checklist update (index_checklist.md)

- [x] B1b Translate Diagnostics
