# 06 UI & Graph Architecture Layers

## Goal
Establecer un límite estricto y espacial ("Matrioshka" o muñecas rusas) entre la interfaz general de la aplicación, el motor de renderizado del grafo, y el contenido interno de los nodos. Esto erradica el patrón de "God Component" y permite la reutilización del canvas en cualquier dominio (CV, Job, Portfolio).

## El Modelo Mental (DOM Mapping)
La aplicación se divide en 3 capas de representación espacial y de responsabilidad. Cada capa tiene su propia tríada de `Datos -> Esquema -> UI`, pero **operan en ámbitos estrictamente aislados**.

| Nivel | Rol | Ruta Mental (DOM) |
|---|---|---|
| **L1: UI / APP** | El Macro-Contenedor | `/html/body/div/div[1]/nav` |
| **L2: Graph Viewer** | El Motor Espacial | `.../main/section/div` |
| **L3: Internal Node**| El Contenido Rico | `.../div/div[1]/div[1]/...` |

---

## Nivel 1: UI / APP (El Orquestador)
Gobierna la pantalla completa. Su trabajo es cargar los datos, leer el esquema de dominio (ej. `match.schema.json`) y decidir qué vista se muestra.

* **Responsabilidades:**
  * Navegación global (Sidebars, Breadcrumbs, Tabs).
  * Obtención de datos (Fetching API / Neo4j / Local Mock).
  * Filtrado de negocio (ej. "Mostrar solo skills técnicos").
  * Inyectar los datos limpios al Nivel 2.
* **Componentes Típicos:**
  * `AppShell.tsx`, `JobWorkspaceShell.tsx`
  * `MatchControlPanel.tsx`, `EvidenceBankPanel.tsx`
  * Páginas orquestadoras (`Match.tsx`, `BaseCvEditor.tsx`)
* **Lo que NO hace:** Dibujar nodos, calcular layouts X/Y, usar hooks de React Flow.

## Nivel 2: Graph Viewer (El Motor Espacial)
Es el lienzo de dibujo (`UniversalGraphCanvas`). Trata a los nodos como "cajas negras". Solo sabe de coordenadas espaciales, conexiones topológicas y eventos de interacción.

* **Responsabilidades:**
  * Renderizar `<ReactFlow>` puro.
  * Dibujar los cascarones de los nodos (bordes, colores de fondo según tokens, *handles*).
  * Dibujar las aristas (curvas de Bezier, `ProxyEdges`).
  * Ejecutar el motor de Layout matemático (Dagre/ELK).
  * Emitir eventos de clic hacia el Nivel 1 (`onNodeClick`).
* **Componentes Típicos:**
  * `<UniversalGraphCanvas>` (El antiguo `KnowledgeGraph.tsx` refactorizado).
  * `<UniversalNodeShell>` y `<UniversalGroupShell>`.
  * `<UniversalEdge>` y `<ProxyEdge>`.
* **Lo que NO hace:** Saber qué es un "Candidato" o "Oferta". Renderizar editores de texto complejos o lógica de formularios.

## Nivel 3: Internal Representation (La "Carne")
Son los componentes que viven *dentro* del `UniversalNodeShell`. Son completamente agnósticos al grafo; funcionarían igual si los pones en una tabla o un modal tradicional.

* **Responsabilidades:**
  * Mostrar datos enriquecidos o interactivos.
  * Renderizar vistas colapsables internas.
  * Manejar estados de edición locales (ej. tipar en un editor Markdown).
* **Componentes Típicos:**
  * `<IntelligentEditor mode="tag-hover">`
  * `<JsonPreview>`, `<MarkdownPreview>`, `<ImagePreview>`
  * Filas de atributos y `<RequirementItem>`
* **Lo que NO hace:** Llamar a `useReactFlow()`. Centrar la cámara. Saber quién es su nodo padre o a quién está conectado.

---

## La Regla de Oro (Strict Boundaries)
**Un nivel no puede saltarse a otro ni conocer la lógica del otro.**

1. **Inversión de Control:** El Nivel 3 no puede decirle al Nivel 2 que haga zoom. El Nivel 3 emite un evento (`onFocusRequest`), el Nivel 2 lo escucha y ejecuta la animación de la cámara.
2. **Ceguera de Dominio:** El Nivel 2 no puede tener lógica condicional de negocio (ej. `if (node.category === 'person')`). Esa evaluación la hace el Nivel 1 (vía Schema) y le pasa al Nivel 2 una orden visual simple (`themeToken: 'primary'`).

## Mapa Visual de Refactorización

```mermaid
graph TD
    classDef nivel1 fill:#f5eef8,stroke:#76448a,stroke-width:2px;
    classDef nivel2 fill:#e8f8f5,stroke:#117a65,stroke-width:2px;
    classDef nivel3 fill:#fef9e7,stroke:#b7950b,stroke-width:2px;

    subgraph L1 [Nivel 1: UI / APP]
        direction TB
        Layout[< AppShell > Layouts]:::nivel1
        Sidebar[< Sidebars / Control Panels >]:::nivel1
        Page[< Pagina Orquestadora: Data + Schema >]:::nivel1
    end

    subgraph L2 [Nivel 2: Graph Viewer]
        direction TB
        Canvas[< UniversalGraphCanvas > ReactFlow]:::nivel2
        NodeShell[< UniversalNodeShell > Cajas y Handles]:::nivel2
        Edges[< Edges > Curvas]:::nivel2
    end

    subgraph L3 [Nivel 3: Internal Representation]
        direction TB
        Editor[< IntelligentEditor >]:::nivel3
        Preview[< Json/Markdown Preview >]:::nivel3
        Props[< Atributos y Tags >]:::nivel3
    end

    Page -->|Inyecta AST Array| Canvas
    Canvas --> NodeShell
    NodeShell -->|Lee 'type' e inyecta| Editor
    NodeShell -->|Lee 'type' e inyecta| Preview
