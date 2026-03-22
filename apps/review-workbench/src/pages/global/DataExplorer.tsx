import { useSearchParams } from 'react-router-dom';
import { SplitPane } from '../../components/molecules/SplitPane';
import { BreadcrumbNav } from '../../features/explorer/components/BreadcrumbNav';
import { ExplorerTree } from '../../features/explorer/components/ExplorerTree';
import { FilePreview } from '../../features/explorer/components/FilePreview';
import { useExplorerBrowse } from '../../features/explorer/api/useExplorerBrowse';

export function DataExplorer() {
  const [searchParams, setSearchParams] = useSearchParams();
  const activePath = searchParams.get('path') ?? '';

  // Always browse the parent directory for the tree
  const parentPath = activePath.includes('/')
    ? activePath.split('/').slice(0, -1).join('/')
    : '';
  const treeQuery = useExplorerBrowse(parentPath);
  const previewQuery = useExplorerBrowse(activePath);

  const handleNavigate = (path: string) => {
    setSearchParams(path ? { path } : {});
  };

  const treeEntries = treeQuery.data?.entries ?? [];

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-outline/20 px-4 py-2">
        <p className="font-mono text-[10px] text-primary uppercase tracking-widest">Explorer</p>
        <h1 className="font-headline text-lg font-bold text-on-surface">Data Explorer</h1>
      </div>
      <div className="flex-1 min-h-0">
        <SplitPane orientation="horizontal" defaultSizes={[30, 70]}>
          {/* Left: Tree */}
          <div className="flex flex-col h-full bg-surface-container-low border-r border-outline/20 overflow-hidden">
            <BreadcrumbNav path={activePath} onNavigate={handleNavigate} />
            <div className="flex-1 overflow-auto">
              <ExplorerTree
                entries={treeEntries}
                activePath={activePath}
                onSelect={handleNavigate}
              />
            </div>
          </div>
          {/* Right: Preview */}
          <div className="flex flex-col h-full overflow-hidden">
            <div className="bg-surface-high px-4 py-2 font-mono text-[10px] text-on-muted uppercase border-b border-outline/20">
              {activePath || 'ROOT'}
            </div>
            <div className="flex-1 overflow-auto bg-surface">
              <FilePreview
                data={previewQuery.data}
                isLoading={activePath ? previewQuery.isLoading : treeQuery.isLoading}
                isError={activePath ? previewQuery.isError : treeQuery.isError}
                activePath={activePath}
                onNavigate={handleNavigate}
              />
            </div>
          </div>
        </SplitPane>
      </div>
    </div>
  );
}
