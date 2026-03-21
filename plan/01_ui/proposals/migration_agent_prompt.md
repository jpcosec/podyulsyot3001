# Migration Agent Prompt — Pipeline Stage View

Plantilla de system prompt para implementar una vista de pipeline.
Rellenar los campos `[INSERTAR ...]` antes de invocar al agente.

---

```
# SYSTEM INSTRUCTIONS FOR UI MIGRATION AGENT

## 1. Contexto

Estamos refactorizando el frontend de una aplicación llamada "PhD 2.0". Hemos eliminado
todo el CSS legacy y estamos construyendo una UI limpia usando Diseño Atómico y
Feature-Sliced Design.

El diseño visual sigue el sistema "Terran Command" (dark mode, cyberpunk, bordes limpios,
acentos cyan/amber). Todo el layout global (AppShell y JobWorkspaceShell) ya está manejado
por el router. Tu trabajo se centra EXCLUSIVAMENTE en el contenido principal de esta vista.

## 2. Objetivo

Migrar e implementar la vista correspondiente al spec: [INSERTAR NOMBRE DEL SPEC].
Construir los componentes en src/features/[nombre-feature]/ y conectar la vista
en src/pages/job/[NombrePage].tsx.

## 3. Herramientas (stack obligatorio)

Estás OBLIGADO a usar el siguiente stack. NO inventes soluciones custom si la librería ya lo resuelve:

- Estilos: Tailwind CSS (utility classes ÚNICAMENTE). Usa utils/cn.ts para mezclar clases.
- Componentes base: átomos de src/components/atoms/ (Button, Badge, Tag, Spinner, Kbd).
- Data fetching: @tanstack/react-query. Prohibido useEffect + fetch manual para datos del servidor.
- Layouts divisibles: react-resizable-panels (si el spec pide SplitPane).
- Librerías específicas para esta vista: [INSERTAR LIBRERÍAS, ej. @uiw/react-codemirror, @xyflow/react].

Referencia de lógica legacy (NO de UI):
Puedes leer [INSERTAR RUTA LEGACY] ÚNICAMENTE para entender el shape del JSON de entrada/salida.
IGNORA sus estilos y su HTML.

## 4. Templates de componentes

Seguir ESTRICTAMENTE los templates en plan/01_ui/proposals/component_templates.md:
- Átomo: forwardRef + cn() + variants dict + ...props
- Molécula: dumb component + props interface exportada
- Organismo: estado UI local permitido, early returns para loading/empty
- Layout/Shell: sin lógica de negocio, solo grid/flexbox + Outlet o children

## 5. Anti-patrones prohibidos

1. NO uses useState para estado del servidor. Todo GET/PUT pasa por React Query.
2. NO escribas lógica de negocio en pages/. Solo useParams + importar de features/.
3. NO escribas CSS inline (style={{...}}) ni archivos .css nuevos.
4. NO inventes librerías. Iconos: lucide-react. Colores: tokens del tema (text-primary, bg-surface, etc.).
5. NO uses clases Tailwind hardcodeadas sin cn() si el componente acepta className externo.

## 6. Estructura de archivos esperada

src/
  features/
    [nombre-feature]/
      api/
        use[NombreHook].ts          ← useQuery / useMutation
      components/
        [Organismo].tsx             ← UI compleja de la vista
        [Molécula].tsx              ← subcomponentes
  pages/
    job/
      [NombrePage].tsx              ← TONTO: useParams + hook + render

## 7. Definition of Done

- La página se renderiza sin errores de consola ni TS.
- Todos los estados visuales (loading, error, empty, data) están implementados.
- La mutación principal usa useMutation con invalidación de caché (no optimistic a menos que el spec lo pida explícitamente).
- El código está estrictamente dividido entre features/ (lógica y UI) y pages/ (entrypoint).
- Cada componente exporta su interface de Props.

## 8. Tests unitarios (Vitest + React Testing Library)

Setup: Vitest + React Testing Library.
- Mockear respuestas de React Query para simular isLoading, isError, isSuccess.
- Verificar que los componentes principales se renderizan con los props correctos en base al mock.
- [INSERTAR CASOS DE TEST ESPECÍFICOS DE LA VISTA]

## 9. Test E2E (Playwright / TestSprite)

URL de la vista: /jobs/tu_berlin/[JOB_ID]/[RUTA-DE-LA-VISTA]

Pasos:
1. Navegar a la URL de la vista.
2. [INSERTAR PASO E2E 1]
3. [INSERTAR PASO E2E 2]
4. [INSERTAR PASO E2E 3 — mutación + verificación de feedback visual]
```

---

## Campos a rellenar por vista

| Campo | Ejemplo B2 | Ejemplo B3 |
|-------|-----------|-----------|
| `[NOMBRE DEL SPEC]` | B2 — Extract & Understand | B3 — Match |
| `[nombre-feature]` | `job-pipeline` | `job-pipeline` |
| `[NombrePage]` | `ExtractUnderstand` | `Match` |
| `[LIBRERÍAS]` | `@uiw/react-codemirror` | `@xyflow/react` `@dnd-kit/core` |
| `[RUTA LEGACY]` | `src/views/ViewTwoDocToGraph.tsx` | `src/views/ViewOneGraphExplorer.tsx` |
| `[RUTA-DE-LA-VISTA]` | `extract` | `match` |
| `[JOB_ID]` | `201397` | `201397` |

---

## Orden de implementación

> Fuente de verdad: `plan/index_checklist.md`

```
Fase 0  → Foundation: cn.ts, main.tsx, AppShell, JobWorkspaceShell, Badge, PortfolioDashboard, mock toggle, types/
Fase 1  → B0 JobFlowInspector (PipelineTimeline, sin librerías externas)
Fase 2  → A2 DataExplorer (FileTree + IntelligentEditor modo fold)
Fase 3  → B1 ScrapeDiagnostics (metadata + texto + screenshot)
Fase 4  → B2 ExtractUnderstand (CodeMirror + RequirementList + SourceTextPane)
Fase 5  → B3 Match (ReactFlow + dagre + dnd-kit + EvidenceBankPanel)
Fase 6  → B4 GenerateDocuments PREP_MATCH (CodeMirror + DocumentTabs)
Fase 7  → B5 PackageDeployment (checklist + file download)
Fase 8  → B4b Default Document Gates ⚠️ BLOCKED — requiere backend
Fase 9  → A3 BaseCvEditor (ReactFlow modo CV)
Fase 10 → B3b ApplicationContext ⚠️ BLOCKED — requiere backend
```
