import { IntelligentEditor } from '../../../components/organisms/IntelligentEditor';

interface Props {
  content: string;
  onChange: (value: string) => void;
}

export function DocumentEditor({ content, onChange }: Props) {
  return (
    <IntelligentEditor
      mode="fold"
      content={content}
      language="markdown"
      onChange={onChange}
      className="h-full"
    />
  );
}
