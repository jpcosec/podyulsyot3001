import { useState } from 'react';
import { cn } from '../../../utils/cn';
import type { SimpleNode } from '../../../pages/global/KnowledgeGraph';

interface Props {
  unmappedNodes: SimpleNode[];
  onSelectNode: (nodeId: string) => void;
}

export function UnmappedSkillsPanel({ unmappedNodes, onSelectNode }: Props) {
  const [collapsed, setCollapsed] = useState(false);

  if (collapsed) {
    return (
      <div
        className="w-8 shrink-0 border-l border-outline/20 bg-surface flex flex-col items-center pt-3 cursor-pointer hover:bg-surface-low transition-colors"
        onClick={() => setCollapsed(false)}
      >
        <span className="font-mono text-[9px] text-on-muted [writing-mode:vertical-rl] mt-4 whitespace-nowrap">
          UNMAPPED ({unmappedNodes.length})
        </span>
      </div>
    );
  }

  return (
    <aside className="w-56 shrink-0 border-l border-outline/20 bg-surface flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-outline/20 bg-surface-low">
        <span className="font-mono text-[9px] text-on-muted uppercase tracking-widest">
          Unmapped ({unmappedNodes.length})
        </span>
        <button
          onClick={() => setCollapsed(true)}
          className="font-mono text-[10px] text-on-muted/60 hover:text-on-muted transition-colors"
          aria-label="Collapse unmapped panel"
        >
          ›
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-1">
        {unmappedNodes.length === 0 ? (
          <p className="font-mono text-[10px] text-on-muted/60 p-2 text-center">
            All skills mapped
          </p>
        ) : (
          unmappedNodes.map(node => (
            <button
              key={node.id}
              onClick={() => onSelectNode(node.id)}
              className={cn(
                'text-left px-2 py-1.5 border border-outline/20',
                'font-mono text-[11px] text-on-surface',
                'hover:border-primary/40 hover:bg-primary/5 transition-colors',
              )}
            >
              <span className="block truncate">{node.data.name}</span>
              {node.data.properties['score'] && (
                <span className="text-on-muted/60 text-[10px]">
                  {node.data.properties['score']}
                </span>
              )}
            </button>
          ))
        )}
      </div>
    </aside>
  );
}
