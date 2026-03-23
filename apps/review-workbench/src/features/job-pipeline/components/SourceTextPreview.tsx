import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ArtifactFile } from '../../../types/api.types';

interface Props {
  files: ArtifactFile[];
}

export function SourceTextPreview({ files }: Props) {
  const [expanded, setExpanded] = useState(false);
  const sourceFile = files.find(f => f.path.includes('source_text'));
  const content = sourceFile?.content ?? '';
  const lines = content.split('\n');
  const hasMore = lines.length > 15;

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
      <div className={`bg-surface-low border border-outline/20 p-3 overflow-auto ${!expanded ? 'max-h-96' : ''}`}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {expanded ? content : lines.slice(0, 15).join('\n')}
        </ReactMarkdown>
      </div>
    </div>
  );
}
