import { IntelligentEditor } from '../../../components/organisms/IntelligentEditor';

interface Props {
  content: string;
}

export function JsonPreview({ content }: Props) {
  return (
    <div className="h-full overflow-hidden">
      <IntelligentEditor mode="fold" content={content} language="json" readOnly />
    </div>
  );
}
