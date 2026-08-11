import { build } from "vite";
import react from "@vitejs/plugin-react";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { gzipSync } from "node:zlib";

const runtimeEntry = `
import React from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams
} from "react-router-dom";

function RuntimePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const params = useParams();
  return (
    <>
      <Link to={location.pathname} onClick={() => navigate(params.id ?? "/")}>
        runtime
      </Link>
      <NavLink to={location.pathname}>navigation</NavLink>
    </>
  );
}

function RuntimeApp() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/:id?" element={<RuntimePage />} />
      </Routes>
    </BrowserRouter>
  );
}

createRoot(document.createElement("div")).render(<RuntimeApp />);
`;

function manualChunks(id) {
  if (/[/\\]node_modules[/\\](react|react-dom|scheduler)[/\\]/.test(id)) {
    return "react-vendor";
  }
  if (/[/\\]node_modules[/\\](?:react-router|@remix-run[/\\]router)[/\\]/.test(id)) {
    return "router";
  }
}

function measureChunk(chunk) {
  return {
    rawBytes: Buffer.byteLength(chunk.code),
    gzipBytes: gzipSync(chunk.code).length
  };
}

export async function measureIsolatedRuntime(webRoot) {
  const fixtureDirectory = await mkdtemp(join(tmpdir(), "vela-runtime-baseline-"));
  const entry = join(fixtureDirectory, "entry.jsx");
  await writeFile(entry, runtimeEntry);

  try {
    const result = await build({
      root: fixtureDirectory,
      mode: "production",
      configFile: false,
      logLevel: "silent",
      plugins: [react()],
      resolve: {
        alias: {
          react: join(webRoot, "node_modules/react"),
          "react-dom": join(webRoot, "node_modules/react-dom"),
          "react-router-dom": join(webRoot, "node_modules/react-router-dom")
        }
      },
      build: {
        write: false,
        rollupOptions: {
          input: entry,
          output: { manualChunks }
        }
      }
    });
    const chunks = result.output.filter((output) => output.type === "chunk");
    const reactVendor = chunks.find((chunk) => chunk.name === "react-vendor");
    const router = chunks.find((chunk) => chunk.name === "router");
    if (!reactVendor || !router) {
      throw new Error("Isolated runtime build did not emit React and Router chunks.");
    }

    return {
      reactVendor: measureChunk(reactVendor),
      router: measureChunk(router)
    };
  } finally {
    await rm(fixtureDirectory, { recursive: true, force: true });
  }
}
