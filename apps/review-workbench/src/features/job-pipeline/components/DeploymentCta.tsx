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

  return (
    <button
      onClick={handleClick}
      className="w-full bg-primary text-primary-on font-headline font-bold uppercase tracking-widest text-sm py-4 tactical-glow hover:brightness-110 transition-all"
    >
      {confirmed ? '[ CONFIRM DEPLOYMENT → ]' : 'MARK AS DEPLOYED →'}
    </button>
  );
}
