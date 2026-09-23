/*
 * Build/evidence identity helpers.
 *
 * The acceptance report must record (per `web-frontend-app`):
 *   - git HEAD + tracked-diff / untracked frontend-source fingerprint,
 *   - build manifest hash,
 *   - fixtures + harness fingerprint,
 *   - browser version,
 *   - screenshot paths/hashes.
 * Generated artifacts (node_modules, dist, reports) are excluded from the
 * fingerprint so the report cannot self-reference.
 */
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

/* Playwright transpiles TS spec/support files, where `import.meta.url` is not
 * reliable; Playwright always runs with cwd = apps/web (the config root).
 */
const WEB_ROOT = process.cwd();
const REPO_ROOT = path.resolve(WEB_ROOT, "..", "..");

export function sha256(content: string): string {
  return createHash("sha256").update(content).digest("hex");
}

function git(args: string[]): string {
  return execFileSync("git", args, { cwd: REPO_ROOT, encoding: "utf8" }).trim();
}

export function gitHead(): string {
  return git(["rev-parse", "HEAD"]);
}

/**
 * Fingerprint of frontend-relevant source: tracked files (using the git
 * index + working tree contents) plus untracked-but-not-ignored frontend
 * files, excluding node_modules/dist/build/report directories.
 */
export async function sourceFingerprint(): Promise<{ hash: string; files: number }> {
  const tracked = git(["ls-files", "apps/web", "docs/tokens.md"]).split("\n").filter(Boolean);
  const status = git(["status", "--porcelain", "--", "apps/web", "docs/tokens.md"]);
  const untracked = status
    .split("\n")
    .filter((line) => line.startsWith("??"))
    .map((line) => line.slice(2).trim())
    .filter(Boolean);

  const files = new Set<string>(tracked);
  for (const entry of untracked) {
    if (entry.includes("node_modules") || entry.startsWith("apps/web/dist") || entry.startsWith("apps/web/build")) {
      continue;
    }
    // Untracked directories are listed with a trailing slash; expand shallow.
    if (entry.endsWith("/")) {
      const inner = await listFilesRecursively(path.join(REPO_ROOT, entry));
      for (const file of inner) {
        files.add(file);
      }
    } else {
      files.add(entry);
    }
  }

  const hash = createHash("sha256");
  for (const file of [...files].sort()) {
    try {
      const content = await readFile(path.join(REPO_ROOT, file));
      hash.update(file);
      hash.update(content);
    } catch {
      // Deleted in the working tree: record the deletion by hashing the path only.
      hash.update(file);
      hash.update("<deleted>");
    }
  }

  return { hash: sha256(hash.digest("hex")), files: files.size };
}

async function listFilesRecursively(dir: string): Promise<string[]> {
  const entries = await readdir(dir, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await listFilesRecursively(full)));
    } else {
      files.push(path.relative(REPO_ROOT, full));
    }
  }
  return files;
}

/** Hash of the Vite build manifest that identifies the tested build. */
export async function buildManifestHash(): Promise<{ hash: string; entry: string | null }> {
  const manifestPath = path.join(WEB_ROOT, "dist", ".vite", "manifest.json");
  const content = await readFile(manifestPath, "utf8");
  let manifest: Record<string, { isEntry?: boolean }>;
  try {
    manifest = JSON.parse(content) as Record<string, { isEntry?: boolean }>;
  } catch (error: unknown) {
    throw new Error(
      `dist/.vite/manifest.json is not valid JSON (was the acceptance build run?): ${String(error)}`
    );
  }
  const entryKey = Object.keys(manifest).find((key) => manifest[key]?.isEntry) ?? null;
  return { hash: sha256(content), entry: entryKey };
}

/** Hash of the fixtures + harness sources (runner, support, fixtures, specs). */
export async function harnessFingerprint(): Promise<string> {
  const files = await listFilesRecursively(path.join(WEB_ROOT, "e2e"));
  const hash = createHash("sha256");
  for (const file of files.sort()) {
    hash.update(file);
    hash.update(await readFile(path.join(REPO_ROOT, file)));
  }
  return sha256(hash.digest("hex"));
}

export async function browserIdentity(browserName: string, browserVersion: string): Promise<{
  name: string;
  version: string;
  userAgent?: string;
}> {
  return { name: browserName, version: browserVersion };
}
