import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import stylelint from "stylelint";

/**
 * Concentrated design-system static contract tests.
 *
 * Owned by the `design-system` OpenSpec capability: exact semantic token
 * values, dual-font runtime resources/preloads, forbidden legacy tokens, and
 * the canonical-root guarantee. These tests intentionally pin exact values —
 * a value change requires an OpenSpec change first.
 */

const WEB_ROOT = join(__dirname, "../..");
const SRC_ROOT = join(WEB_ROOT, "src");
const TOKENS_CSS = readFileSync(join(SRC_ROOT, "styles/tokens.css"), "utf8");
const STYLES_CSS = readFileSync(join(SRC_ROOT, "styles.css"), "utf8");
const INDEX_HTML = readFileSync(join(WEB_ROOT, "index.html"), "utf8");
const PUBLIC_FONTS_DIR = join(WEB_ROOT, "public/fonts");
const GITIGNORE = readFileSync(join(WEB_ROOT, "../../.gitignore"), "utf8");

/** Strips block comments so prose cannot satisfy or break checks. */
function stripCssComments(css: string): string {
  return css.replace(/\/\*[\s\S]*?\*\//g, "");
}

const TOKENS_BODY = stripCssComments(TOKENS_CSS).match(
  /:root\s*\{([\s\S]*)\}/
)![1];

function tokenDeclaration(name: string): string {
  const match = TOKENS_BODY.match(
    new RegExp(`--${name}:\\s*([^;]+);`)
  );
  expect(match, `--${name} must be declared in tokens.css`).not.toBeNull();
  return match![1].trim();
}

/** Resolves a token's value through var() alias chains to a literal. */
function resolveToken(name: string): string {
  const raw = tokenDeclaration(name);
  const reference = raw.match(/^var\((--[\w-]+)\)$/);
  return reference ? resolveToken(reference[1].slice(2)) : raw;
}

function sha256(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function parseHex(hex: string): [number, number, number] {
  const normalized = hex.replace(/^#/, "");
  return [
    parseInt(normalized.slice(0, 2), 16),
    parseInt(normalized.slice(2, 4), 16),
    parseInt(normalized.slice(4, 6), 16)
  ];
}

function relativeLuminance(hex: string): number {
  const [r, g, b] = parseHex(hex).map((channel) => {
    const s = channel / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrastRatio(foreground: string, background: string): number {
  const lighter = Math.max(relativeLuminance(foreground), relativeLuminance(background));
  const darker = Math.min(relativeLuminance(foreground), relativeLuminance(background));
  return (lighter + 0.05) / (darker + 0.05);
}

describe("semantic color roles", () => {
  const exactRoles: Record<string, string> = {
    "surface-canvas": "#090c12",
    "surface-panel": "#0f141d",
    "surface-raised": "#151c28",
    "surface-hover": "#1c2533",
    "border-subtle": "#263244",
    "border-strong": "#35445a",
    "text-primary": "#f4f7fb",
    "text-secondary": "#b7c0ce",
    "text-tertiary": "#7f8a9a",
    "interactive-primary": "#6d8eff",
    "interactive-primary-hover": "#87a4ff",
    "interactive-primary-pressed": "#587af2",
    "focus-ring-color": "#87a4ff",
    "status-success": "#45d483",
    "status-warning": "#f6c85f",
    "status-danger": "#ff5c7a",
    "status-info": "#52c7ea",
    "market-up": "#ff7a59",
    "market-down": "#2fc6a2",
    "market-flat": "#b7c0ce",
    "chart-primary-line": "#7c9cff",
    "chart-grid": "#263244",
    "chart-axis": "#7f8a9a",
    "chart-crosshair": "#7f8a9a",
    "chart-series-1": "#7c9cff",
    "chart-series-2": "#46c2b3",
    "chart-series-3": "#f3c969",
    "chart-series-4": "#d88cff",
    "chart-series-5": "#ff8a65",
    "chart-series-6": "#8fcb6a"
  };

  it("declares every semantic role with its exact contract value", () => {
    for (const [name, value] of Object.entries(exactRoles)) {
      expect(resolveToken(name), `--${name}`).toBe(value);
    }
  });

  it("lists the semantic groups in the leading token catalog", () => {
    const catalog = TOKENS_CSS.slice(0, TOKENS_CSS.indexOf(":root"));
    for (const group of [
      "Surfaces",
      "Borders",
      "Text",
      "Interaction",
      "Status",
      "China market",
      "Charts",
      "Typography",
      "Spacing",
      "Radius",
      "Shadow",
      "Layout",
      "Motion"
    ]) {
      expect(catalog.toLowerCase()).toContain(group.toLowerCase());
    }
  });
});

describe("dual-font runtime", () => {
  it("declares --font-sans and --font-mono with the required fallback chains", () => {
    const sans = tokenDeclaration("font-sans");
    expect(sans.startsWith('"Geist Sans"')).toBe(true);
    for (const fallback of [
      "PingFang SC",
      "Microsoft YaHei",
      "Noto Sans SC",
      "sans-serif"
    ]) {
      expect(sans, `--font-sans needs ${fallback}`).toContain(fallback);
    }

    expect(tokenDeclaration("font-mono")).toBe(
      '"Geist Mono", "SFMono-Regular", "Cascadia Mono", "Roboto Mono", Menlo, Monaco, Consolas, monospace'
    );
  });

  it("vendors exactly the two pinned Geist variable WOFF2 resources", () => {
    const files = readdirSync(PUBLIC_FONTS_DIR).filter((name) =>
      statSync(join(PUBLIC_FONTS_DIR, name)).isFile()
    );
    expect(files.sort()).toEqual([
      "Geist-Variable.woff2",
      "GeistMono-Variable.woff2"
    ]);
    expect(sha256(join(PUBLIC_FONTS_DIR, "Geist-Variable.woff2"))).toBe(
      "2ffebe993e969069a9789d15164b7715d42491b5835516c5e3b935d5f81b05f1"
    );
    expect(sha256(join(PUBLIC_FONTS_DIR, "GeistMono-Variable.woff2"))).toBe(
      "afaacc4c5fbba89d2ebf7a02dc4070208540874592a5504d57175782fe893101"
    );
  });

  it("declares exactly two @font-face rules for the product-facing families", () => {
    const faces = STYLES_CSS.match(/@font-face\s*{[^}]*}/g) ?? [];
    expect(faces).toHaveLength(2);
    const sans = faces.find((face) => face.includes('"Geist Sans"'));
    const mono = faces.find((face) => face.includes('"Geist Mono"'));
    expect(sans).toBeDefined();
    expect(mono).toBeDefined();
    for (const face of [sans!, mono!]) {
      expect(face).toContain('format("woff2-variations")');
      expect(face).toContain("font-weight: 100 900");
      expect(face).toContain("font-style: normal");
      expect(face).toContain("font-display: swap");
      expect(face).not.toContain("unicode-range");
      expect(face).not.toContain("font-feature-settings");
    }
    expect(sans!).toContain('url("/fonts/Geist-Variable.woff2")');
    expect(mono!).toContain('url("/fonts/GeistMono-Variable.woff2")');
  });

  it("preloads exactly the two @font-face resources in index.html", () => {
    const preloads = [
      ...INDEX_HTML.matchAll(
        /<link\s+rel="preload"\s+href="([^"]+)"\s+as="font"/g
      )
    ].map((match) => match[1]);
    expect(preloads.sort()).toEqual([
      "/fonts/Geist-Variable.woff2",
      "/fonts/GeistMono-Variable.woff2"
    ]);
    expect(preloads).toHaveLength(2);
    const srcs = [...STYLES_CSS.matchAll(/url\("([^"]+)"\)/g)].map(
      (match) => match[1]
    );
    for (const preload of preloads) {
      expect(srcs).toContain(preload);
    }
  });
});

describe("forbidden legacy tokens", () => {
  const LEGACY_PATTERNS: RegExp[] = [
    /--color-(?:void|carbon|obsidian|graphite|smoke|ash|fog|mist|bone|paper|acid-lime|pulse-green|coral-red|signal-teal|iris-violet|lavender)\b/,
    /--surface-(?:void|carbon|obsidian|slate)\b/,
    /--color-series-\d/,
    /--font-inter-variable\b/,
    /--font-display\b/,
    /--font-berkeley-mono\b/,
    /--feedback-accent-[\w-]+/,
    /--font-feature-settings-default\b/
  ];

  function* runtimeFiles(dir: string): Generator<string> {
    for (const name of readdirSync(dir)) {
      const full = join(dir, name);
      if (statSync(full).isDirectory()) {
        if (name === "__fixtures__") continue;
        yield* runtimeFiles(full);
      } else if (/\.(css|ts|tsx)$/.test(name) && !name.includes(".test.")) {
        yield full;
      }
    }
  }

  it("leaves no legacy declaration or consumer in runtime source", () => {
    const violations: string[] = [];
    for (const file of runtimeFiles(SRC_ROOT)) {
      const relative = file.slice(SRC_ROOT.length + 1);
      const content = file.endsWith(".css")
        ? stripCssComments(readFileSync(file, "utf8"))
        : readFileSync(file, "utf8");
      for (const pattern of LEGACY_PATTERNS) {
        if (pattern.test(content)) violations.push(`${relative}: ${pattern}`);
      }
    }
    expect(violations).toEqual([]);
  });

  it("keeps tokens.css the only :root token source", () => {
    expect(TOKENS_CSS.match(/:root\s*\{/g)).toHaveLength(1);
    const offenders: string[] = [];
    for (const file of runtimeFiles(SRC_ROOT)) {
      if (!file.endsWith(".css") || file.endsWith("tokens.css")) continue;
      if (/:root\s*\{/.test(stripCssComments(readFileSync(file, "utf8")))) {
        offenders.push(file.slice(SRC_ROOT.length + 1));
      }
    }
    expect(offenders).toEqual([]);
  });
});

describe("research-workstation type scale", () => {
  // Sizes are rem so they scale with the user's root font; each value equals
  // the documented px at the default 16px root font.
  const roles: Record<string, [string, string]> = {
    "page-title": ["2.25rem", "2.5rem"],
    "page-title-compact": ["1.75rem", "2.25rem"],
    "section-title": ["1.375rem", "1.75rem"],
    "card-title": ["1rem", "1.375rem"],
    "metric-hero": ["2rem", "2.25rem"],
    metric: ["1.5rem", "1.875rem"],
    body: ["0.9375rem", "1.375rem"],
    dense: ["0.8125rem", "1.25rem"],
    label: ["0.75rem", "1rem"],
    meta: ["0.6875rem", "1rem"],
    "chart-axis": ["0.6875rem", "1rem"]
  };

  it("declares every role size and its --leading-* pair exactly", () => {
    for (const [role, [size, leading]] of Object.entries(roles)) {
      expect(resolveToken(`text-${role}`), `--text-${role}`).toBe(size);
      expect(resolveToken(`leading-${role}`), `--leading-${role}`).toBe(leading);
    }
  });

  it("declares the four card data rungs and card-title pair", () => {
    expect(resolveToken("card-meta-size")).toBe("0.6875rem");
    expect(resolveToken("leading-body-card")).toBe("1.25rem");
    expect(resolveToken("card-body-size")).toBe("0.8125rem");
    expect(resolveToken("card-emphasis-size")).toBe("1.5rem");
    expect(resolveToken("leading-emphasis")).toBe("1.875rem");
    expect(resolveToken("card-display-size")).toBe("2rem");
    expect(resolveToken("leading-display-card")).toBe("2.25rem");
  });

  it("retains the tracking contract", () => {
    expect(tokenDeclaration("tracking-meta")).toBe("0.06em");
    expect(tokenDeclaration("tracking-numeral")).toBe("-0.01em");
    expect(tokenDeclaration("tracking-title")).toBe("-0.035em");
  });

  it("routes every line-height in the global stylesheet through a --leading-* token", () => {
    const bodies = stripCssComments(STYLES_CSS);
    const literals = [
      ...bodies.matchAll(/line-height:\s*([^;]+);/g)
    ].map((match) => match[1].trim());
    expect(literals.length).toBeGreaterThan(0);
    for (const value of literals) {
      expect(value, "line-height must use a --leading-* token").toMatch(
        /^var\(--leading-[\w-]+\)$/
      );
    }
  });
});

describe("component aliases and states", () => {
  it("rebases card primitives onto the semantic roles", () => {
    expect(tokenDeclaration("card-bg")).toBe("var(--surface-raised)");
    expect(tokenDeclaration("panel-bg")).toBe("var(--surface-panel)");
    expect(tokenDeclaration("card-border-color")).toBe("var(--border-subtle)");
    expect(tokenDeclaration("card-radius")).toBe("var(--radius-cards)");
    expect(tokenDeclaration("card-shadow")).toBe("none");
  });

  it("keeps the three-variant button contract on semantic tokens", () => {
    const css = stripCssComments(STYLES_CSS);
    const primary = css.match(/\.button-primary\s*{[^}]*}/)![0];
    expect(primary).toContain("var(--interactive-primary)");
    expect(primary).toContain("var(--surface-canvas)");
    const secondary = css.match(/\.button-secondary\s*{[^}]*}/)![0];
    expect(secondary).toContain("var(--border-subtle)");
    expect(secondary).toContain("var(--text-secondary)");
    const pressed = css.match(
      /\.button-secondary\[aria-pressed="true"\]\s*{[^}]*}/
    )![0];
    expect(pressed).toContain("var(--surface-hover)");
    expect(pressed).toContain("var(--border-strong)");
    expect(pressed).toContain("var(--text-primary)");
  });

  it("promotes readable Command Palette metadata to secondary on hover/active", () => {
    const css = stripCssComments(STYLES_CSS);
    const promotion = css.match(
      /\.command-palette-row:hover \.command-palette-row-kind,[^{]*\.command-palette-row-active \.command-palette-row-kind\s*{[^}]*}/
    );
    expect(promotion).not.toBeNull();
    expect(promotion![0]).toContain("var(--text-secondary)");
  });

  it("keeps the active-row foreground/background pair at WCAG AA contrast", () => {
    const raised = resolveToken("surface-hover");
    expect(raised).toBe("#1c2533");
    // --text-tertiary on --surface-hover is 4.41:1 (below AA), which is why
    // readable metadata MUST promote to --text-secondary (8.40:1).
    expect(contrastRatio(resolveToken("text-tertiary"), raised)).toBeLessThan(4.5);
    expect(contrastRatio(resolveToken("text-secondary"), raised)).toBeGreaterThanOrEqual(4.5);
  });

  it("binds compact-list rows to the shared 20px leading", () => {
    const css = stripCssComments(STYLES_CSS);
    const dt = css.match(/\.compact-list dt\s*{[^}]*}/)![0];
    const dd = css.match(/\.compact-list dd\s*{[^}]*}/)![0];
    expect(dt).toContain("var(--leading-body-card)");
    expect(dd).toContain("var(--leading-body-card)");
  });
});

