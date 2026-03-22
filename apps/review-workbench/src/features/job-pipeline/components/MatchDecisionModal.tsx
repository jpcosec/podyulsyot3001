import { useState } from 'react';
import { Button } from '../../../components/atoms/Button';
import type { GateDecisionPayload } from '../../../types/api.types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onDecide: (payload: GateDecisionPayload) => void;
  isLoading: boolean;
}

export function MatchDecisionModal({ isOpen, onClose, onDecide, isLoading }: Props) {
  const [feedback, setFeedback] = useState('');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-surface-container border border-secondary/30 w-96 p-6">
        <div className="mb-4">
          <p className="font-mono text-[10px] text-secondary uppercase tracking-[0.2em] mb-1">Gate Decision</p>
          <h2 className="font-headline font-bold text-on-surface uppercase">Review Match</h2>
        </div>

        <div className="space-y-3 mb-4">
          <Button
            variant="primary"
            size="sm"
            className="w-full justify-center"
            onClick={() => onDecide({ decision: 'approve' })}
            loading={isLoading}
          >
            ✓ APPROVE
          </Button>
          <div>
            <textarea
              value={feedback}
              onChange={e => setFeedback(e.target.value)}
              placeholder="Optional feedback for regeneration..."
              className="w-full bg-surface-low border border-outline/30 p-2 font-mono text-xs text-on-surface placeholder:text-on-muted resize-none h-20 focus:outline-none focus:border-primary/50"
            />
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-center mt-1"
              onClick={() => onDecide({ decision: 'request_regeneration', feedback: feedback ? [feedback] : [] })}
              loading={isLoading}
            >
              ↻ REQUEST REGEN
            </Button>
          </div>
          <Button
            variant="danger"
            size="sm"
            className="w-full justify-center"
            onClick={() => onDecide({ decision: 'reject' })}
            loading={isLoading}
          >
            ✗ REJECT
          </Button>
        </div>

        <button
          onClick={onClose}
          className="font-mono text-[10px] text-on-muted uppercase hover:text-on-surface w-full text-center"
        >
          CANCEL
        </button>
      </div>
    </div>
  );
}
