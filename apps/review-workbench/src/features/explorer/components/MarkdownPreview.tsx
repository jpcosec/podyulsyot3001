import { IntelligentEditor } from '../../../components/organisms/IntelligentEditor';

interface Props {
  content: string;
}

export function MarkdownPreview({ content }: Props) {
  return (
    <div className="h-full overflow-hidden">
      <IntelligentEditor mode="fold" content={content} language="markdown" readOnly />
    </div>
  );
}
