import type { ArtifactFile } from '../../../types/api.types';

interface Props {
  files: ArtifactFile[];
}

export function ErrorScreenshot({ files }: Props) {
  const screenshotFile = files.find(f => f.path.endsWith('error_screenshot.png'));
  if (!screenshotFile) return null;

  return (
    <div className="border border-error/40 bg-error-container/10 p-4">
      <p className="font-mono text-[10px] text-error uppercase tracking-[0.2em] mb-3">
        Error Screenshot
      </p>
      {screenshotFile.content_type === 'image' && screenshotFile.content ? (
        <img
          src={`data:image/png;base64,${screenshotFile.content}`}
          alt="Scrape error screenshot"
          className="max-w-full border border-error/20"
        />
      ) : (
        <p className="font-mono text-xs text-error">
          ERROR_TRACE: {screenshotFile.path}
        </p>
      )}
    </div>
  );
}
