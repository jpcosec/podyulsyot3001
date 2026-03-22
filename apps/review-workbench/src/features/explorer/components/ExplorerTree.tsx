import { useState } from 'react';
import { Folder, FolderOpen, FileJson, FileText, Image, FileType, File, ChevronRight, ChevronDown } from 'lucide-react';
import { cn } from '../../../utils/cn';
import type { ExplorerEntry } from '../../../types/api.types';

interface Props {
  entries: ExplorerEntry[];
  activePath: string;
  onSelect: (path: string) => void;
  onLoadChildren?: (path: string) => void;
  childrenMap?: Record<string, ExplorerEntry[]>;
  indent?: number;
}

function FileIcon({ entry, expanded }: { entry: ExplorerEntry; expanded?: boolean }) {
  if (entry.is_dir) {
    return expanded
      ? <FolderOpen size={14} className="text-primary flex-shrink-0" />
      : <Folder size={14} className="text-primary-dim flex-shrink-0" />;
  }
  const ext = entry.extension ?? entry.name.split('.').pop() ?? '';
  if (ext === 'json') return <FileJson size={14} className="text-primary flex-shrink-0" />;
  if (ext === 'md') return <FileText size={14} className="text-primary-dim flex-shrink-0" />;
  if (ext === 'png' || ext === 'jpg' || ext === 'jpeg') return <Image size={14} className="text-on-muted flex-shrink-0" />;
  if (ext === 'pdf') return <FileType size={14} className="text-error flex-shrink-0" />;
  return <File size={14} className="text-on-muted flex-shrink-0" />;
}

export function ExplorerTree({ entries, activePath, onSelect, onLoadChildren, childrenMap = {}, indent = 0 }: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggleFolder = (path: string) => {
    const isExpanding = !expanded.has(path);
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
    if (isExpanding) onLoadChildren?.(path);
  };

  if (entries.length === 0) {
    return (
      <div className="p-4">
        <p className="font-mono text-[10px] text-on-muted uppercase">DIRECTORY_EMPTY</p>
      </div>
    );
  }

  return (
    <div className="py-1">
      {entries.map(entry => {
        const isExpanded = expanded.has(entry.path);
        const children = childrenMap[entry.path];

        return (
          <div key={entry.path}>
            <button
              onClick={() => {
                if (entry.is_dir) {
                  toggleFolder(entry.path);
                } else {
                  onSelect(entry.path);
                }
              }}
              className={cn(
                'w-full flex items-center gap-1.5 py-1.5 text-left hover:bg-primary/5 transition-colors',
                activePath === entry.path
                  ? 'bg-primary/10 text-primary border-r-2 border-primary'
                  : 'text-on-surface'
              )}
              style={{ paddingLeft: `${12 + indent * 16}px` }}
            >
              {entry.is_dir ? (
                <span className="text-on-muted/60">
                  {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                </span>
              ) : (
                <span className="w-3" />
              )}
              <FileIcon entry={entry} expanded={isExpanded} />
              <span className="font-mono text-xs truncate">{entry.name}</span>
              {entry.is_dir && !isExpanded && entry.child_count !== undefined && (
                <span className="font-mono text-[10px] text-on-muted ml-auto pr-3">{entry.child_count}</span>
              )}
            </button>

            {entry.is_dir && isExpanded && children && children.length > 0 && (
              <ExplorerTree
                entries={children}
                activePath={activePath}
                onSelect={onSelect}
                onLoadChildren={onLoadChildren}
                childrenMap={childrenMap}
                indent={indent + 1}
              />
            )}
            {entry.is_dir && isExpanded && children && children.length === 0 && (
              <div style={{ paddingLeft: `${28 + (indent + 1) * 16}px` }} className="py-1">
                <span className="font-mono text-[9px] text-on-muted/40 uppercase">empty</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
