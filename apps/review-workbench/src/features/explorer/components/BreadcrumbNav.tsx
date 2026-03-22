import { cn } from '../../../utils/cn';

interface Props {
  path: string;
  onNavigate: (path: string) => void;
}

export function BreadcrumbNav({ path, onNavigate }: Props) {
  const parts = path ? path.split('/').filter(Boolean) : [];

  return (
    <div className="flex items-center gap-1 font-mono text-[10px] uppercase px-3 py-2 border-b border-outline/20">
      <button
        onClick={() => onNavigate('')}
        className={cn('text-primary hover:text-primary-dim', parts.length === 0 && 'text-on-surface')}
      >
        ROOT
      </button>
      {parts.map((part, i) => {
        const partPath = parts.slice(0, i + 1).join('/');
        return (
          <span key={partPath} className="flex items-center gap-1">
            <span className="text-on-muted">/</span>
            <button
              onClick={() => onNavigate(partPath)}
              className={cn(
                'hover:text-primary',
                i === parts.length - 1 ? 'text-on-surface' : 'text-primary/70'
              )}
            >
              {part}
            </button>
          </span>
        );
      })}
    </div>
  );
}
