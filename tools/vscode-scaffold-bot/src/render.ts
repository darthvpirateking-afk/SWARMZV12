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
