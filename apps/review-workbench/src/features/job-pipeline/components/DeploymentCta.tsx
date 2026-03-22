import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface Props {
  source: string;
  jobId: string;
  isComplete: boolean;
}

export function DeploymentCta({ source: _source, jobId: _jobId, isComplete }: Props) {
  const navigate = useNavigate();
  const [confirmed, setConfirmed] = useState(false);

  const handleClick = () => {
    if (!confirmed) {
      setConfirmed(true);
      return;
    }
    navigate('/');
  };

  if (!isComplete) {
    return (
      <div className="bg-surface-high border border-outline/20 p-4 text-center">
        <p className="font-mono text-[10px] text-on-muted uppercase">
          PIPELINE_INCOMPLETE — RETURN_TO_FLOW
        </p>
      </div>
    );
  }

  if (confirmed) {
    return (
      <div className="border border-primary/40 bg-primary/5 p-4">
        <p className="font-mono text-[10px] text-primary uppercase tracking-widest mb-3 text-center">
          Deployment confirmation — are you sure?
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => setConfirmed(false)}
            className="flex-1 border border-outline/40 text-on-muted font-mono text-xs py-2 hover:border-outline/80 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex-1 bg-primary text-primary-on font-headline font-bold uppercase tracking-widest text-xs py-2 tactical-glow hover:brightness-110 transition-all"
          >
            Confirm
          </button>
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={handleClick}
      className="w-full bg-primary text-primary-on font-headline font-bold uppercase tracking-widest text-sm py-4 tactical-glow hover:brightness-110 transition-all"
    >
      MARK AS DEPLOYED →
    </button>
  );
}