describe("layout and control tokens", () => {
  it("resolves the research rhythm tokens onto the spacing ladder", () => {
    expect(resolveToken("section-gap")).toBe("3rem");
    expect(resolveToken("section-gap-compact")).toBe("2rem");
    expect(resolveToken("group-gap")).toBe("1.5rem");
    expect(resolveToken("heading-content-gap")).toBe("1.5rem");
    expect(resolveToken("page-gutter-wide")).toBe("2rem");
    expect(resolveToken("page-gutter-medium")).toBe("1.5rem");
    expect(resolveToken("page-gutter-compact")).toBe("1rem");
  });

  it("keeps the canonical page width and routes card padding through the ladder", () => {
    expect(tokenDeclaration("page-max-width")).toBe("1200px");
    expect(resolveToken("card-padding")).toBe("1.5rem");
    expect(resolveToken("card-padding-x")).toBe("1.5rem");
    expect(resolveToken("card-padding-y")).toBe("1.5rem");
    expect(resolveToken("card-padding-compact")).toBe("1rem");
  });

  it("declares the control minimum heights", () => {
    expect(tokenDeclaration("control-min-height")).toBe("2.25rem");
    expect(tokenDeclaration("control-touch-size")).toBe("2.75rem");
  });

  it("keeps spacing primitives in rem equivalents of the documented px", () => {
    for (const [name, value] of [
      ["spacing-unit", "0.25rem"],
      ["spacing-4", "0.25rem"],
      ["spacing-8", "0.5rem"],
      ["spacing-12", "0.75rem"],
      ["spacing-16", "1rem"],
      ["spacing-20", "1.25rem"],
      ["spacing-24", "1.5rem"],
      ["spacing-32", "2rem"],
      ["spacing-48", "3rem"],
      ["spacing-96", "6rem"]
    ] as Array<[string, string]>) {
      expect(tokenDeclaration(name), `--${name}`).toBe(value);
    }
  });

  it("declares no custom properties inside media queries (responsive rules select tokens)", () => {
    const mediaBlocks = STYLES_CSS.match(/@media[^{]+\{(?:[^{}]*\{[^}]*\})*[^{}]*\}/g) ?? [];
    expect(mediaBlocks.length).toBeGreaterThan(0);
    const offenders = mediaBlocks
      .flatMap((block) => [...block.matchAll(/--[\w-]+\s*:/g)].map(() => block))
      .filter(Boolean);
    expect(offenders).toEqual([]);
  });

  it("gives controls the touch minimum under pointer:coarse", () => {
    const coarseBlocks = STYLES_CSS.match(
      /@media \(pointer: coarse\)\s*\{[\s\S]*?\n\}/g
    ) ?? [];
    expect(coarseBlocks.length).toBe(1);
    const block = coarseBlocks[0];
    for (const selector of [
      ".button-primary",
      ".button-secondary",
      ".button-tertiary",
      ".backtest-run-form input",
      ".stability-select select"
    ]) {
      expect(block).toContain(selector);
    }
    expect(block).toContain("var(--control-touch-size)");
  });

  it("declares the dynamic viewport sizes with a vh fallback", () => {
    const shellRule = STYLES_CSS.match(/\.app-shell\s*\{[^}]*\}/)![0];
    expect(shellRule).toContain("min-height: 100vh;");
    expect(shellRule).toContain("min-height: 100dvh;");
    expect(shellRule.indexOf("min-height: 100vh;")).toBeLessThan(
      shellRule.indexOf("min-height: 100dvh;")
    );

    const dialogRule = STYLES_CSS.match(/\.command-palette-dialog\s*\{[^}]*\}/)![0];
    expect(dialogRule).toContain("max-height: 60vh;");
    expect(dialogRule).toContain("max-height: 60dvh;");
  });
});

