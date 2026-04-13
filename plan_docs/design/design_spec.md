Aquí tienes el **Documento de Diseño Arquitectónico (ADD)** para Ariadne 2.0. Este documento cristaliza todas las decisiones, abstracciones y patrones que hemos definido. Es ideal para que lo guardes en `docs/architecture/system_design.md` y sirva como la "Biblia" para cualquier desarrollador que entre al proyecto.

---

# 🏛️ Ariadne 2.0: System Design Summary

## 1. Resumen Ejecutivo
**Ariadne 2.0** es un motor de automatización web semántica basado en LangGraph. Utiliza un patrón de **Arquitectura Hexagonal (Puertos y Adaptadores)** combinado con un bucle cognitivo **Sense-Think-Act**. Su objetivo es navegar portales web complejos (SPA, Shadow DOMs, Anti-Bots) minimizando el uso de LLMs mediante un grafo topológico que "aprende" las rutas (Self-Healing) y delega el I/O pesado a periféricos aislados.

## 2. Las 4 Invariantes Arquitectónicas (Leyes de la Física)
Cualquier PR que viole estas reglas debe ser rechazado automáticamente:
1. **El Event Loop es Sagrado:** Cero I/O síncrono bloqueante en el "Hot Loop" de LangGraph.
2. **El Navegador es un Singleton:** Un único contexto de navegador por misión para preservar el estado efímero (React/Vue) y cookies.
3. **El DOM es Hostil:** Las inyecciones de código (como *Set-of-Mark*) operan sobre *overlays* desconectados. Prohibido mutar el árbol original.
4. **El Enrutamiento es Finito:** Circuit Breakers obligatorios. Todo bucle de rescate LLM tiene un límite estricto (ej. 3 intentos) antes de pausar y escalar a un humano (HITL).

---

## 3. Topología del Sistema (El Modelo de Teseo)

El sistema se divide en tres capas estrictas, aisladas mediante Inyección de Dependencias.

### Capa 1: La Periferia (I/O Físico)
Interfaces puras que conectan el cerebro con la realidad.
* **`Sensor` (Protocol):** Modo "Read-Only". Captura el estado del mundo (`SnapshotResult` con DOM simplificado, URL y Captura Base64).
* **`Motor` (Protocol):** Modo "Write-Only". Ejecuta comandos atómicos (`Click`, `Fill`).
* **`BrowserAdapter`:** Implementación concreta (ej. `Crawl4AIAdapter` o `BrowserOSAdapter`). Controla el ciclo de vida (`__aenter__`) y verifica la salud de la conexión (`is_healthy()`).

### Capa 2: Dimensión Cognitiva (Memoria Activa)
Estructuras de datos en memoria que resuelven problemas espaciales y de ruta.
* **`Labyrinth` (Grafo Topológico):** Responde a *"¿Dónde estoy?"*. Conoce las habitaciones (URLs/Estados) y evalúa los predicados de presencia usando selectores CSS, XPath o heurísticas locales.
* **`AriadneThread` (Vector de Misión):** Responde a *"¿Hacia dónde voy?"*. Contiene la lista de transiciones exitosas para una misión (ej. `easy_apply`).

### Capa 3: Los Actores (Nodos LangGraph)
Funciones o Clases invocables que dirigen el flujo, recibiendo la Capa 1 y 2 inyectadas.
* **`Theseus` (Fast Path):** Ejecutor determinista. Si el `Sensor` ve lo que pide el `Labyrinth`, usa el `Motor` para seguir el `AriadneThread`. Costo: $0.
* **`Delphi` (Rescue Agent):** El Oráculo (LLM o Humano). Entra cuando Theseus se pierde. Usa Visión y herramientas MCP (*Set-of-Mark*) para encontrar una salida.
* **`Recorder` (Asimilador):** El escriba que actualiza la memoria. Escucha las victorias de Delphi para expandir el `Labyrinth` y tejer nuevos `AriadneThreads`.

---

## 4. El Motor de Asimilación Dual (Self-Healing)

Ariadne 2.0 no requiere programar JSONs a mano para portales nuevos. Aprende de dos fuentes de verdad:

1. **Grabación Activa (LLM/Theseus):** Mientras LangGraph opera, el `Motor` emite una traza de sus acciones exitosas al `Recorder`.
2. **Grabación Pasiva (Zero-Code):** Un humano navega usando Chrome, exporta la sesión de Chrome DevTools Recorder (un archivo `.json` crudo), y el `Recorder` lo asimila, traduciendo clics físicos a intenciones semánticas ligadas a un perfil de usuario.

---

## 5. Diagrama de Arquitectura (Object & Data Flow)

```mermaid
flowchart TD
    classDef protocol fill:#f3e5f5,stroke:#1565c0,stroke-width:2px,stroke-dasharray: 5 5,color:#000;
    classDef concrete fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000;
    classDef memory fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000;
    classDef node_fast fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000;
    classDef node_slow fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#000;
    classDef system fill:#eceff1,stroke:#616161,stroke-width:2px,color:#000;

    subgraph Periphery ["🔌 La Periferia (Adaptadores I/O)"]
        direction TB
        Sensor[["«Protocol»\nSensor\n.perceive()"]]:::protocol
        Motor[["«Protocol»\nMotor\n.act()"]]:::protocol
        
        BrowserAdapter["🌐 BrowserAdapter\n(Implementa Sensor y Motor)"]:::concrete
        BrowserAdapter -.->|Bind| Sensor
        BrowserAdapter -.->|Bind| Motor
    end

    subgraph Cognition ["🧠 Dimensión Cognitiva (Memoria Activa)"]
        direction TB
        Labyrinth["🏛️ Labyrinth\n.identify_room(snapshot)\n.expand(room_data)"]:::memory
        Thread["🧵 AriadneThread\n.get_next_step(room_id)\n.add_step(edge)"]:::memory
    end

    subgraph LangGraph ["⚡ Nodos del Grafo (Inyección de Dependencias)"]
        direction LR
        Theseus{"⚔️ Theseus\n(Determinismo)"}:::node_fast
        Delphi["🔮 Delphi\n(LLM/HITL Rescue)"]:::node_slow
        Recorder["📜 Recorder\n(Asimilación)"]:::system
    end

    %% Interacciones
    Theseus -->|1. perceive()| Sensor
    Theseus <-->|2. identify_room()| Labyrinth
    Theseus <-->|3. get_next_step()| Thread
    Theseus -->|4. act(command)| Motor

    Theseus -->|Falla/Se pierde| Delphi
    Delphi -->|1. perceive()| Sensor
    Delphi -->|2. act(command)| Motor

    Motor -.->|Traza interna| Recorder
    Chrome[("Chrome DevTools\n(Exportación Pasiva)")]:::system -.->|Traza humana| Recorder
    
    Recorder -->|1. expand()| Labyrinth
    Recorder -->|2. add_step()| Thread
```
