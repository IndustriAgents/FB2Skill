import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      // In dev, proxy API calls to the FastAPI backend so the SPA can use
      // relative URLs (`/convert`, `/ontology`, etc.) without CORS headaches.
      "/health": "http://127.0.0.1:8000",
      "/convert": "http://127.0.0.1:8000",
      "/skills": "http://127.0.0.1:8000",
      "/ontology": "http://127.0.0.1:8000",
      "/ontologies": "http://127.0.0.1:8000",
      "/openapi.json": "http://127.0.0.1:8000",
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
