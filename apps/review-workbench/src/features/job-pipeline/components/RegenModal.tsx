import { useState } from 'react';
import { Button } from '../../../components/atoms/Button';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (feedback: string) => void;
  isLoading: boolean;
}

export function RegenModal({ isOpen, onClose, onConfirm, isLoading }: Props) {
  const [feedback, setFeedback] = useState('');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-surface-container border border-secondary/30 w-96 p-6">
        <div className="mb-4">
          <p className="font-mono text-[10px] text-secondary uppercase tracking-[0.2em] mb-1">Regenerate</p>
          <h2 className="font-headline font-bold text-on-surface uppercase">Request Regeneration</h2>
        </div>
        <textarea
          value={feedback}
          onChange={e => setFeedback(e.target.value)}
          placeholder="Describe what needs to be improved…"
          className="w-full bg-surface-low border border-outline/30 p-3 font-body text-sm text-on-surface placeholder:text-on-muted resize-none h-24 focus:outline-none focus:border-secondary/50 mb-4"
        />
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" className="flex-1 justify-center" onClick={onClose}>
            CANCEL
          </Button>
          <Button
            variant="primary"
            size="sm"
            className="flex-1 justify-center"
            onClick={() => { onConfirm(feedback); setFeedback(''); }}
            loading={isLoading}
          >
            CONFIRM REGEN
          </Button>
        </div>
      </div>
    </div>
  );
}
