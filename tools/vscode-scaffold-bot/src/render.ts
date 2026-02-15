/**
 * Template rendering engine.
 * Provides deterministic placeholder substitution and name transforms.
 */

export type TransformKind = "lower" | "upper" | "snake" | "kebab" | "pascal";

/** Convert an arbitrary name string to snake_case */
export function toSnakeCase(s: string): string {
  return s
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/[\s\-]+/g, "_")
    .toLowerCase();
}

/** Convert an arbitrary name string to kebab-case */
export function toKebabCase(s: string): string {
  return s
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/[\s_]+/g, "-")
    .toLowerCase();
}

/** Convert an arbitrary name string to PascalCase */
export function toPascalCase(s: string): string {
  return s
    .replace(/[\s_\-]+(.)/g, (_, c: string) => c.toUpperCase())
    .replace(/^(.)/, (_, c: string) => c.toUpperCase());
}

/** Apply a named transform to a value */
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
  name: string;
  snakeName: string;
  kebabName: string;
  pascalName: string;
  timestampISO: string;
  year: string;
}

/** Build the full set of built-in variables from a raw name and optional fixed timestamp */
export function buildBuiltInVars(name: string, nowISO?: string): BuiltInVars {
  const ts = nowISO ?? new Date().toISOString();
  return {
    name,
    snakeName: toSnakeCase(name),
    kebabName: toKebabCase(name),
    pascalName: toPascalCase(name),
    timestampISO: ts,
    year: ts.slice(0, 4),
  };
}

/**
 * Replace all `{{key}}` tokens in `text` with values from `vars`.
 * Unknown tokens are left as-is.
 */
export function renderString(text: string, vars: Record<string, string>): string {
  return text.replace(/\{\{(\w+)\}\}/g, (match, key: string) => {
    return Object.prototype.hasOwnProperty.call(vars, key) ? vars[key] : match;
  });
}
