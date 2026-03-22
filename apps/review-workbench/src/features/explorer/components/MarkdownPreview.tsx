import CodeMirror from '@uiw/react-codemirror';
import { markdown } from '@codemirror/lang-markdown';
import { oneDark } from '@codemirror/theme-one-dark';

interface Props {
  content: string;
}

export function MarkdownPreview({ content }: Props) {
  return (
    <CodeMirror
      value={content}
      extensions={[markdown()]}
      theme={oneDark}
      editable={false}
      basicSetup={{ lineNumbers: true }}
      className="text-xs h-full overflow-auto"
    />
  );
}
