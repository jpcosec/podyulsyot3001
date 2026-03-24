# Foundation: Átomos y Moléculas

> UI base que cualquier capa puede consumir. No tiene dependencias internas.

---

## Átomos

| Átomo | Props | Descripción |
|--------|-------|-------------|
| `Button` | `variant: 'primary' \| 'ghost' \| 'danger'`, `size: 'sm' \| 'md'`, `loading?: boolean` | Botón con estados |
| `Badge` | `variant: 'primary' \| 'secondary' \| 'success' \| 'muted'`, `size: 'xs' \| 'sm'` | Indicador de estado |
| `Tag` | `id`, `category: 'skill' \| 'req' \| 'risk'`, `onHover`, `onClick` | Span inline con color |
| `Icon` | `name: string`, `size: 'xs' \| 'sm' \| 'md'` | Wrapper de Lucide |
| `Spinner` | `size: 'xs' \| 'sm' \| 'md'` | Loading indicator |
| `Kbd` | `keys: string[]` | Atajo de teclado |

---

## Moléculas

| Molécula | Dependencias | Descripción |
|----------|--------------|-------------|
| `SplitPane` | - | Wrapper de react-resizable-panels |
| `ControlPanel` | Button, Spinner | Panel genérico con acciones |
| `DiagnosticCard` | Badge, Icon | Tarjeta con estado |
| `FileTree` | Icon | Árbol de archivos |

---

## Reglas

- **Sin dependencias internas** - Un átomo no puede importar otro átomo
- **Sin lógica de negocio** - Solo rendering y eventos simples
- **Consumido por todas las capas** - L1, L2, L3 pueden usarlo
