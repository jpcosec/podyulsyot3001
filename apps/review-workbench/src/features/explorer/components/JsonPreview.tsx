import CodeMirror from '@uiw/react-codemirror';
import { json } from '@codemirror/lang-json';
import { oneDark } from '@codemirror/theme-one-dark';

interface Props {
  content: string;
}

export function JsonPreview({ content }: Props) {
  return (
    <CodeMirror
      value={content}
      extensions={[json()]}
      theme={oneDark}
      editable={false}
      basicSetup={{ lineNumbers: true, foldGutter: true }}
      className="text-xs h-full overflow-auto"
    />
  );
}
