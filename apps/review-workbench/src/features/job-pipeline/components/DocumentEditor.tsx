import CodeMirror from '@uiw/react-codemirror';
import { markdown } from '@codemirror/lang-markdown';
import { oneDark } from '@codemirror/theme-one-dark';

interface Props {
  content: string;
  onChange: (value: string) => void;
}

export function DocumentEditor({ content, onChange }: Props) {
  return (
    <CodeMirror
      value={content}
      extensions={[markdown()]}
      theme={oneDark}
      onChange={onChange}
      basicSetup={{ lineNumbers: true, foldGutter: false }}
      className="flex-1 h-full text-sm overflow-auto"
      style={{ height: '100%' }}
    />
  );
}
