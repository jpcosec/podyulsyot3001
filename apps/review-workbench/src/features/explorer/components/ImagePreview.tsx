interface Props {
  path: string;
  content: string | null;
}

export function ImagePreview({ path, content }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 gap-4">
      {content ? (
        <img
          src={`data:image/png;base64,${content}`}
          alt={path}
          className="max-w-full max-h-96 border border-outline/20"
        />
      ) : (
        <div className="border border-outline/20 bg-surface-container p-8 text-center">
          <p className="font-mono text-[10px] text-on-muted uppercase">IMAGE_NOT_AVAILABLE</p>
          <p className="font-mono text-[10px] text-on-muted mt-1">{path}</p>
        </div>
      )}
    </div>
  );
}
