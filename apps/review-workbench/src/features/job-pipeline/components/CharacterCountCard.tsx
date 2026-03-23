import { cn } from '../../../utils/cn';

interface Props {
  original: number;
  translated: number;
}

export function CharacterCountCard({ original, translated }: Props) {
  const delta = translated - original;
  const percent = ((delta / original) * 100).toFixed(1);
  const isSignificantLoss = delta < 0 && Math.abs(delta / original) > 0.2;

  return (
    <div className="bg-surface-container-low border border-outline/20 p-4">
      <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em] mb-3">
        Character Count
      </p>

      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-on-muted w-24">Original</span>
          <span className="font-mono text-xs text-on-surface">
            {original.toLocaleString()} chars
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-on-muted w-24">Translated</span>
          <span className="font-mono text-xs text-on-surface">
            {translated.toLocaleString()} chars
          </span>
        </div>
        <div className="flex items-center gap-2 pt-1 border-t border-outline/10">
          <span className="font-mono text-[10px] text-on-muted w-24">Delta</span>
          <span
            className={cn(
              'font-mono text-xs',
              isSignificantLoss ? 'text-error' : 'text-primary'
            )}
          >
            {delta >= 0 ? '+' : ''}{delta.toLocaleString()} ({percent}%)
          </span>
        </div>
      </div>

      {isSignificantLoss && (
        <div className="mt-3 p-2 border border-error/30 bg-error/5 font-mono text-[10px] text-error">
          ⚠ High character loss detected (&gt;20%). Verify translation quality.
        </div>
      )}
    </div>
  );
}
