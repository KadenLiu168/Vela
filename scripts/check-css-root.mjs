#!/usr/bin/env node
// Zero-dependency guard: fail if any CSS file under apps/web/src (except
// tokens.css) declares a `:root { ... }` block. The design-system
// OpenSpec capability requires all design tokens to live in tokens.css.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = dirname(fileURLToPath(import.meta.url)); // scripts/
const srcDir = join(repoRoot, "..", "apps", "web", "src"); // repo/apps/web/src
const allowed = new Set(["tokens.css"]);

function walk(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) out.push(...walk(full));
    else if (name.endsWith(".css")) out.push(full);
  }
  return out;
}

function hasRootBlock(css) {
  // strip /* ... */ block comments so selectors inside comments
  // (e.g. "MUST NOT contain a `:root { ... }` block") are ignored
  const stripped = css.replace(/\/\*[\s\S]*?\*\//g, "");
  return /:root\s*\{/.test(stripped);
}

const violations = [];
for (const file of walk(srcDir)) {
  if (allowed.has(file.split(/[\\/]/).pop())) continue;
  if (hasRootBlock(readFileSync(file, "utf8"))) {
    violations.push(relative(srcDir, file));
  }
}

if (violations.length) {
  console.error("ERROR: `:root` block found outside tokens.css:");
  for (const v of violations) console.error(`  - src/${v}`);
  process.exit(1);
}
console.log("OK: no `:root` block outside tokens.css");
