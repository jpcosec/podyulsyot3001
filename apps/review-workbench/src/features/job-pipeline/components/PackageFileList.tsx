import { FileType, FileText } from 'lucide-react';
import type { PackageFile } from '../../../types/api.types';
import { cn } from '../../../utils/cn';

interface Props {
  files: PackageFile[];
}

function FileIcon({ name }: { name: string }) {
  if (name.endsWith('.pdf')) return <FileType size={16} className="text-error" />;
  return <FileText size={16} className="text-primary" />;
}

export function PackageFileList({ files }: Props) {
  return (
    <div className="bg-surface-low panel-border p-6">
      <div className="flex items-center justify-between mb-4">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]">Package Files</p>
        <button
          className="font-mono text-[10px] text-on-muted border border-outline/30 px-3 py-1 cursor-not-allowed opacity-50"
          disabled
          title="COMING_SOON"
        >
          DOWNLOAD ALL AS ZIP
        </button>
      </div>
      <div className="space-y-3">
        {files.map(file => (
          <div key={file.path} className="flex items-center gap-3">
            <FileIcon name={file.name} />
            <span className="font-mono text-xs text-on-surface flex-1">{file.name}</span>
            <span className="font-mono text-[10px] text-on-muted">{file.size_kb} KB</span>
            <a
              href={file.path}
              download={file.name}
              className="font-mono text-[10px] text-primary hover:text-primary/80 uppercase tracking-widest border border-primary/30 px-2 py-1 transition-colors"
            >
              DOWNLOAD
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
