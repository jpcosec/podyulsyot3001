import { cn } from '../../utils/cn';

const CATEGORIES = {
  skill: 'border-l-primary text-primary bg-primary/5',
  req: 'border-l-secondary text-secondary bg-secondary/5',
  risk: 'border-l-error text-error bg-error/5',
};

interface Props {
  category?: keyof typeof CATEGORIES;
  className?: string;
  children: React.ReactNode;
  onClick?: () => void;
}

export function Tag({ category = 'req', className, children, onClick }: Props) {
  return (
    <span
      onClick={onClick}
      className={cn(
        'inline-flex items-center px-2 py-0.5 font-mono text-[9px] uppercase tracking-widest border-l-2',
        CATEGORIES[category],
        onClick && 'cursor-pointer hover:opacity-80',
        className,
      )}
    >
      {children}
    </span>
  );
}
