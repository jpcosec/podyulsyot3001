import { cn } from '../../utils/cn';

interface Props {
  keys: string[];
  className?: string;
}

export function Kbd({ keys, className }: Props) {
  return (
    <span className={cn('inline-flex items-center gap-0.5', className)}>
      {keys.map((key, i) => (
        <kbd
          key={i}
          className="font-mono text-[9px] px-1 py-0.5 bg-surface border border-outline/40 text-on-muted uppercase"
        >
          {key}
        </kbd>
      ))}
    </span>
  );
}
