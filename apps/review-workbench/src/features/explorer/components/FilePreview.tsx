import { Spinner } from '../../../components/atoms/Spinner';
import { AlertTriangle } from 'lucide-react';
import { JsonPreview } from './JsonPreview';
import { MarkdownPreview } from './MarkdownPreview';
import { ImagePreview } from './ImagePreview';
import type { ExplorerPayload } from '../../../types/api.types';

interface Props {
  data: ExplorerPayload | undefined;
  isLoading: boolean;
  isError: boolean;
  activePath: string;
  onNavigate: (path: string) => void;
}

export function FilePreview({ data, isLoading, isError, activePath, onNavigate }: Props) {
  if (!activePath) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="font-mono text-[10px] text-on-muted uppercase">SELECT_A_FILE_OR_FOLDER</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner size="md" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex items-center justify-center h-full gap-2">
        <AlertTriangle size={16} className="text-error" />
        <p className="font-mono text-xs text-error uppercase">{activePath} NOT_FOUND</p>
      </div>
    );
  }

  if (data.is_dir) {
    const entries = data.entries ?? [];
    if (entries.length === 0) {
      return (
        <div className="flex items-center justify-center h-full">
          <p className="font-mono text-[10px] text-on-muted uppercase">DIRECTORY_EMPTY</p>
        </div>
      );
    }
    return (
      <div className="p-4 grid grid-cols-3 gap-2">
        {entries.map(entry => (
          <button
            key={entry.path}
            onClick={() => onNavigate(entry.path)}
            className="bg-surface-container border border-outline/20 p-3 text-left hover:border-primary/30 transition-colors"
          >
            <p className="font-mono text-xs text-on-surface truncate">{entry.name}</p>
            <p className="font-mono text-[10px] text-on-muted mt-1">
              {entry.is_dir ? 'DIR' : entry.extension?.toUpperCase() ?? 'FILE'}
            </p>
          </button>
        ))}
      </div>
    );
  }

  // File content
  const contentType = data.content_type;
  if (contentType === 'too_large') {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="font-mono text-[10px] text-on-muted uppercase">FILE_EXCEEDS_LIMIT</p>
      </div>
    );
  }
  if (contentType === 'binary') {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="font-mono text-[10px] text-on-muted uppercase">BINARY_CONTENT: NO_PREVIEW</p>
      </div>
    );
  }
  if (contentType === 'image') {
    return <ImagePreview path={data.path} content={data.content ?? null} />;
  }

  const ext = activePath.split('.').pop() ?? '';
  const content = data.content ?? '';
  if (ext === 'json') return <JsonPreview content={content} />;
  if (ext === 'md') return <MarkdownPreview content={content} />;
  if (ext === 'txt' || ext === 'log' || ext === 'yaml' || ext === 'yml' || ext === 'toml') {
    return (
      <pre className="p-4 font-mono text-xs text-on-surface whitespace-pre-wrap overflow-auto">
        {content}
      </pre>
    );
  }
  return (
    <div className="flex flex-col items-center justify-center h-full gap-2">
      <p className="font-mono text-xs text-on-muted uppercase">Preview not available</p>
      <p className="font-mono text-[10px] text-on-muted/60">.{ext} files cannot be previewed</p>
    </div>
  );
}
