import { Link } from "react-router-dom";

import { RichTextPane } from "../components/RichTextPane";

export function TextTaggerPage(): JSX.Element {
  return (
    <section className="panel">
      <div className="breadcrumbs">
        <Link to="/">Portfolio</Link>
        <span>/</span>
        <Link to="/sandbox">Sandbox</Link>
        <span>/</span>
        <span>Text Tagger</span>
      </div>
      <h1>Text Tagger</h1>
      <p>
        Select text patches, assign relation categories, and manage mapped node cards in the
        sidebar.
      </p>
      <RichTextPane />
    </section>
  );
}
