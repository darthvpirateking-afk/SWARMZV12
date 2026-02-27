#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

const FORBIDDEN_PREFIXES = ["core/", "governance/", "protocol/"];
const REQUIRED_PREFIX = "plugins/";

function normalizePath(rawPath) {
  return String(rawPath || "")
    .trim()
    .replace(/\\/g, "/")
    .replace(/^\.\/+/, "");
}

function pathViolation(rawPath) {
  const normalized = normalizePath(rawPath);
  if (!normalized) {
    return null;
  }
  if (
    path.isAbsolute(normalized) ||
    normalized.startsWith("/") ||
    normalized.startsWith("../") ||
    normalized.includes("/../")
  ) {
    return `unsafe patch path: ${rawPath}`;
  }
  for (const prefix of FORBIDDEN_PREFIXES) {
    if (normalized.startsWith(prefix)) {
      return `path touches forbidden area: ${rawPath}`;
    }
  }
  if (!normalized.startsWith(REQUIRED_PREFIX)) {
    return `path must stay under plugins/: ${rawPath}`;
  }
  return null;
}

function extractFiles(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("patchpack must be a JSON object");
  }
  const files = payload.files;
  if (!Array.isArray(files)) {
    throw new Error("patchpack.files must be an array");
  }
  return files;
}

function validatePatchpack(payload) {
  const files = extractFiles(payload);
  for (const entry of files) {
    const entryPath =
      typeof entry === "string"
        ? entry
        : entry && typeof entry === "object"
          ? entry.path
          : "";
    const violation = pathViolation(entryPath);
    if (violation) {
      return { ok: false, reason: violation };
    }
  }
  return { ok: true };
}

function main() {
  const patchpackPath = process.argv[2];
  if (!patchpackPath) {
    console.error("Usage: node tools/validators/noCoreMutation.js <patchpack.json>");
    process.exit(1);
  }
  const fullPath = path.resolve(process.cwd(), patchpackPath);
  const payload = JSON.parse(fs.readFileSync(fullPath, "utf8"));
  const result = validatePatchpack(payload);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.ok ? 0 : 1);
}

if (require.main === module) {
  try {
    main();
  } catch (err) {
    console.error(
      JSON.stringify(
        {
          ok: false,
          reason: err instanceof Error ? err.message : String(err),
        },
        null,
        2
      )
    );
    process.exit(1);
  }
}

module.exports = {
  FORBIDDEN_PREFIXES,
  REQUIRED_PREFIX,
  normalizePath,
  pathViolation,
  validatePatchpack,
};
