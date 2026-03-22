import { useNavigate } from 'react-router-dom';
import { Button } from '../../../components/atoms/Button';
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
    <div className="w-80 bg-background border-l border-secondary/20 flex flex-col overflow-hidden">
      <div className="px-4 py-3 border-b border-outline/20">
        <p className="font-mono text-[10px] text-secondary uppercase tracking-[0.2em]">Phase</p>
        <p className="font-headline font-bold text-secondary uppercase tracking-widest text-sm">Extract</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
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
      </div>

      <div className="p-4 border-t border-outline/20 space-y-2">
        <div className="font-mono text-[9px] text-on-muted space-y-1">
          <p>Ctrl+S — Save draft</p>
          <p>Ctrl+Enter — Commit + go to match</p>
        </div>
        <Button variant="ghost" size="sm" className="w-full justify-center" onClick={onSave} loading={isSaving}>
          SAVE DRAFT
        </Button>
        <Button
          variant="primary"
          size="sm"
          className="w-full justify-center"
          onClick={() => {
            onSave();
            navigate(`/jobs/${source}/${jobId}/match`);
          }}
        >
          COMMIT → MATCH
        </Button>
      </div>
    </div>
  );
}
