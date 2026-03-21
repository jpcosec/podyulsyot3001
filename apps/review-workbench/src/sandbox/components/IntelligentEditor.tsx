import { useState, useRef } from 'react';

interface PinnedNode {
  id: string;
  title: string;
  category: 'skill' | 'req';
  yPos: number;
}

export function IntelligentEditor({ text }: { text: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredTagId, setHoveredTagId] = useState<string | null>(null);
  const [pinnedNodes, setPinnedNodes] = useState<PinnedNode[]>([]);

  return (
    <div
      ref={containerRef}
      className="relative flex w-full h-[600px] bg-surface-container panel-border rounded-none"
    >
      {/* 1. ZONA DEL EDITOR DE TEXTO (Izquierda) */}
      <div className="flex-1 p-6 overflow-y-auto font-mono text-sm leading-relaxed relative">
        <p>
          El candidato demuestra experiencia sólida en{' '}
          <span
            className="bg-primary/15 border-l-2 border-primary px-1 cursor-pointer transition-colors hover:bg-primary/30"
            onMouseEnter={() => setHoveredTagId('SKL-1')}
            onMouseLeave={() => setHoveredTagId(null)}
            onClick={() =>
              setPinnedNodes((prev) =>
                prev.find((n) => n.id === 'SKL-1')
                  ? prev
                  : [...prev, { id: 'SKL-1', title: 'Python', category: 'skill', yPos: 100 }],
              )
            }
          >
            Python
          </span>
          {' '}y desarrollo backend.
        </p>

        <p className="mt-4">
          Su trayectoria en{' '}
          <span
            className="bg-secondary/15 border-l-2 border-secondary px-1 cursor-pointer transition-colors hover:bg-secondary/30"
            onMouseEnter={() => setHoveredTagId('REQ-2')}
            onMouseLeave={() => setHoveredTagId(null)}
            onClick={() =>
              setPinnedNodes((prev) =>
                prev.find((n) => n.id === 'REQ-2')
                  ? prev
                  : [
                      ...prev,
                      {
                        id: 'REQ-2',
                        title: 'Distributed Systems',
                        category: 'req',
                        yPos: 200,
                      },
                    ],
              )
            }
          >
            sistemas distribuidos
          </span>
          {' '}es relevante para el puesto.
        </p>

        {/* Hover Card Flotante */}
        {hoveredTagId && (
          <div className="absolute top-10 left-40 bg-surface-high panel-border p-2 shadow-lg z-floating-card">
            <div className="text-[10px] text-primary font-mono">ID: {hoveredTagId}</div>
            <div className="font-headline text-sm font-bold">
              {hoveredTagId === 'SKL-1' ? 'Python' : 'Distributed Systems'}
            </div>
            <div className="text-[10px] text-on-muted uppercase tracking-widest mt-1">
              {hoveredTagId === 'SKL-1' ? 'skill' : 'requirement'}
            </div>
            <div className="text-xs text-on-muted cursor-grab mt-2">Click to pin →</div>
          </div>
        )}

        {/* Preview del texto completo */}
        {text && (
          <div className="mt-6 text-xs text-on-muted border-t border-outline/20 pt-4">
            <span className="font-mono text-[9px] uppercase tracking-widest text-primary/60">
              raw text
            </span>
            <p className="mt-1 whitespace-pre-wrap">{text}</p>
          </div>
        )}
      </div>

      {/* 2. CAPA SVG PARA LÍNEAS */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-svg-lines">
        {pinnedNodes.map((node) => (
          <path
            key={node.id}
            d={`M 280 ${node.yPos - 40} C 400 ${node.yPos - 40}, 400 ${node.yPos}, 600 ${node.yPos}`}
            fill="none"
            stroke={node.category === 'skill' ? '#00f2ff' : '#ffaa00'}
            strokeWidth="1.5"
            strokeDasharray="4 4"
            className="opacity-50"
          />
        ))}
      </svg>

      {/* 3. MARGEN DERECHO — Tarjetas Pineadas */}
      <div className="w-64 bg-background border-l panel-border p-4 flex flex-col gap-2 overflow-y-auto z-editor-overlay">
        <div className="font-mono text-[10px] text-on-muted uppercase tracking-widest mb-4">
          Pinned Context
        </div>

        {pinnedNodes.length === 0 && (
          <p className="text-[11px] text-on-muted/60 italic">
            Click a tag in the editor to pin it here.
          </p>
        )}

        {pinnedNodes.map((node) => (
          <div
            key={node.id}
            className={`bg-surface-high p-2 cursor-pointer hover:brightness-125 transition-all ${
              node.category === 'skill'
                ? 'border border-primary/20 tactical-glow'
                : 'border border-secondary/20 alert-glow'
            }`}
          >
            <div className="flex justify-between items-start">
              <span
                className={`text-[9px] font-mono ${
                  node.category === 'skill' ? 'text-primary' : 'text-secondary'
                }`}
              >
                [{node.id}]
              </span>
              <button
                onClick={() => setPinnedNodes((prev) => prev.filter((n) => n.id !== node.id))}
                className="text-on-muted hover:text-error text-sm leading-none"
              >
                ×
              </button>
            </div>
            <div className="text-sm mt-1 text-on-surface">{node.title}</div>
            <div className="text-[9px] text-on-muted uppercase tracking-widest mt-1">
              {node.category}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
