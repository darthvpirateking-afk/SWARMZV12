import * as fs from "fs";
import * as path from "path";
import { TemplateMeta } from "./templateRegistry";
import { RenderCtx, renderString } from "./render";

export interface FilePlan {
  relativePath: string;
  absolutePath: string;
  content: string;
  exists: boolean;
}

export function planFromTemplate(
  template: TemplateMeta,
  targetDir: string,
  ctx: RenderCtx
): FilePlan[] {
  const filesDir = path.join(template.dir, "files");
  if (!fs.existsSync(filesDir)) return [];

  const plans: FilePlan[] = [];
  collectFiles(filesDir, filesDir, targetDir, ctx, plans);
  return plans;
}

function collectFiles(
  baseDir: string,
  currentDir: string,
  targetDir: string,
  ctx: RenderCtx,
  plans: FilePlan[]
): void {
  for (const entry of fs.readdirSync(currentDir, { withFileTypes: true })) {
    const srcPath = path.join(currentDir, entry.name);
    const relFromBase = path.relative(baseDir, srcPath);
    const renderedRel = renderString(relFromBase, ctx);

    if (entry.isDirectory()) {
      collectFiles(baseDir, srcPath, targetDir, ctx, plans);
    } else {
      const raw = fs.readFileSync(srcPath, "utf-8");
      const content = renderString(raw, ctx);
      const absTarget = path.join(targetDir, renderedRel);
      plans.push({
        relativePath: renderedRel,
        absolutePath: absTarget,
        content,
        exists: fs.existsSync(absTarget),
      });
    }
  }
}

export async function generateFromTemplate(
  plans: FilePlan[],
  allowOverwrite: boolean
): Promise<{ written: string[]; skipped: string[] }> {
  const written: string[] = [];
  const skipped: string[] = [];

  for (const plan of plans) {
    if (plan.exists && !allowOverwrite) {
      skipped.push(plan.relativePath);
      continue;
    }
    const dir = path.dirname(plan.absolutePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(plan.absolutePath, plan.content, "utf-8");
    written.push(plan.relativePath);
  }

  return { written, skipped };
}
