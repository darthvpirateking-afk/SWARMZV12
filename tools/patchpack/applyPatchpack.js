#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { normalizePath, validatePatchpack } = require("../validators/noCoreMutation");

function usage() {
  console.error(
    "Usage: node tools/patchpack/applyPatchpack.js --patchpack <file> --root <dir> [--dry-run]"
  );
}

function parseArgs(argv) {
  const args = {
    dryRun: false,
    patchpack: "",
    root: "",
  };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--dry-run") {
      args.dryRun = true;
      continue;
    }
    if (token === "--patchpack") {
      args.patchpack = argv[i + 1] || "";
      i += 1;
      continue;
    }
    if (token === "--root") {
      args.root = argv[i + 1] || "";
      i += 1;
      continue;
    }
  }
  if (!args.patchpack || !args.root) {
    throw new Error("missing required arguments");
  }
  return args;
}

function ensureUnderRoot(rootDir, filePath) {
  const absRoot = path.resolve(rootDir);
  const absTarget = path.resolve(rootDir, filePath);
  const rel = path.relative(absRoot, absTarget).replace(/\\/g, "/");
  if (rel.startsWith("../") || rel.includes("/../") || rel === "..") {
    throw new Error(`path escapes root: ${filePath}`);
  }
  return absTarget;
}

function applyPatchpack(patchpack, rootDir, dryRun) {
  const validation = validatePatchpack(patchpack);
  if (!validation.ok) {
    throw new Error(validation.reason);
  }

  const writtenFiles = [];
  for (const entry of patchpack.files) {
    if (typeof entry === "string") {
      if (dryRun) {
        writtenFiles.push(normalizePath(entry));
      }
      continue;
    }
    if (!entry || typeof entry !== "object") {
      throw new Error("each file entry must be a string path or object");
    }
    const relPath = normalizePath(entry.path);
    const absPath = ensureUnderRoot(rootDir, relPath);
    const content = typeof entry.content === "string" ? entry.content : "";
    if (!dryRun) {
      fs.mkdirSync(path.dirname(absPath), { recursive: true });
      fs.writeFileSync(absPath, content, "utf8");
    }
    writtenFiles.push(relPath);
  }

  return {
    dry_run: dryRun,
    ok: true,
    root: path.resolve(rootDir).replace(/\\/g, "/"),
    written_files: writtenFiles,
  };
}

function main() {
  const args = parseArgs(process.argv);
  const patchpackPath = path.resolve(process.cwd(), args.patchpack);
  const payload = JSON.parse(fs.readFileSync(patchpackPath, "utf8"));
  const result = applyPatchpack(payload, args.root, args.dryRun);
  console.log(JSON.stringify(result, null, 2));
}

if (require.main === module) {
  try {
    main();
  } catch (err) {
    usage();
    console.error(
      JSON.stringify(
        {
          ok: false,
          error: err instanceof Error ? err.message : String(err),
        },
        null,
        2
      )
    );
    process.exit(1);
  }
}

module.exports = {
  applyPatchpack,
  ensureUnderRoot,
  parseArgs,
};
