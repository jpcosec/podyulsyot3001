# Guía de Navegación

> Cómo leer y navegar la documentación del Node Editor.

---

## El Espiritu

Esta documentación describe **cómo construir**, no qué construir. Asume que ya sabes lo que necesitas - aquí encuentras el cómo.

**Principios:**
- **Arquitectura primero** - Entender las capas antes de escribir código
- **Contratos definidos** - Los tipos definen las interfaces entre niveles
- **Ejemplos concretos** - Código real, no teoría abstracta
- **Evolución continua** - Los docs crecen con el código

---

## Estructura de Carpetas

```
plan/
├── ARCHITECTURE.md      ← START HERE
├── GUIDE.md
│
├── 01_L1_ui_app/       ← Orquestación (API, páginas)
├── 02_L2_graph_viewer/  ← Motor espacial (ReactFlow)
├── 03_L3_internal_nodes/ ← Contenido (editores, previews)
│
└── _meta/               ← Arquitectura, contratos, guías
```

---

## Dónde Empezar

### Si quieres entender la arquitectura general
→ `ARCHITECTURE.md`

### Si quieres implementar algo
1. Lee `ARCHITECTURE.md` para entender el nivel
2. Busca el doc específico en L1/L2/L3
3. Consulta `_meta/implementation_example.md` para ejemplos de código

### Si quieres refactorizar
→ `_meta/refactor_knowledgegraph.md`

### Si quieres entender el futuro (Code IDE)
→ `_meta/code_ide_as_graph.md`

---

## Niveles de Profundidad

| Profundidad | Para | Docs |
|-------------|------|------|
| 1. Conceptos | Entender el modelo | `ARCHITECTURE.md`, `_meta/*` |
| 2. Contratos | Integrar partes | `_meta/flow_contract.md` |
| 3. Implementación | Escribir código | `L*_*/*.md`, `_meta/implementation_example.md` |

---

## Orden de Lectura Recomendado

1. **`ARCHITECTURE.md`** - Modelo de 3 capas (15 min)
2. **`_meta/flow_contract.md`** - Cómo fluyen datos (10 min)
3. **`_meta/implementation_example.md`** - Ejemplo completo (15 min)
4. Doc específico del nivel que necesitas

---

## Mapa de Contenedores (Anidamiento)

```
┌─────────────────────────────────────────────────────────────┐
│ 01_L1_ui_app (Orquestador, Fetching, Schema)                │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ 02_L2_graph_viewer (ReactFlow, Dagre, Topología)    │   │
│   │                                                     │   │
│   │   ┌────────────────────────────────────────────┐   │   │
│   │   │ 03_L3_internal_nodes (Carne, UI rica)      │   │   │
│   │   └────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Preguntas Frecuentes

**¿Necesito leer todo?**
No. Lee `ARCHITECTURE.md` y luego el doc específico de tu nivel.

**¿Los docs tienen código?**
Sí. Los docs en `_meta/` tienen ejemplos concretos en TypeScript.

**¿Esto es para runtime?**
No. Los docs son arquitectura y contratos. El runtime es el código en `src/`.

**¿Cómo sugiero cambios?**
Edita el doc correspondiente y haz PR. Los docs evolucionan con el código.

---

## Glosario

| Término | Significado |
|---------|-------------|
| AST | Abstract Syntax Tree - representación intermedia del grafo |
| L1/L2/L3 | Niveles de arquitectura (App/Canvas/Node) |
| Schema | JSON declarativo que dicta cómo un dominio se traduce a grafo |
| Token | Referencia visual (color, borde) agnóstica al dominio |
| Cascarón | Componente que envuelve contenido (NodeShell) |
| Payload | La "carne" o datos crudos (markdown, json) que L3 renderiza |
| Motor de Traducción | Función `schemaToGraph()` que convierte datos a AST |
| Data Down | Información fluye hacia abajo como props/AST |
| Events Up | Intenciones fluyen hacia arriba como callbacks |
