import { useState } from 'react';
import { Folder, FolderOpen, FileJson, FileText, Image, FileType, File, ChevronRight, ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface FileTreeNode {
  name: string;
  path: string;
  is_dir: boolean;
  extension?: string;
  child_count?: number;
}

interface NodeProps {
  node: FileTreeNode;
  currentPath: string;
  onNavigate: (path: string) => void;
  onFileSelect: (path: string) => void;
  childrenMap?: Record<string, FileTreeNode[]>;
  indent?: number;
}

interface Props {
  nodes: FileTreeNode[];
  currentPath: string;
  onNavigate: (path: string) => void;
  onFileSelect: (path: string) => void;
  childrenMap?: Record<string, FileTreeNode[]>;
  indent?: number;
  className?: string;
}

function FileIcon({ node, expanded }: { node: FileTreeNode; expanded?: boolean }) {
  if (node.is_dir) {
    return expanded
      ? <FolderOpen size={14} className="text-primary flex-shrink-0" />
      : <Folder size={14} className="text-primary-dim flex-shrink-0" />;
  }
  const ext = node.extension ?? node.name.split('.').pop() ?? '';
  if (ext === 'json') return <FileJson size={14} className="text-primary flex-shrink-0" />;
  if (ext === 'md') return <FileText size={14} className="text-primary-dim flex-shrink-0" />;
  if (ext === 'png' || ext === 'jpg' || ext === 'jpeg') return <Image size={14} className="text-on-muted flex-shrink-0" />;
  if (ext === 'pdf') return <FileType size={14} className="text-error flex-shrink-0" />;
  return <File size={14} className="text-on-muted flex-shrink-0" />;
}

function FileTreeNode({ node, currentPath, onNavigate, onFileSelect, childrenMap, indent = 0 }: NodeProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggleFolder = (path: string) => {
    const isExpanding = !expanded.has(path);
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
    if (isExpanding) onNavigate(path);
  };

  const isExpanded = expanded.has(node.path);
  const children = childrenMap?.[node.path];

  return (
    <div>
      <button
        onClick={() => {
          if (node.is_dir) {
            toggleFolder(node.path);
          } else {
            onFileSelect(node.path);
          }
        }}
        className={cn(
          'w-full flex items-center gap-1.5 py-1.5 text-left hover:bg-primary/5 transition-colors',
          currentPath === node.path
            ? 'bg-primary/10 text-primary border-r-2 border-primary'
            : 'text-on-surface'
        )}
        style={{ paddingLeft: `${12 + indent * 16}px` }}
      >
        {node.is_dir ? (
          <span className="text-on-muted/60">
            {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          </span>
        ) : (
          <span className="w-3" />
        )}
        <FileIcon node={node} expanded={isExpanded} />
        <span className="font-mono text-xs truncate">{node.name}</span>
        {node.is_dir && !isExpanded && node.child_count !== undefined && (
          <span className="font-mono text-[10px] text-on-muted ml-auto pr-3">{node.child_count}</span>
        )}
      </button>

      {node.is_dir && isExpanded && children && children.length > 0 && (
        <FileTree
          nodes={children}
          currentPath={currentPath}
          onNavigate={onNavigate}
          onFileSelect={onFileSelect}
          childrenMap={childrenMap}
          indent={indent + 1}
        />
      )}
      {node.is_dir && isExpanded && children && children.length === 0 && (
        <div style={{ paddingLeft: `${28 + (indent + 1) * 16}px` }} className="py-1">
          <span className="font-mono text-[9px] text-on-muted/40 uppercase">empty</span>
        </div>
      )}
    </div>
  );
}

export function FileTree({
  nodes,
  currentPath,
  onNavigate,
  onFileSelect,
  childrenMap = {},
  indent = 0,
  className,
}: Props) {
  if (nodes.length === 0) {
    return (
      <div className="p-4">
        <p className="font-mono text-[10px] text-on-muted uppercase">DIRECTORY_EMPTY</p>
      </div>
    );
  }

  return (
    <div className={cn('py-1', className)}>
      {nodes.map(node => (
        <FileTreeNode
          key={node.path}
          node={node}
          currentPath={currentPath}
          onNavigate={onNavigate}
          onFileSelect={onFileSelect}
          childrenMap={childrenMap}
          indent={indent}
        />
      ))}
    </div>
  );
}
