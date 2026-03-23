import { FileTree, type FileTreeNode } from '../../../components/organisms/FileTree';
import type { ExplorerEntry } from '../../../types/api.types';

interface Props {
  entries: ExplorerEntry[];
  activePath: string;
  onSelect: (path: string) => void;
  onLoadChildren?: (path: string) => void;
  childrenMap?: Record<string, ExplorerEntry[]>;
  indent?: number;
}

function toFileNodes(entries: ExplorerEntry[]): FileTreeNode[] {
  return entries.map(e => ({
    name: e.name,
    path: e.path,
    is_dir: e.is_dir,
    extension: e.extension,
    child_count: e.child_count,
  }));
}

export function ExplorerTree({ entries, activePath, onSelect, onLoadChildren, childrenMap = {}, indent = 0 }: Props) {
  const fileNodes = toFileNodes(entries);

  const fileChildrenMap: Record<string, FileTreeNode[]> = {};
  for (const [key, val] of Object.entries(childrenMap)) {
    fileChildrenMap[key] = toFileNodes(val);
  }

  return (
    <FileTree
      nodes={fileNodes}
      currentPath={activePath}
      onNavigate={path => onLoadChildren?.(path)}
      onFileSelect={onSelect}
      childrenMap={fileChildrenMap}
      indent={indent}
    />
  );
}
