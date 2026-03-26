export type AttributeType =
  | "string"
  | "text_markdown"
  | "number"
  | "date"
  | "datetime"
  | "boolean"
  | "enum"
  | "enum_open";

export interface EntityCardProps {
  title: string;
  category: string;
  properties?: Record<string, string>;
  badges?: string[];
  visualToken?: string;
}

export interface PropertiesPreviewProps {
  properties: Record<string, string>;
}

export interface PropertyPair {
  key: string;
  value: string;
  dataType: AttributeType;
}

export interface PropertyEditorProps {
  pairs: PropertyPair[];
  onChange: (pairs: PropertyPair[]) => void;
  readOnly?: boolean;
}

export interface PlaceholderNodeProps {
  colorToken: string;
}
