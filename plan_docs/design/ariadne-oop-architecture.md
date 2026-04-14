# Ariadne OOP Architecture Draft

This document captures a proposed object-oriented architecture for Ariadne, separating browser I/O, active memory, and LangGraph actors.

## Conceptual Flow

```mermaid
flowchart TD
    %% Clases y Estilos
    classDef physical fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef memory fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000;
    classDef actor_fast fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000;
    classDef actor_slow fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#000;
    classDef system fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000;

    %% 1. EL MUNDO FISICO - IO
    subgraph Periphery ["🌍 La Periferia - IO Web"]
        Browser(("🌐 Navegador - El Mundo Real")):::physical
        Sensor["👁️ Sensor - Lee el esqueleto HTML/Visual"]:::physical
        Motor["✋ Motor - Ejecuta clics/teclas"]:::physical
    end

    %% 2. LA DIMENSION COGNITIVA - Memoria
    subgraph Cognition ["🧠 Dimensión Cognitiva - Memoria"]
        Laberinto[("🏛️ El Laberinto - Grafo Topológico")]:::memory
        Hilo[("🧵 Hilo de Ariadna - Rutas de éxito")]:::memory
    end

    %% 3. LOS ACTORES - LangGraph
    subgraph Execution ["⚡ El Bucle de Acción - LangGraph"]
        Teseo{"⚔️ Teseo - Ejecutor Determinista"}:::actor_fast
        Delfos["🔮 Oráculo de Delfos - LLM o Humano"]:::actor_slow
        Recorder["📜 Grabador - Observa y Asimila"]:::system
    end

    %% La Fisica Basica
    Browser -.->|Renderiza| Sensor
    Motor -->|Ejecuta| Browser

    %% Percepcion
    Sensor -->|1. Informa la habitación actual| Teseo

    %% Razonamiento Rapido
    Teseo <-->|2. ¿Conozco esta habitación?| Laberinto
    Teseo <-->|3. ¿Hacia dónde voy?| Hilo

    %% Bifurcacion
    Teseo -->|4a. Hay Hilo Fast Path| Motor
    Teseo -->|4b. Perdido / Sin Hilo| Delfos

    %% Exploracion
    Delfos -->|Opción A: Usa deducción y manos virtuales LLM| Motor
    Delfos -->|Opción B: Baja en persona y mueve su mouse Humano| Browser

    %% Aprendizaje y Evolucion
    Motor -->|Registro Activo Teseo/LLM| Recorder
    Browser -.->|Exportación Pasiva - Chrome DevTools| Recorder

    Recorder -.->|Dibuja nuevas habitaciones| Laberinto
    Recorder -.->|Teje una nueva ruta| Hilo
```

## OOP Direction

Pasar de funciones sueltas a un diseño orientado a objetos permite inyectar dependencias explícitas en los nodos de LangGraph y limpiar el uso de `config` como canal implícito de runtime state.

## 1. La Periferia (I/O)

Estos son los protocolos e implementaciones que tocan el navegador.

- `Sensor` (Protocol)
  - Rol: leer la realidad física y traducirla a un DTO.
  - Método clave: `async def perceive(self) -> SnapshotResult`
- `Motor` (Protocol)
  - Rol: ejecutar instrucciones primitivas sobre el navegador.
  - Método clave: `async def act(self, command: MotorCommand) -> ExecutionResult`
- `BrowserAdapter` (Clase concreta)
  - Rol: implementación real del navegador, heredando de `Sensor` y `Motor`.
  - Maneja el ciclo de vida real con `__aenter__` y `__aexit__`.

## 2. La Dimensión Cognitiva (Memoria)

La memoria se separa en dos clases activas.

- `Labyrinth`
  - Rol: entender dónde estamos.
  - Estado interno: grafo de `StateDefinition`.
  - Métodos clave:
    - `identify_room(snapshot: SnapshotResult) -> str`
    - `expand(new_room_data) -> None`
- `AriadneThread`
  - Rol: saber hacia dónde ir para una misión específica.
  - Estado interno: lista de transiciones dirigidas.
  - Método clave: `get_next_step(current_room_id: str) -> Command`

## 3. Los Actores (Nodos de LangGraph)

Los nodos pasan a ser instancias callables con dependencias inyectadas por constructor.

