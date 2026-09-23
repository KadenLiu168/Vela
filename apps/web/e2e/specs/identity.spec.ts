import { writeFile, unlink } from "node:fs/promises";
import path from "node:path";
import { test, expect } from "../support/test.ts";
import { sourceFingerprint } from "../support/identity.ts";

test("generated Change evidence does not change the frontend source fingerprint", async () => {
  const before = await sourceFingerprint();
  const probe = path.resolve(
    process.cwd(),
    "../../openspec/changes/refine-web-research-visual-system/evidence/browser/fingerprint-probe.txt"
  );
  try {
    await writeFile(probe, "generated evidence probe\n");
    expect(await sourceFingerprint()).toEqual(before);
  } finally {
    await unlink(probe);
  }
});
