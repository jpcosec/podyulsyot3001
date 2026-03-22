import { useNavigate } from 'react-router-dom';

interface Props {
  source: string;
  jobId: string;
  currentNode: string;
}

const NODE_ROUTE_MAP: Record<string, string> = {
  scrape: 'scrape',
  translate_if_needed: 'scrape',
  extract_understand: 'extract',
  match: 'match',
  review_match: 'match',
  generate_documents: 'sculpt',
  render: 'sculpt',
  package: 'deployment',
};

export function HitlCtaBanner({ source, jobId, currentNode }: Props) {
  const navigate = useNavigate();
  const routeSuffix = NODE_ROUTE_MAP[currentNode] || currentNode;

  const handleGoToReview = () => {
    navigate(`/jobs/${source}/${jobId}/${routeSuffix}`);
  };

  return (
    <div className="bg-secondary/10 border border-secondary/40 p-4 flex items-center justify-between mb-4">
      <span className="font-headline font-bold uppercase text-sm text-on-surface">
        HUMAN REVIEW REQUIRED — {currentNode.toUpperCase()}
      </span>
      <button
        onClick={handleGoToReview}
        className="bg-secondary text-black font-headline font-bold uppercase text-xs px-4 py-2 hover:bg-secondary/90 transition-colors"
      >
        GO TO REVIEW →
      </button>
    </div>
  );
}
