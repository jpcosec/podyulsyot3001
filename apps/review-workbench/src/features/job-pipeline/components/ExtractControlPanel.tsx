import { useNavigate } from 'react-router-dom';
import { ControlPanel } from '../../../components/molecules/ControlPanel';
import type { RequirementItem } from '../../../types/api.types';

interface Props {
  source: string;
  jobId: string;
  selectedReq: RequirementItem | null;
  onSave: () => void;
  isSaving: boolean;
}

export function ExtractControlPanel({ source, jobId, selectedReq, onSave, isSaving }: Props) {
  const navigate = useNavigate();

  return (
    <ControlPanel
      title="Extract"
      phaseColor="secondary"
      actions={[
        { label: 'SAVE DRAFT', variant: 'ghost', onClick: onSave, loading: isSaving },
        {
          label: 'COMMIT → MATCH',
          variant: 'primary',
          onClick: () => { onSave(); navigate(`/jobs/${source}/${jobId}/match`); },
        },
      ]}
      shortcuts={[
        { keys: ['Ctrl', 'S'], label: 'Save draft' },
        { keys: ['Ctrl', 'Enter'], label: 'Commit + go to match' },
      ]}
    >
      {selectedReq ? (
        <div>
          <p className="font-mono text-[10px] text-on-muted uppercase mb-2">Selected Req</p>
          <pre className="bg-surface-container border border-outline/20 p-2 font-mono text-[9px] text-on-surface overflow-auto whitespace-pre-wrap">
            {JSON.stringify(selectedReq, null, 2)}
          </pre>
        </div>
      ) : (
        <p className="font-mono text-[10px] text-on-muted uppercase">Click a requirement to inspect</p>
      )}
    </ControlPanel>
  );
}
