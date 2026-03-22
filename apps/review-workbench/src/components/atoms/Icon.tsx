import { type LucideProps, type LucideIcon } from 'lucide-react';
import { cn } from '../../utils/cn';

const SIZES: Record<'xs' | 'sm' | 'md', number> = { xs: 12, sm: 16, md: 20 };

interface Props extends Omit<LucideProps, 'size'> {
  icon: LucideIcon;
  size?: keyof typeof SIZES;
}

export function Icon({ icon: IconComponent, size = 'sm', className, ...props }: Props) {
  return <IconComponent size={SIZES[size]} className={cn('shrink-0', className)} {...props} />;
}
