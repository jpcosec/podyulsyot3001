import { Link } from "react-router-dom";

const STACK_ITEMS = [
  "React Flow (@xyflow/react)",
  "Zustand por slices (grafo / editor / UI)",
  "React Hook Form + Zod para modal tipado",
  "Overlays en portal (modal, menu contextual, edge panel)",
  "Auto-layout inicial con Dagre",
];

const ITERATIONS = [
  {
    name: "Iteracion 1: Workspace + estado base",
    goals: [
      "Ruta sandbox dedicada con layout fullscreen",
      "Canvas + sidebar colapsable",
      "Estados browse/focus con transiciones basicas",
    ],
  },
  {
    name: "Iteracion 2: Nodos y relaciones",
    goals: [
      "Custom nodes/edges",
      "Hover + seleccion + focus visual",
      "Filtro por tipo de relacion",
      "Contenedores colapsados/expandidos con hijos visibles",
    ],
  },
  {
    name: "Iteracion 3: Edit node modal tipado",
    goals: [
      "Formulario RHF+Zod por tipo de nodo",
      "Dirty/save/discard",
      "Guard rule de salida de modo edit",
    ],
  },
  {
    name: "Iteracion 4: Edit relation + drag-to-connect",
    goals: [
      "Panel editable de relacion",
      "onConnectStart/onConnectEnd + menu flotante",
      "Crear y conectar nodo nuevo desde menu",
    ],
  },
  {
    name: "Iteracion 5: Paleta + auto-layout + hardening",
    goals: [
      "Drag and drop desde sidebar",
      "Auto-layout por accion",
      "Optimizacion de rendimiento con memo/selectores",
    ],
  },
];

const ACCEPTANCE = [
  "Focus centra y limita interaccion en no relacionados.",
  "Modal tipado bloquea guardado cuando hay errores.",
  "Dirty state se activa con cambios y se limpia al guardar/descartar.",
  "Drag-to-connect en canvas vacio abre menu contextual en la posicion de suelta.",
  "Menu contextual permite conectar nodo existente o crear uno nuevo conectado.",
  "Filtros y mapeo visual actualizan el canvas en tiempo real.",
  "Nodos contenedor muestran contador en colapsado y revelan hijos al expandir.",
  "Auto-layout reordena nodos sin romper relaciones.",
];

export function NodeEditorPlanPage(): JSX.Element {
  return (
    <section className="panel">
      <div className="breadcrumbs">
        <Link to="/">Portfolio</Link>
        <span>/</span>
        <Link to="/sandbox">Sandbox</Link>
        <span>/</span>
        <span>Node Editor Plan</span>
      </div>

      <h1>Node Editor Implementation Plan</h1>
      <p>
        Plan tecnico de implementacion para la fase de mapeo nodo a nodo, basado en la
        especificacion UX y en patrones de React Flow.
      </p>

      <article className="panel sandbox-card">
        <h2>Documento fuente</h2>
        <p>
          La version completa del plan vive en
          {" "}
          <code>docs/architecture/node_editor_frontend_implementation_plan.md</code>.
        </p>
      </article>

      <article className="panel sandbox-card">
        <h2>Stack recomendado</h2>
        <ul>
          {STACK_ITEMS.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </article>

      <article className="panel sandbox-card">
        <h2>Roadmap por iteraciones</h2>
        {ITERATIONS.map((iteration) => (
          <div key={iteration.name} style={{ marginBottom: 12 }}>
            <h3>{iteration.name}</h3>
            <ul>
              {iteration.goals.map((goal) => (
                <li key={goal}>{goal}</li>
              ))}
            </ul>
          </div>
        ))}
      </article>

      <article className="panel sandbox-card">
        <h2>Criterios de aceptacion</h2>
        <ul>
          {ACCEPTANCE.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </article>
    </section>
  );
}
