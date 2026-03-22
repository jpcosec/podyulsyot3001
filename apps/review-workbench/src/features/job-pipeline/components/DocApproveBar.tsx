import { cn } from '../../../utils/cn';
import type { DocKey } from './DocumentTabs';

interface Props {
  onSave: () => void;
  onApprove: () => void;
  isSaving: boolean;
  isApproved: boolean;
  activeTab: DocKey;
}

export function DocApproveBar({ onSave, onApprove, isSaving, isApproved, activeTab: _ }: Props) {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-surface-container border-t border-outline/20">
      <span className="font-mono text-[9px] text-on-muted">
        Ctrl+S to save · Ctrl+Enter to approve
      </span>
      <div className="flex gap-2">
        <button
          onClick={onSave}
          disabled={isSaving}
          className={cn(
            'font-mono text-[10px] uppercase tracking-widest px-3 py-1.5 border transition-colors',
            'border-outline/30 text-on-muted hover:text-on-surface hover:border-outline/60',
            isSaving && 'opacity-50 cursor-not-allowed'
          )}
        >
          {isSaving ? 'SAVING…' : 'SAVE'}
        </button>
        <button
          onClick={onApprove}
          className={cn(
            'font-mono text-[10px] uppercase tracking-widest px-3 py-1.5 border transition-colors',
            isApproved
              ? 'border-primary/40 text-primary bg-primary/10'
              : 'border-primary/30 text-primary hover:bg-primary/10'
          )}
        >
          {isApproved ? '✓ APPROVED' : 'APPROVE'}
        </button>
      </div>
    </div>
  );
}
