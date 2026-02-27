export type TransformKind = "lower" | "upper" | "snake" | "kebab" | "pascal";

export function toSnakeCase(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/[\s\-]+/g, "_")
    .toLowerCase();
}

export function toKebabCase(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/[\s_]+/g, "-")
    .toLowerCase();
}

export function toPascalCase(value: string): string {
  return value
    .replace(/[\s_\-]+(.)/g, (_, c: string) => c.toUpperCase())
    .replace(/^(.)/, (_, c: string) => c.toUpperCase());
}

export function applyTransform(value: string, transform: TransformKind): string {
  switch (transform) {
    case "lower":
      return value.toLowerCase();
    case "upper":
      return value.toUpperCase();
    case "snake":
      return toSnakeCase(value);
    case "kebab":
      return toKebabCase(value);
    case "pascal":
      return toPascalCase(value);
    default:
      return value;
  }
}

export interface BuiltInVars {
  kebabName: string;
  name: string;
  pascalName: string;
  snakeName: string;
  timestampISO: string;
  year: string;
}

export function buildBuiltInVars(name: string, nowISO?: string): BuiltInVars {
  const timestamp = nowISO ?? new Date().toISOString();
  return {
    kebabName: toKebabCase(name),
    name,
    pascalName: toPascalCase(name),
    snakeName: toSnakeCase(name),
    timestampISO: timestamp,
    year: timestamp.slice(0, 4),
  };
}

export function renderString(text: string, vars: Record<string, string>): string {
  return text.replace(/\{\{(\w+)\}\}/g, (match, key: string) => {
    return Object.prototype.hasOwnProperty.call(vars, key) ? vars[key] : match;
  });
}
