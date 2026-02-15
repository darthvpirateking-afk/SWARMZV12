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
export interface RenderCtx {
  [key: string]: string;
}

export function buildCtx(vars: Record<string, string>): RenderCtx {
  const ctx: RenderCtx = { ...vars };

  // Derive common casing variants if a "name" variable exists
  if (ctx["name"]) {
    const raw = ctx["name"];
    if (!ctx["snakeName"]) {
      ctx["snakeName"] = toSnake(raw);
    }
    if (!ctx["camelName"]) {
      ctx["camelName"] = toCamel(raw);
    }
    if (!ctx["PascalName"]) {
      ctx["PascalName"] = toPascal(raw);
    }
    if (!ctx["kebabName"]) {
      ctx["kebabName"] = toKebab(raw);
    }
  }
  return ctx;
}

export function renderString(template: string, ctx: RenderCtx): string {
  return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    return key in ctx ? ctx[key] : match;
  });
}

function toSnake(s: string): string {
  return s
    .replace(/([a-z])([A-Z])/g, "$1_$2")
    .replace(/[\s\-]+/g, "_")
    .toLowerCase();
}

function toCamel(s: string): string {
  const snake = toSnake(s);
  return snake.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
}

function toPascal(s: string): string {
  const camel = toCamel(s);
  return camel.charAt(0).toUpperCase() + camel.slice(1);
}

function toKebab(s: string): string {
  return toSnake(s).replace(/_/g, "-");
}
