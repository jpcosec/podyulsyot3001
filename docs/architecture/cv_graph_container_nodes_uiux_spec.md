# Especificacion de UI/UX: Editor de Grafos (Fase: Estructuras de Documentos)

## 1. Vision General

Esta especificacion define el comportamiento de los "Nodos Contenedores", disenados para mapear informacion jerarquica o estructurada (como secciones de un Curriculum Vitae, capitulos de un documento o parrafos de una carta). Introduce el concepto de anidamiento (nodos dentro de nodos) manteniendo la claridad visual del lienzo.

## 2. Anatomia del Nodo Contenedor

Un nodo contenedor representa una "Seccion" y tiene dos estados visuales excluyentes:

### [A] Estado Colapsado (Por defecto)

- **Visual:** Tamano similar a un nodo estandar.
- **Indicadores:** Muestra un icono de expansion (ej. `>`) y un "Badge" (pildora) con el conteo de elementos internos (ej. `3 Entradas`).
- **Comportamiento:** Se arrastra libremente por el lienzo. Sus nodos internos estan ocultos pero vinculados logicamente; si el padre se mueve, la posicion relativa de los hijos se preserva.

### [B] Estado Expandido

- **Gatillo:** Clic en el icono de expansion o doble clic en la cabecera del contenedor.
- **Visual:** El nodo se redimensiona, convirtiendose en un "mini-lienzo" o panel con fondo contrastante.
- **Layout Interno:** Los nodos internos no flotan libremente, sino que se organizan mediante un **Auto-Layout Vertical** (forma de lista secuencial).

## 3. Interacciones de Anidamiento (Drag & Drop Estructural)

### Absorcion (Insertar)

1. El usuario arrastra un nodo libre sobre un contenedor expandido.
2. **Feedback Visual:** El contenedor muestra un estado de *Dropzone* (borde iluminado o cambio de opacidad).
3. Al soltar, el nodo libre es absorbido, se ajusta al ancho de la lista interna y se posiciona al final de la secuencia.

### Extraccion (Liberar)

1. El usuario arrastra un nodo hijo fuera de los limites visuales del contenedor padre.
2. Al soltarlo en el lienzo exterior, el nodo rompe su vinculo de parentesco y vuelve a ser un nodo libre.

### Reordenamiento Interno

- Dentro del contenedor, el usuario puede arrastrar los nodos hijos hacia arriba o abajo para alterar su orden secuencial (index). Un indicador visual (linea horizontal) muestra donde caera el elemento.

## 4. Enrutamiento de Relaciones (Regla del Proxy Visual)

Manejo de lineas de relacion cuando conectan con nodos anidados:

- **Si el contenedor esta Expandido:** La linea se dibuja con normalidad, atravesando el borde del contenedor padre hasta conectar con el *handle* del nodo hijo especifico.
- **Si el contenedor esta Colapsado:** Para evitar perdida de contexto, la linea se redibuja apuntando al *handle* del nodo padre, pero adopta un **estilo visual de proxy** (ej. linea punteada, semitransparente o de color distintivo) indicando que la relacion real pertenece a un elemento interno.

## 5. Modo Edicion en Contenedores

- **Edicion del Padre:** Al editar el contenedor, el Modal de Edicion incluye una pestana o seccion adicional llamada "Elementos Internos", mostrando una lista en texto plano de los nodos hijos, permitiendo reordenarlos o eliminarlos directamente desde el formulario.
- **Edicion del Hijo:** Se puede acceder al modal de un nodo hijo haciendo doble clic sobre el cuando el contenedor esta expandido.
