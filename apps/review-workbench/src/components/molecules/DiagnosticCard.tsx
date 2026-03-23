import { cn } from '../../utils/cn';

interface Props {
  title: string;
  children: React.ReactNode;
  className?: string;
  headerAction?: React.ReactNode;
}

export function DiagnosticCard({ title, children, className, headerAction }: Props) {
  return (
    <div className={cn('bg-surface-container-low border border-outline/20', className)}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-outline/20">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]">
          {title}
        </p>
        {headerAction}
      </div>
      <div className="p-4">
        {children}
      </div>
    </div>
  );
}
