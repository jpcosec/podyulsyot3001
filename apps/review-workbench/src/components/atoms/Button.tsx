import { cn } from '../../utils/cn';
import { Spinner } from './Spinner';

const VARIANTS = {
  primary: 'bg-primary text-black font-headline font-bold uppercase tracking-widest hover:brightness-110 tactical-glow',
  ghost:   'bg-transparent text-on-muted border border-outline/30 font-headline uppercase tracking-widest hover:text-on-surface hover:border-outline/60',
  danger:  'bg-error/15 text-error border border-error/30 font-headline uppercase tracking-widest hover:bg-error/25',
};

const SIZES = {
  sm: 'px-3 py-1 text-[10px]',
  md: 'px-4 py-2 text-xs',
};

interface Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof VARIANTS;
  size?: keyof typeof SIZES;
  loading?: boolean;
}

export function Button({ variant = 'primary', size = 'md', loading, disabled, className, children, ...props }: Props) {
  return (
    <button
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center gap-2 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...props}
    >
      {loading && <Spinner size="xs" />}
      {children}
    </button>
  );
}
