import { cn } from '../../utils/cn';

const SIZES = {
  xs: 'w-3 h-3 border',
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
};

interface Props {
  size?: keyof typeof SIZES;
  className?: string;
}

export function Spinner({ size = 'sm', className }: Props) {
  return (
    <span
      className={cn(
        'inline-block border-primary border-t-transparent rounded-full animate-spin',
        SIZES[size],
        className,
      )}
    />
  );
}
