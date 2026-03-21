import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { browseExplorer } from "../api/client";
import type { ExplorerPayload } from "../types/models";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function BreadcrumbNav({ currentPath }: { currentPath: string }): JSX.Element {
  const parts = currentPath.split("/").filter(Boolean);
  const crumbs = [{ label: "data/jobs", path: "" }];
  let accumulated = "";
  for (const part of parts) {
    accumulated = accumulated ? `${accumulated}/${part}` : part;
    crumbs.push({ label: part, path: accumulated });
  }
  return (
    <div className="breadcrumbs">
      {crumbs.map((crumb, i) => (
        <span key={crumb.path || "root"}>
          {i > 0 && <span>/</span>}
          {i < crumbs.length - 1 ? (
            <Link to={`/explorer?path=${encodeURIComponent(crumb.path)}`}>{crumb.label}</Link>
          ) : (
            <span>{crumb.label}</span>
          )}
        </span>
      ))}
    </div>
  );
}

function FilePreview({ data }: { data: ExplorerPayload }): JSX.Element {
  if (data.content_type === "image" && data.content) {
    return <img src={data.content} alt={data.name} style={{ maxWidth: "100%", borderRadius: 4 }} />;
  }
  if (data.content_type === "too_large") {
    return <p className="text-dim">File too large to preview ({formatSize(data.size_bytes ?? 0)})</p>;
  }
  if (data.content_type === "binary") {
    return <p className="text-dim">Binary file — no preview available</p>;
  }
  const isJson = data.extension === ".json";
  let displayContent = data.content ?? "";
  if (isJson) {
    try {
      displayContent = JSON.stringify(JSON.parse(displayContent), null, 2);
    } catch {
      /* keep raw */
    }
  }
  return <pre className="explorer-preview">{displayContent}</pre>;
}

export function DataExplorerPage(): JSX.Element {
  const [searchParams] = useSearchParams();
  const currentPath = searchParams.get("path") ?? "";
  const [data, setData] = useState<ExplorerPayload | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setData(null);
    setError("");
    browseExplorer(currentPath)
      .then(setData)
      .catch((err: Error) => setError(err.message));
  }, [currentPath]);

  return (
    <section className="panel">
      <BreadcrumbNav currentPath={currentPath} />
      <h1>Data Explorer</h1>
      <p className="text-dim">Browse local artifacts in data/jobs/</p>

      {error && <p className="error">{error}</p>}

      {data?.is_dir && data.entries && (
        <div className="explorer-list">
          {data.entries.map((entry) => (
            <Link
              key={entry.path}
              to={`/explorer?path=${encodeURIComponent(entry.path)}`}
              className="explorer-entry"
            >
              <span className="material-symbols-outlined">
                {entry.is_dir ? "folder" : "description"}
              </span>
              <span className="explorer-entry-name">{entry.name}</span>
              {!entry.is_dir && entry.size_bytes != null && (
                <span className="explorer-entry-meta">{formatSize(entry.size_bytes)}</span>
              )}
              {entry.is_dir && entry.child_count != null && (
                <span className="explorer-entry-meta">{entry.child_count} items</span>
              )}
            </Link>
          ))}
          {data.entries.length === 0 && <p className="text-dim">Empty directory</p>}
        </div>
      )}

      {data && !data.is_dir && (
        <div className="explorer-file-view">
          <div className="explorer-file-header">
            <strong>{data.name}</strong>
            {data.size_bytes != null && <span className="text-dim">{formatSize(data.size_bytes)}</span>}
          </div>
          <FilePreview data={data} />
        </div>
      )}

      {!data && !error && <p>Loading...</p>}
    </section>
  );
}
