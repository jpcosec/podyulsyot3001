import { useEffect } from 'react';
import { cn } from '../../utils/cn';

interface Shortcut {
  key: string;
  action: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  shortcuts: Shortcut[];
  title?: string;
}

export function ShortcutsModal({ isOpen, onClose, shortcuts, title }: Props) {
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-surface-container border border-outline/30 p-6 min-w-[320px] max-w-[480px] relative"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          {title && (
            <p className={cn('font-mono text-[10px] text-on-muted uppercase tracking-widest')}>
              {title}
            </p>
          )}
          <button
            onClick={onClose}
            className="font-mono text-sm text-on-muted/60 hover:text-on-muted ml-auto"
          >
            ×
          </button>
        </div>
        <table className="w-full">
          <tbody>
            {shortcuts.map(({ key, action }) => (
              <tr key={key} className="border-b border-outline/10 last:border-0">
                <td className="py-1.5 pr-4">
                  <kbd className="font-mono text-xs bg-surface-high border border-outline/30 px-1.5 py-0.5 whitespace-nowrap">
                    {key}
                  </kbd>
                </td>
                <td className="py-1.5 font-mono text-xs text-on-surface">
                  {action}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
