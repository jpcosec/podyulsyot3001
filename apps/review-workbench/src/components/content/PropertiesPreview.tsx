import { useState } from "react";

import { Button } from "@/components/ui/button";

import type { PropertiesPreviewProps } from "./types";

export function PropertiesPreview({ properties }: PropertiesPreviewProps) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(properties);

  if (entries.length === 0) {
    return null;
  }

  return (
    <div className="rounded-md border">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="h-8 w-full justify-between rounded-b-none rounded-t-md px-2 font-mono text-[10px] uppercase"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span>Properties</span>
        <span className="text-xs text-muted-foreground">{entries.length}</span>
      </Button>

      {open ? (
        <div className="max-h-44 overflow-auto border-t">
          <table className="w-full text-left text-xs">
            <thead className="bg-muted/40">
              <tr>
                <th className="w-[120px] px-2 py-1 font-mono text-[10px] uppercase">Key</th>
                <th className="px-2 py-1 font-mono text-[10px] uppercase">Value</th>
              </tr>
            </thead>
            <tbody>
              {entries.map(([key, value]) => (
                <tr key={key} className="border-t">
                  <td className="px-2 py-1 font-mono">{key}</td>
                  <td className="max-w-[240px] truncate px-2 py-1">{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
