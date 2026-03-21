import { Link } from 'react-router-dom';

import { IntelligentEditor } from '../components/IntelligentEditor';

const SAMPLE_TEXT = `El candidato cuenta con sólida experiencia en Python y sistemas distribuidos,
habiendo liderado proyectos de integración de datos en entornos de alta disponibilidad.
Su trabajo de tesis abordó técnicas de preparación de datos a escala, directamente
alineado con los requisitos del puesto de Research Assistant en Data Integration.`;

export function IntelligentEditorPage(): JSX.Element {
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="breadcrumbs mb-6">
        <Link to="/">Portfolio</Link>
        <span>/</span>
        <Link to="/sandbox">Sandbox</Link>
        <span>/</span>
        <span>Intelligent Editor</span>
      </div>

      <h1 className="font-headline text-lg font-bold uppercase tracking-widest text-on-surface mb-1">
        Intelligent Editor
      </h1>
      <p className="text-sm text-on-muted mb-6">
        Click any highlighted tag to pin it in the context sidebar. Hover to preview.
        Lines connect pinned context to their source spans.
      </p>

      <IntelligentEditor text={SAMPLE_TEXT} />
    </div>
  );
}
