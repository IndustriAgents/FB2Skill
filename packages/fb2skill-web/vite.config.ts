import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const API_TARGET = "http://127.0.0.1:8000";

// API prefixes proxied to FastAPI in dev. Some of them (`/graphdb`,
// `/ontology`) are also client-side SPA routes, so a browser navigation to
// them — a deep link or a plain page reload — would otherwise be answered by
// the backend (stale `dist/index.html`, or raw Turtle) instead of the dev SPA.
const API_PREFIXES = [
  "/health",
  "/convert",
  "/skills",
  "/ontology",
  "/ontologies",
  "/graphdb",
  "/export",
  "/openapi.json",
];

/** Structural subset of `http.IncomingMessage` (avoids a @types/node dep). */
interface ProxyRequest {
  method?: string;
  headers: { accept?: string };
}

/**
 * Let document navigations fall through to Vite's SPA handling.
 *
 * `fetch()` from the app sends a wildcard Accept header, while a top-level
 * navigation sends `Accept: text/html,...` — so this only diverts page loads.
 */
function spaBypass(req: ProxyRequest): string | undefined {
  const accept = req.headers.accept ?? "";
  if (req.method === "GET" && accept.includes("text/html")) return "/index.html";
  return undefined;
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      API_PREFIXES.map((p) => [p, { target: API_TARGET, bypass: spaBypass }])
    ),
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
