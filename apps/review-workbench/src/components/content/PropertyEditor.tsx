import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

import type { AttributeType, PropertyEditorProps, PropertyPair } from "./types";

const ATTRIBUTE_TYPES: AttributeType[] = [
  "string",
  "text_markdown",
  "number",
  "date",
  "datetime",
  "boolean",
  "enum",
  "enum_open",
];

export function PropertyEditor({ pairs, onChange, readOnly = false }: PropertyEditorProps) {
  const updatePair = (index: number, updates: Partial<PropertyPair>) => {
    const next = [...pairs];
    next[index] = { ...next[index], ...updates };
    onChange(next);
  };

  const addPair = () => {
    onChange([...pairs, { key: "", value: "", dataType: "string" }]);
  };

  const removePair = (index: number) => {
    onChange(pairs.filter((_, pairIndex) => pairIndex !== index));
  };

  return (
    <div className="space-y-3">
      {pairs.map((pair, index) => (
        <div key={index} className="space-y-1">
          <div className="flex items-center gap-1">
            <Input
              value={pair.key}
              onChange={(event) => updatePair(index, { key: event.target.value })}
              placeholder="key"
              className="h-8 font-mono text-xs"
              disabled={readOnly}
            />
            <Select
              value={pair.dataType}
              onValueChange={(value: AttributeType) => updatePair(index, { dataType: value })}
              disabled={readOnly}
            >
              <SelectTrigger className="h-8 w-[130px] text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ATTRIBUTE_TYPES.map((type) => (
                  <SelectItem key={type} value={type} className="text-xs">
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {!readOnly ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-8 px-2 text-destructive"
                onClick={() => removePair(index)}
              >
                x
              </Button>
            ) : null}
          </div>

          <PropertyValueInput
            pair={pair}
            onChange={(value) => updatePair(index, { value })}
            readOnly={readOnly}
          />
        </div>
      ))}

      {!readOnly ? (
        <Button type="button" variant="outline" size="sm" className="w-full" onClick={addPair}>
          + Add Property
        </Button>
      ) : null}
    </div>
  );
}

interface PropertyValueInputProps {
  pair: PropertyPair;
  onChange: (value: string) => void;
  readOnly: boolean;
}

function PropertyValueInput({ pair, onChange, readOnly }: PropertyValueInputProps) {
  switch (pair.dataType) {
    case "text_markdown":
      return (
        <Textarea
          value={pair.value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Markdown content..."
          className="min-h-[80px] text-xs"
          disabled={readOnly}
        />
      );

    case "number":
      return (
        <Input
          type="number"
          value={pair.value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="0"
          className="text-xs"
          disabled={readOnly}
        />
      );

    case "date":
      return (
        <Input
          type="date"
          value={pair.value}
          onChange={(event) => onChange(event.target.value)}
          className="text-xs"
          disabled={readOnly}
        />
      );

    case "datetime":
      return (
        <Input
          type="datetime-local"
          value={pair.value}
          onChange={(event) => onChange(event.target.value)}
          className="text-xs"
          disabled={readOnly}
        />
      );

    case "boolean":
      return (
        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={pair.value === "true"}
            onChange={(event) => onChange(event.target.checked ? "true" : "false")}
            disabled={readOnly}
          />
          {pair.value === "true" ? "true" : "false"}
        </label>
      );

    case "enum":
      return (
        <Select value={pair.value || undefined} onValueChange={onChange} disabled={readOnly}>
          <SelectTrigger className="text-xs">
            <SelectValue placeholder="select..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="low" className="text-xs">
              Low
            </SelectItem>
            <SelectItem value="medium" className="text-xs">
              Medium
            </SelectItem>
            <SelectItem value="high" className="text-xs">
              High
            </SelectItem>
          </SelectContent>
        </Select>
      );

    default:
      return (
        <Input
          value={pair.value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={pair.dataType === "enum_open" ? "value (free enum)" : "value"}
          className="text-xs"
          disabled={readOnly}
        />
      );
  }
}
