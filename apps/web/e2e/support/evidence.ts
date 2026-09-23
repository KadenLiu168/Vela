/*
 * Evidence helpers — identity records and screenshot hashing.
 *
 * The acceptance/baseline reports record:
 *   git HEAD, tracked-diff + untracked frontend-source fingerprint,
 *   build manifest hash, fixtures/harness fingerprint, browser version,
 *   route/state/viewport, screenshot paths and hashes.
 */
import { mkdir, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  buildManifestHash,
  gitHead,
  harnessFingerprint,
  sourceFingerprint
} from "./identity.ts";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

export type EvidenceEntry = {
  file: string;
  sha256: string;
};

export type EvidenceReport = {
  generatedAt: string;
  gitHead: string;
  sourceFingerprint: { hash: string; files: number };
  buildManifest: { hash: string; entry: string | null };
  harnessFingerprint: string;
  browser: { name: string; version: string };
  screenshots: EvidenceEntry[];
};

/** Collects the version identity for an evidence report. */
export async function collectIdentity(browserName: string, browserVersion: string): Promise<
  Omit<EvidenceReport, "generatedAt" | "screenshots">
> {
  const [source, manifest, harness] = await Promise.all([
    sourceFingerprint(),
    buildManifestHash(),
    harnessFingerprint()
  ]);

  return {
    gitHead: gitHead(),
    sourceFingerprint: source,
    buildManifest: manifest,
    harnessFingerprint: harness,
    browser: { name: browserName, version: browserVersion }
  };
}

/** Hashes a screenshot file and registers it as an evidence entry. */
export async function screenshotEntry(file: string): Promise<EvidenceEntry> {
  const content = await readFile(file);
  return { file: path.basename(file), sha256: createHash("sha256").update(content).digest("hex") };
}

/**
 * Writes the report and verifies every referenced screenshot actually exists
 * on disk (the report must not reference phantom artifacts).
 */
export async function writeEvidenceReport(
  reportDir: string,
  report: EvidenceReport
): Promise<void> {
  await mkdir(reportDir, { recursive: true });
  const reportPath = path.join(reportDir, "baseline-report.json");

  for (const entry of report.screenshots) {
    const resolved = path.join(reportDir, entry.file);
    const info = await stat(resolved);
    if (!info.isFile()) {
      throw new Error(`Evidence artifact missing: ${resolved}`);
    }
  }

  await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
}
