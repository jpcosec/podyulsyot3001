# Guia de Implementacion Front-end: Nodos Contenedores (Sub-flows)

> Status note (2026-03-20): this guide captures a useful frontend implementation strategy, but parts of it are now design-history relative to the current `CvGraphEditorPage` implementation. Treat it as a reference guide, not as the sole canonical description of the active sandbox.


Este documento detalla la estrategia tecnica para implementar jerarquias, layouts internos y *edge proxying* utilizando **React Flow**, superando sus limitaciones de posicionamiento absoluto.

## 1. Conceptos Core en React Flow para Jerarquias

- `parentNode`: Propiedad en el objeto del nodo hijo que define su pertenencia a un contenedor.
- `extent: 'parent'`: Regla opcional para evitar que un nodo hijo sea arrastrado fuera de los limites visuales de su padre sin una accion explicita.
- `hidden`: Propiedad dinamica para ocultar nodos hijos cuando el padre se colapsa.

## 2. Estrategia de Implementacion por Feature

### A. Estado de Expansion/Colapso

- **Implementacion:** El *Custom Node* contenedor debe tener un estado local o leer de `data.isExpanded`.
- **Accion:** Al alternar el estado, debes iterar sobre todos los nodos en el store de Zustand. Para todos los nodos donde `parentNode === contenedor.id`, cambia su propiedad `hidden` a `true/false`.
- **Redimensionamiento:** Usa el hook `useUpdateNodeInternals` de React Flow despues de expandir/colapsar para obligar al motor a recalcular los *handles* y las dimensiones del nodo padre.

### B. Auto-Layout Interno (Lista Secuencial)

- **El Problema:** React Flow posiciona todo de forma absoluta (`x`, `y`). No entiende de "listas verticales".
- **La Solucion:** Crea una funcion de calculo en el store. Cuando un nodo entra al contenedor (o se reordena), calcula su posicion `y` basandote en su indice:
  `y = padding_top + (index * (altura_nodo_hijo + gap))`
  La posicion `x` debe ser un margen fijo relativo al padre.

### C. Drag & Drop de Absorcion y Extraccion

- **Evento Clave:** Usa `onNodeDragStop`.
- **Logica de Absorcion:**
  1. Obten las coordenadas del nodo que se solto.
  2. Usa geometria simple (bounding boxes) para detectar si cayo *dentro* del area visual de un nodo contenedor expandido.
  3. Si es asi, actualiza el nodo en el store: asignale `parentNode: id_del_contenedor` y ajusta su `x` e `y` para que sea relativo al padre.
- **Logica de Extraccion:** Si un nodo que tenia `parentNode` es soltado fuera del *bounding box* de su padre, elimina la propiedad `parentNode` y convierte sus coordenadas relativas en coordenadas absolutas del lienzo principal.

### D. Enrutamiento de Relaciones (Edge Proxying)

- **Implementacion mediante Custom Edge:** Crea un componente `<ProxyEdge>`.
- **Logica Interna:** El edge recibe el `source` y `target`.
  1. Revisa en el store si el nodo `target` esta `hidden` debido a que su `parentNode` esta colapsado.
  2. Si esta oculto, el *Custom Edge* intercepta el renderizado y en su lugar calcula el trazado (`getBezierPath`) apuntando a las coordenadas del `parentNode`.
  3. Aplica estilos SVG condicionales (`strokeDasharray="5,5"`) para representar visualmente el estado "fantasma".

## 3. Criterios de Aceptacion (Testing Checklist)

- [ ] **Expansion:** Al hacer clic en colapsar, el contenedor se encoge y los nodos hijos desaparecen de la vista.
- [ ] **Absorcion:** Arrastrar un nodo libre sobre un contenedor expandido lo convierte en hijo. El nodo se acomoda automaticamente en forma de lista vertical.
- [ ] **Extraccion:** Arrastrar un hijo fuera del contenedor lo independiza y mantiene su posicion en el lienzo donde lo solte.
- [ ] **Edge Proxy:** Conecto un nodo libre a un nodo hijo. Al colapsar el padre, la linea no desaparece, sino que ahora apunta al padre y se vuelve punteada.
- [ ] **Reordenamiento:** Dentro del contenedor, puedo arrastrar el hijo #3 por encima del #1 y sus posiciones `y` se recalculan automaticamente.

## 4. Que Evitar (Anti-patrones)

1. **Evitar `onNodeDrag` para calculos pesados:** No intentes calcular intersecciones de dropzones o auto-layout *mientras* el raton se esta moviendo (`onNodeDrag`). Hazlo exclusivamente al soltar el raton (`onNodeDragStop`) para no destruir los FPS del navegador.
2. **Confundir coordenadas absolutas vs relativas:** En React Flow, si un nodo tiene `parentNode`, su `x` e `y` son relativas a la esquina superior izquierda de su padre, no del lienzo. Si extraes un hijo, DEBES calcular su nueva posicion absoluta sumando las coordenadas del padre, o saltara por la pantalla.
3. **Ignorar el z-index en la absorcion:** Los nodos contenedores deben tener un `z-index` menor (ej. `-1`) que los nodos estandar. Si un contenedor tiene un z-index alto, interceptara los clics y el usuario no podra seleccionar los nodos que estan dentro de el.
