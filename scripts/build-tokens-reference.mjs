#!/usr/bin/env node
// scripts/build-tokens-reference.mjs
//
// Generates docs/tokens.md from apps/web/src/styles/tokens.css.
// Parses the :root { ... } block, groups declarations by the
// preceding /* N. Section — comment */ marker, resolves var(--X)
// aliases recursively, and emits Markdown.
//
// Zero runtime dependencies: uses only Node built-ins (fs, path).

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const REPO_ROOT = resolve(__dirname, "..");
const TOKENS_PATH = join(REPO_ROOT, "apps/web/src/styles/tokens.css");
const OUTPUT_PATH = join(REPO_ROOT, "docs/tokens.md");

function main() {
  const source = readFileSync(TOKENS_PATH, "utf8");
  const tokens = parseTokens(source);
  const groups = groupBySection(source, tokens);
  const markdown = renderMarkdown(groups);
  mkdirSync(dirname(OUTPUT_PATH), { recursive: true });
  writeFileSync(OUTPUT_PATH, markdown, "utf8");
  console.log(`Wrote ${OUTPUT_PATH} (${markdown.length} bytes, ${tokens.length} tokens across ${groups.length} groups)`);
}

function parseTokens(source) {
  const rootMatch = source.match(/:root\s*\{([\s\S]*?)\}/);
  if (!rootMatch) {
    throw new Error(`Could not find :root { ... } block in ${TOKENS_PATH}`);
  }
  const block = rootMatch[1];
  const tokens = new Map();
  const declRegex = /(--[a-zA-Z0-9-]+)\s*:\s*([^;]+);/g;
  let match;
  while ((match = declRegex.exec(block)) !== null) {
    tokens.set(match[1], match[2].trim());
  }
  return tokens;
}

function groupBySection(source, tokens) {
  // Find each /* N. Comment */ section marker before any token it precedes.
  // We split the source into "section header + declarations" chunks.
  const groups = [];
  const sectionRegex = /\/\*\s*(\d+[a-z]?\.\s*[^*]*?)\s*\*\//g;
  const sections = [];
  let match;
  while ((match = sectionRegex.exec(source)) !== null) {
    sections.push({
      title: match[1].trim(),
      start: match.index + match[0].length,
    });
  }
  // Add a trailing sentinel so the last section gets its tokens.
  sections.push({ title: "_tail", start: source.length });

  for (let i = 0; i < sections.length - 1; i++) {
    const sectionText = source.slice(sections[i].start, sections[i + 1].start);
    const decls = [];
    const declRegex = /(--[a-zA-Z0-9-]+)\s*:\s*([^;]+);/g;
    let m;
    while ((m = declRegex.exec(sectionText)) !== null) {
      decls.push({ name: m[1], value: m[2].trim() });
    }
    if (decls.length > 0) {
      groups.push({ title: sections[i].title, decls });
    }
  }
  return groups;
}

function resolveValue(name, tokens, depth = 0, seen = new Set()) {
  if (depth > 5) return "<cycle>";
  if (seen.has(name)) return "<cycle>";
  const value = tokens.get(name);
  if (value === undefined) return "<not declared>";
  const varMatch = value.match(/^var\((--[a-zA-Z0-9-]+)\)$/);
  if (!varMatch) return value;
  seen.add(name);
  return resolveValue(varMatch[1], tokens, depth + 1, seen);
}

function renderMarkdown(groups) {
  const tokens = new Map();
  for (const g of groups) {
    for (const d of g.decls) {
      tokens.set(d.name, d.value);
    }
  }

  const lines = [];
  lines.push("# Vela Web — Design Tokens Reference");
  lines.push("");
  lines.push(
    `> Auto-generated from \`apps/web/src/styles/tokens.css\` by \`scripts/build-tokens-reference.mjs\`.`
  );
  lines.push(
    "> Regenerate after editing tokens.css: `npm --prefix apps/web run build:tokens-doc`."
  );
  lines.push("");
  lines.push("## Table of Contents");
  lines.push("");
  for (const g of groups) {
    const anchor = g.title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    lines.push(`- [${g.title}](#${anchor})`);
  }
  lines.push("");
  for (const g of groups) {
    lines.push(`## ${g.title}`);
    lines.push("");
    lines.push("| Token | Value | Resolved |");
    lines.push("| --- | --- | --- |");
    for (const d of g.decls) {
      const resolved = resolveValue(d.name, tokens);
      const displayValue = d.value.length > 40 ? `\`${d.value.slice(0, 37)}...\`` : `\`${d.value}\``;
      const displayResolved =
        resolved === d.value || resolved === "<not declared>" || resolved === "<cycle>"
          ? ""
          : `→ \`${resolved}\``;
      lines.push(`| \`${d.name}\` | ${displayValue} | ${displayResolved} |`);
    }
    lines.push("");
  }
  return lines.join("\n");
}

main();
