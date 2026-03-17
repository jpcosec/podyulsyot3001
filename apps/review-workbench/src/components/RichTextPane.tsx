import { useMemo, useState } from "react";
import { createEditor, Descendant } from "slate";
import { Editable, Slate, withReact } from "slate-react";

const initialValue: Descendant[] = [
  {
    children: [{ text: "Select text and annotate in this panel during review." }],
  },
];

export function RichTextPane(): JSX.Element {
  const editor = useMemo(() => withReact(createEditor()), []);
  const [value, setValue] = useState<Descendant[]>(initialValue);

  return (
    <div className="slate-shell">
      <Slate editor={editor} initialValue={value} onChange={setValue}>
        <Editable className="slate-editor" placeholder="Write review notes..." />
      </Slate>
    </div>
  );
}
