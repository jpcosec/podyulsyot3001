import { Folder, FileJson, FileText, Image, FileType, File } from 'lucide-react';
import { cn } from '../../../utils/cn';
import type { ExplorerEntry } from '../../../types/api.types';

interface Props {
  entries: ExplorerEntry[];
  activePath: string;
  onSelect: (path: string) => void;
}

function EntryIcon({ entry }: { entry: ExplorerEntry }) {
  if (entry.is_dir) return <Folder size={14} className="text-primary-dim flex-shrink-0" />;
  const ext = entry.extension ?? entry.name.split('.').pop() ?? '';
  if (ext === 'json') return <FileJson size={14} className="text-primary flex-shrink-0" />;
  if (ext === 'md') return <FileText size={14} className="text-primary-dim flex-shrink-0" />;
  if (ext === 'png' || ext === 'jpg' || ext === 'jpeg') return <Image size={14} className="text-on-muted flex-shrink-0" />;
  if (ext === 'pdf') return <FileType size={14} className="text-error flex-shrink-0" />;
  return <File size={14} className="text-on-muted flex-shrink-0" />;
}

export function ExplorerTree({ entries, activePath, onSelect }: Props) {
  if (entries.length === 0) {
    return (
      <div className="p-4">
        <p className="font-mono text-[10px] text-on-muted uppercase">DIRECTORY_EMPTY</p>
      </div>
    );
  }

  return (
    <div className="py-1">
      {entries.map(entry => (
        <button
          key={entry.path}
          onClick={() => onSelect(entry.path)}
          className={cn(
            'w-full flex items-center gap-2 px-3 py-1.5 text-left hover:bg-primary/5 transition-colors',
            activePath === entry.path
              ? 'bg-primary/10 text-primary border-r-2 border-primary'
              : 'text-on-surface'
          )}
        >
          <EntryIcon entry={entry} />
          <span className="font-mono text-xs truncate">{entry.name}</span>
          {entry.is_dir && entry.child_count !== undefined && (
            <span className="font-mono text-[10px] text-on-muted ml-auto">{entry.child_count}</span>
          )}
        </button>
      ))}
    </div>
  );
}
