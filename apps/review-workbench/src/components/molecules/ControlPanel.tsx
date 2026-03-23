import { Button } from '../atoms/Button';
import { Kbd } from '../atoms/Kbd';
import { cn } from '../../utils/cn';

interface StatusField {
  label: string;
  value: string;
  variant?: 'primary' | 'secondary' | 'error' | 'muted';
}

interface InfoField {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
}

interface Action {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'ghost' | 'danger';
  disabled?: boolean;
  loading?: boolean;
}

interface Shortcut {
  keys: string[];
  label: string;
}

interface Props {
  title: string;
  phaseColor?: 'secondary' | 'primary';
  status?: StatusField;
  fields?: InfoField[];
  actions: Action[];
  shortcuts?: Shortcut[];
  children?: React.ReactNode;
  className?: string;
}

export function ControlPanel({
  title,
  phaseColor = 'secondary',
  status,
  fields,
  actions,
  shortcuts,
  children,
  className,
}: Props) {
  const headerColor = phaseColor === 'secondary' ? 'text-secondary border-secondary/20' : 'text-primary border-primary/20';
  const headerBg = phaseColor === 'secondary' ? 'bg-secondary/5' : 'bg-primary/5';

  return (
    <div className={cn('w-80 bg-background border-l flex flex-col', headerColor.split(' ')[1], className)}>
      <div className={cn('px-4 py-3 border-b', headerBg, `border-${phaseColor}/20`)}>
        <p className={cn('font-mono text-[10px] uppercase tracking-[0.2em] mb-0.5', headerColor.split(' ')[0])}>
          Phase
        </p>
        <p className={cn('font-headline font-bold uppercase tracking-widest text-sm', headerColor.split(' ')[0])}>
          {title}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {status && (
          <div>
            <p className="font-mono text-[10px] text-on-muted uppercase tracking-wider mb-1">
              {status.label}
            </p>
            <p className={cn(
              'font-mono text-xs uppercase font-medium',
              status.variant === 'primary' && 'text-primary',
              status.variant === 'secondary' && 'text-secondary',
              status.variant === 'error' && 'text-error',
              status.variant === 'muted' && 'text-on-muted',
            )}>
              {status.value}
            </p>
          </div>
        )}

        {fields && fields.length > 0 && (
          <div className="space-y-2">
            {fields.map((field, i) => (
              <div key={i}>
                <p className="font-mono text-[10px] text-on-muted uppercase tracking-wider mb-1">
                  {field.label}
                </p>
                <p className={cn(
                  'text-xs',
                  field.mono ? 'font-mono' : 'font-body',
                  'text-on-surface',
                )}>
                  {field.value}
                </p>
              </div>
            ))}
          </div>
        )}

        {children}
      </div>

      {shortcuts && shortcuts.length > 0 && (
        <div className="px-4 py-2 border-t border-outline/10">
          <div className="space-y-1">
            {shortcuts.map((shortcut, i) => (
              <div key={i} className="flex items-center gap-2">
                <Kbd keys={shortcut.keys} />
                <span className="font-mono text-[9px] text-on-muted">{shortcut.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="p-4 border-t border-outline/20 space-y-2">
        {actions.map((action, i) => (
          <Button
            key={i}
            variant={action.variant ?? 'primary'}
            size="sm"
            className="w-full justify-center"
            onClick={action.onClick}
            disabled={action.disabled}
            loading={action.loading}
          >
            {action.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
