# Spec: Data Explorer (Raw Views)

## 1. Objetivo del Operador
Navegar el filesystem de `data/jobs/` para inspeccionar artefactos crudos en cualquier etapa — JSONs aprobados, propuestos, trazas de error, screenshots. No es una vista de edición; es diagnóstico y auditoría.

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v1/explorer/browse?path=<path>` → `ExplorerPayload`
  ```ts
  {
    path: string,
    is_dir: boolean,
    entries?: ExplorerEntry[],     // si es directorio
    content_type?: "text" | "image" | "binary" | "too_large",
    content?: string | null        // si es archivo de texto
  }
  ```

**Escritura:** Ninguna.

---

## 3. Composición de la UI y Layout

**Layout Base:** SplitScreen 30/70 — panel izquierdo (árbol de navegación) + panel derecho (preview).

```
┌── col-left (30%) ─────┬── col-right (70%) ──────────────────┐
│ Path breadcrumb       │ [header: ruta actual + tipo]        │
│                       │                                     │
│ ► tu_berlin/          │  Si directorio:                     │
│   ► 201397/           │    grid de carpetas/archivos        │
│     ► nodes/          │    con iconos por tipo              │
│       ► match/        │                                     │
│         approved/ ←   │  Si archivo texto/JSON:             │
│                       │    pre formateado con sintaxis      │
│                       │    highlighting mono                │
│                       │                                     │
│                       │  Si imagen:                         │
│                       │    img centrada con metadata        │
└───────────────────────┴─────────────────────────────────────┘
```

**Componentes Core:**
- `<ExplorerTree>` — árbol colapsable con íconos por tipo (folder/json/md/image)
- `<BreadcrumbNav>` — path segmentado, cada segmento clickeable
- `<FilePreview>` — dispatcher: `<JsonPreview>` / `<MarkdownPreview>` / `<ImagePreview>` / `<BinaryStub>`
- `<JsonPreview>` — JSON pretty-printed en `font-mono text-xs`, coloreado por tipo de valor

**Componentes a Reciclar/Limpiar:**
- `DataExplorerPage.tsx` existente — mantener lógica, rediseñar layout y estilos

**Íconos por extensión:**
```
.json     → settings_ethernet  (cyan)
.md       → article            (cyan dim)
.png/.jpg → image              (outline)
.pdf      → description        (error/salmon)
.sqlite   → storage            (outline)
carpeta   → folder_special     (cyan dim)
```

---

## 4. Estilos y Unificación (Terran Command Theme)

**Paleta:**
- Panel izquierdo árbol: `bg-surface-container-low border-r border-outline-variant/20`
- Ítem activo en árbol: `bg-primary/10 text-primary border-r-2 border-primary`
- Panel derecho: `bg-surface`
- Header del preview: `bg-surface-container-high px-4 py-2 font-mono text-[10px] text-outline uppercase`
- JSON values: string=primary, number=secondary, boolean=error, null=outline

**Tipografía:**
- Nombres de archivo en árbol: `font-mono text-[11px]`
- Path breadcrumb: `font-mono text-xs text-outline` → segmento activo: `text-on-surface`
- Contenido JSON/text: `font-mono text-xs leading-relaxed`

**Interacciones Clave:**
- Click en carpeta → expande árbol + navega al path en panel derecho
- Click en archivo → carga preview en panel derecho
- Breadcrumb click → sube niveles
- `Esc` → colapsa preview, vuelve al directorio padre

**Estado Vacío:**
- Carpeta vacía: icono `folder_open` + "DIRECTORY_EMPTY" en mono
- Archivo binary: icono `block` + "BINARY_CONTENT: NO_PREVIEW_AVAILABLE"
- Archivo too_large: icono `warning` + "FILE_EXCEEDS_PREVIEW_LIMIT"

**Estado Error:**
- Path no encontrado: icono `error_outline` + path en rojo
