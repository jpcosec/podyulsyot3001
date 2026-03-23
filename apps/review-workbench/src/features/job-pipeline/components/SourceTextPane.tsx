import { IntelligentEditor } from '../../../components/organisms/IntelligentEditor';
import type { RequirementItem, RequirementTextSpan } from '../../../types/api.types';

interface Props {
  markdown: string;
  highlight?: RequirementTextSpan | null;
  requirements?: RequirementItem[];
  onSpanSelect?: (range: { start: number; end: number; text: string }) => void;
}

export function SourceTextPane({ markdown, requirements = [], onSpanSelect }: Props) {
  // RequirementTextSpan uses line numbers; char-level highlights come from RequirementItem spans
  // We pass the active highlight as an empty array — IntelligentEditor handles
  // char-level highlighting via the requirements prop instead
  const highlights: { from: number; to: number; className: string }[] = [];

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-outline/20">
        <p className="font-mono text-[10px] text-on-muted uppercase tracking-[0.2em]">Source Text</p>
      </div>
      <div className="flex-1 overflow-hidden">
        <IntelligentEditor
          mode="tag-hover"
          content={markdown}
          language="markdown"
          highlights={highlights}
          requirements={requirements}
          readOnly={true}
          onSpanSelect={onSpanSelect}
        />
      </div>
    </div>
  );
}
