import { useState } from 'react';
import type { ArtifactFile } from '../../../types/api.types';
import { Button } from '../../../components/atoms/Button';

interface Props {
  files: ArtifactFile[];
}

export function SourceTextPreview({ files }: Props) {
  const [expanded, setExpanded] = useState(false);
  const sourceFile = files.find(f => f.path.includes('source_text'));
  const content = sourceFile?.content ?? '';
  const lines = content.split('\n');
  const visibleLines = expanded ? lines : lines.slice(0, 20);
  const hasMore = lines.length > 20;

  return (
    <div className="bg-surface-container-low border border-outline/20 p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]">
          Source Text Preview
        </p>
        {hasMore && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="font-mono text-[10px] text-primary hover:text-primary-dim uppercase tracking-widest"
          >
            {expanded ? '[ COLLAPSE ]' : '[ EXPAND ]'}
          </button>
        )}
      </div>
      <pre className="font-mono text-xs text-on-surface bg-surface-low border border-outline/20 p-3 overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto">
        {visibleLines.join('\n')}
        {!expanded && hasMore && (
          <span className="text-on-muted"> …{lines.length - 20} more lines</span>
        )}
      </pre>
    </div>
  );
}
