# FUTURE-002: Graph Export (JSON, PNG, SVG)

**Status:** Deferred  
**Priority:** High  
**Estimated Effort:** 2-3 days

---

## Problem

Users need to export graphs for:
- Sharing in presentations (PNG/SVG)
- Backup/backup (JSON)
- Import into other tools

---

## Proposed Solution

### Export Formats

```ts
type ExportFormat = 'json' | 'png' | 'svg' | 'pdf';

interface ExportOptions {
  format: ExportFormat;
  includeMetadata?: boolean;
  scale?: number; // for raster
  background?: string;
}
```

### JSON Export
```ts
function exportToJSON(nodes: ASTNode[], edges: ASTEdge[]): string {
  return JSON.stringify({ nodes, edges, version: '2.0' }, null, 2);
}
```

### PNG/SVG Export
Use ReactFlow's `getNodesBounds` + `toPng`/`toSvg` from `html-to-image`:

```ts
async function exportToImage(format: 'png' | 'svg') {
  const viewport = document.querySelector('.react-flow__viewport');
  if (!viewport) return;
  
  const bounds = getNodesBounds(nodes);
  const toImage = format === 'png' ? toPng : toSvg;
  
  const dataUrl = await toImage(viewport, {
    width: bounds.width,
    height: bounds.height,
    style: { transform: 'translate(0, 0)' },
  });
  
  download(dataUrl, `graph.${format}`);
}
```

### UI Integration

Add to Sidebar → View section:

```tsx
<DropdownMenu>
  <DropdownMenuTrigger>Export</DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuItem onClick={() => handleExport('json')}>
      JSON
    </DropdownMenuItem>
    <DropdownMenuItem onClick={() => handleExport('png')}>
      PNG Image
    </DropdownMenuItem>
    <DropdownMenuItem onClick={() => handleExport('svg')}>
      SVG Vector
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

---

## Dependencies

- `html-to-image` package
- ReactFlow bounds calculation

---

## Risks

- Large graphs may fail to render in canvas-to-image
- Cross-origin issues with external images

---

## Acceptance Criteria

| Format | Test |
|--------|------|
| JSON | Round-trip: export → import produces identical graph |
| PNG | 100 nodes renders correctly |
| SVG | Vectors scale without blur |

---

## References

- html-to-image: https://github.com/bubkoo/html-to-image
- ReactFlow export: https://reactflow.dev/examples/utilities/export