- `Theseus`
  - Rol: ejecutar el camino determinista y barato.
  - Dependencias: `Sensor`, `Motor`, `Labyrinth`, `AriadneThread`.
  - Flujo:
    1. `Sensor.perceive()`
    2. `Labyrinth.identify_room()`
    3. `AriadneThread.get_next_step()`
    4. `Motor.act()`
    5. Si falla o se pierde, deriva a Delfos.
- `Delphi`
  - Rol: rescate LLM/humano cuando Theseus se pierde.
  - Dependencias: `Sensor`, `Motor`, `LLM_Client`.
  - Flujo:
    1. observa con `Sensor`
    2. consulta al LLM con la pantalla cruda
    3. decide una acción visual
    4. ejecuta con `Motor`
- `Recorder`
  - Rol: asimilar eventos y actualizar memoria.
  - Dependencias: `Labyrinth`, `AriadneThread`, `TraceFile`.
  - Flujo:
    1. lee la acción ejecutada
    2. llama a `Labyrinth.expand()` si descubre una pantalla nueva
    3. llama a `AriadneThread.add_step()` para tejer la ruta futura

## LangGraph Wiring Example

```python
# 1. Instanciamos el mundo
adapter = Crawl4AIAdapter()
laberinto = Labyrinth.load_from_db("linkedin")
hilo = AriadneThread.load_from_db("linkedin", mission="easy_apply")

# 2. Instanciamos los actores
teseo = Theseus(sensor=adapter, motor=adapter, labyrinth=laberinto, thread=hilo)
delfos = Delphi(sensor=adapter, motor=adapter, llm_model="gemini-1.5-pro")
recorder = Recorder(labyrinth=laberinto, thread=hilo)

# 3. Armamos el grafo
workflow = StateGraph(AriadneState)
workflow.add_node("teseo", teseo)
workflow.add_node("delfos", delfos)
workflow.add_node("recorder", recorder)

workflow.set_entry_point("teseo")
workflow.add_conditional_edges(
    "teseo",
    route_after_teseo,
    {"recorder": "recorder", "delfos": "delfos"},
)
```

## Object Diagram

```mermaid
flowchart TD
    classDef protocol fill:#f3e5f5,stroke:#1565c0,stroke-width:2px,stroke-dasharray: 5 5,color:#000;
    classDef concrete fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef memory fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000;
    classDef node_fast fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000;
    classDef node_slow fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#000;
    classDef system fill:#eceff1,stroke:#616161,stroke-width:2px,color:#000;

    subgraph Periphery ["🔌 La Periferia - Adaptadores IO"]
        direction TB
        Sensor[["«Protocol» Sensor"]]:::protocol
        Motor[["«Protocol» Motor"]]:::protocol

        BrowserAdapter["🌐 BrowserAdapter - Implementa Sensor y Motor"]:::concrete
        BrowserAdapter -.->|Bind| Sensor
        BrowserAdapter -.->|Bind| Motor
    end

    subgraph Cognition ["🧠 Dimensión Cognitiva - Memoria"]
        direction TB
        Labyrinth["🏛️ Labyrinth - Identifica y Expande"]:::memory
        Thread["🧵 AriadneThread - Gestión de pasos"]:::memory
    end

    subgraph LangGraph ["⚡ Nodos del Grafo - Inyección de Dependencias"]
        direction LR
        Theseus{"⚔️ Theseus - Determinismo"}:::node_fast
        Delphi{"🔮 Delphi - Rescue Agent"}:::node_slow
        Recorder{"📜 Recorder - Assimilator"}:::system
    end

    Theseus -->|1. perceive| Sensor
    Theseus <-->|2. identify_room| Labyrinth
    Theseus <-->|3. get_next_step| Thread
    Theseus -->|4. act-command| Motor

    Theseus -->|Falla/Se pierde| Delphi
    Delphi -->|1. perceive| Sensor
    Delphi -->|2. act-command| Motor

    Motor -.->|Traza de Eventos| Recorder
    Recorder -->|1. expand| Labyrinth
    Recorder -->|2. add_step| Thread
```

## Notes

- `orchestrator.py` becomes a dependency injector instead of a bucket of runtime wiring.
- `Theseus` no longer needs hidden config wiring for browser state.
- `Labyrinth` and `AriadneThread` become active memory objects rather than passive JSON blobs.
- `Recorder` becomes the universal assimilation layer for deterministic and exploratory action traces.