describe("design-system stylelint guard", () => {
  function stylelintConfig(): Record<string, unknown> {
    const config = JSON.parse(
      readFileSync(join(WEB_ROOT, ".stylelintrc.json"), "utf8")
    ) as { ignoreFiles?: string[] } & Record<string, unknown>;
    delete config.ignoreFiles;
    return config;
  }

  it("rejects the negative legacy fixture", async () => {
    const fixture = readFileSync(
      join(SRC_ROOT, "styles/__fixtures__/legacy.fixture.css"),
      "utf8"
    );
    const lint = await stylelint.lint({
      code: fixture,
      config: stylelintConfig(),
      configBasedir: WEB_ROOT
    });
    expect(lint.errored).toBe(true);
    expect(lint.results[0].warnings.length).toBeGreaterThanOrEqual(5);
    const rules = new Set(lint.results[0].warnings.map((w) => w.rule));
    expect(rules).toContain("declaration-property-value-disallowed-list");
  });

  it("passes the conforming production stylesheet", async () => {
    const lint = await stylelint.lint({
      code: STYLES_CSS,
      codeFilename: "src/styles.css",
      config: stylelintConfig(),
      configBasedir: WEB_ROOT
    });
    expect(lint.errored).toBe(false);
    expect(lint.results[0].warnings).toEqual([]);
  });
});

describe("generated token documentation", () => {
  it("is unignored and lists every canonical token", () => {
    expect(GITIGNORE).toMatch(/^docs\/\*\s*$/m);
    expect(GITIGNORE).toMatch(/^!docs\/tokens\.md\s*$/m);

    const docs = readFileSync(join(WEB_ROOT, "../../docs/tokens.md"), "utf8");
    const names = [...TOKENS_BODY.matchAll(/(--[\w-]+):/g)].map(
      (match) => match[1]
    );
    expect(names.length).toBeGreaterThan(40);
    for (const name of names) {
      expect(docs, `${name} must be documented`).toContain(name);
    }
  });
});
