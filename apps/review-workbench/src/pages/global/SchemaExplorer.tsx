import { useMemo, useState } from 'react';
import { cn } from '../../utils/cn';
import { KnowledgeGraph } from './KnowledgeGraph';
import { schemaToGraph } from '../../features/schema-explorer/lib/schemaToGraph';
import { useSchema, type SchemaDomain } from '../../features/schema-explorer/lib/useSchema';

const DOMAINS: { id: SchemaDomain; label: string }[] = [
  { id: 'cv',    label: 'CV' },
  { id: 'job',   label: 'Job' },
  { id: 'match', label: 'Match' },
];

export function SchemaExplorer() {
  const [domain, setDomain] = useState<SchemaDomain>('cv');
  const schema = useSchema(domain);
  const isStub = schema.node_types.length === 0;
  const { nodes, edges } = useMemo(() => schemaToGraph(schema), [schema]);

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <header className="flex items-center gap-3 px-6 py-3 border-b border-outline/10 bg-surface">
        <span className="text-on-muted font-mono text-[10px] uppercase tracking-widest mr-2">Schema</span>
        {DOMAINS.map(d => (
          <button
            key={d.id}
            onClick={() => setDomain(d.id)}
            className={cn(
              'px-3 py-1 font-mono text-[11px] uppercase tracking-widest border transition-colors',
              domain === d.id
                ? 'border-primary text-primary bg-primary/10'
                : 'border-outline/20 text-on-muted hover:border-primary/50 hover:text-on-surface bg-transparent',
            )}
          >
            {d.label}
          </button>
        ))}

        <div className="flex items-center gap-3 ml-auto">
          {Object.entries(schema.visual_encoding.color_tokens).map(([token, colors]) => (
            <span key={token} className="flex items-center gap-1">
              <span
                className="inline-block w-2.5 h-2.5 rounded-sm border"
                style={{ borderColor: colors.border, backgroundColor: colors.bg }}
              />
              <span className="font-mono text-[9px] text-on-muted uppercase tracking-widest">
                {token}
              </span>
            </span>
          ))}
        </div>

        <span className="text-on-muted font-mono text-[10px] ml-4">
          {schema.document.label} · v{schema.document.version}
        </span>
      </header>

      {isStub ? (
        <div className="flex-1 flex items-center justify-center text-on-muted font-mono text-sm">
          Schema not yet defined for <span className="text-primary mx-1 uppercase">{domain}</span>
        </div>
      ) : (
        <div className="flex-1">
          <KnowledgeGraph initialNodes={nodes} initialEdges={edges} readOnly />
        </div>
      )}
    </div>
  );
}
