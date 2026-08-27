import type {
  ConvertRequestFields,
  ConvertResponse,
  ExportRequest,
  ExportZipRequest,
  GraphDBConnection,
  GraphListResponse,
  OntologiesResponse,
  PushRequest,
  PushResponse,
  SkillListResponse,
  TestConnectionResponse,
} from "../types/api";

const apiBase = ""; // same-origin in dev (vite proxy) and prod (static mount)

class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(`HTTP ${status}: ${detail}`);
  }
}

/**
 * Render a FastAPI `detail` payload as a single human-readable line.
 *
 * `detail` is a plain string for `HTTPException`, but a list of `{loc, msg}`
 * objects for 422 request-validation errors -- stringifying that list yields
 * "[object Object]" and hides the actual cause (e.g. a GraphDB URL entered
 * without an http:// scheme).
 */
function formatDetail(detail: unknown): string | null {
  if (typeof detail === "string") return detail.trim() || null;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((entry) => {
        if (typeof entry === "string") return entry;
        const { msg, loc } = (entry ?? {}) as { msg?: unknown; loc?: unknown };
        if (typeof msg !== "string") return null;
        // Drop the leading "body"/"query" segment; keep the field path.
        const field = Array.isArray(loc)
          ? loc.filter((s) => s !== "body" && s !== "query").join(".")
          : "";
        return field ? `${field}: ${msg}` : msg;
      })
      .filter((s): s is string => Boolean(s));
    if (parts.length > 0) return parts.join("; ");
  }
  return null;
}

async function errorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return formatDetail(body?.detail) ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

async function unwrap<T>(res: Response): Promise<T> {
  if (!res.ok) throw new ApiError(res.status, await errorDetail(res));
  return res.json() as Promise<T>;
}

export async function health(): Promise<{ status: string }> {
  return unwrap(await fetch(`${apiBase}/health`));
}

export async function discoverSkills(
  zip: File,
  opcuaXmlRelPath?: string
): Promise<SkillListResponse> {
  const fd = new FormData();
  fd.append("project_zip", zip, zip.name || "project.zip");
  if (opcuaXmlRelPath) fd.append("opcua_xml_rel_path", opcuaXmlRelPath);
  return unwrap(
    await fetch(`${apiBase}/skills/discover`, { method: "POST", body: fd })
  );
}

export async function convertProject(
  zip: File,
  fields: ConvertRequestFields
): Promise<ConvertResponse> {
  const fd = new FormData();
  fd.append("project_zip", zip, zip.name || "project.zip");
  fd.append("endpoint_url", fields.endpoint_url);
  fd.append("base_iri", fields.base_iri);
  fd.append("resource", fields.resource);
  fd.append("namespace_index", String(fields.namespace_index ?? 2));
  if (fields.only) fd.append("only", fields.only);
  if (fields.opcua_xml_rel_path) fd.append("opcua_xml_rel_path", fields.opcua_xml_rel_path);
  fd.append("ontology", fields.ontology ?? "maestro");
  return unwrap(
    await fetch(`${apiBase}/convert`, { method: "POST", body: fd })
  );
}

export async function fetchOntology(): Promise<string> {
  const res = await fetch(`${apiBase}/ontology`);
  if (!res.ok) throw new ApiError(res.status, res.statusText);
  return res.text();
}

export async function fetchOntologies(): Promise<OntologiesResponse> {
  return unwrap(await fetch(`${apiBase}/ontologies`));
}

export async function fetchOntologyFile(
  ontologyId: string,
  path: string
): Promise<string> {
  const res = await fetch(`${apiBase}/ontologies/${ontologyId}/files/${path}`);
  if (!res.ok) throw new ApiError(res.status, res.statusText);
  return res.text();
}

// --- File downloads --------------------------------------------------------

export interface DownloadedFile {
  blob: Blob;
  filename: string;
}

function filenameFrom(res: Response, fallback: string): string {
  const cd = res.headers.get("content-disposition") ?? "";
  const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd);
  return m ? decodeURIComponent(m[1]) : fallback;
}

async function unwrapFile(res: Response, fallback: string): Promise<DownloadedFile> {
  if (!res.ok) throw new ApiError(res.status, await errorDetail(res));
  return { blob: await res.blob(), filename: filenameFrom(res, fallback) };
}

/** Trigger a browser download for an in-memory blob. */
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function postJson(path: string, body: unknown): Promise<Response> {
  return fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function exportSkill(name: string, ttl: string): Promise<DownloadedFile> {
  return unwrapFile(await postJson("/export/skill", { name, ttl }), `${name}.ttl`);
}

export async function exportSkillsZip(req: ExportZipRequest): Promise<DownloadedFile> {
  return unwrapFile(await postJson("/export/skills.zip", req), "skills.zip");
}

// --- GraphDB ---------------------------------------------------------------

export async function testGraphDb(
  connection: GraphDBConnection
): Promise<TestConnectionResponse> {
  return unwrap(await postJson("/graphdb/test", { connection }));
}

export async function listGraphDbGraphs(
  connection: GraphDBConnection
): Promise<GraphListResponse> {
  return unwrap(await postJson("/graphdb/graphs", { connection }));
}

export async function pushToGraphDb(req: PushRequest): Promise<PushResponse> {
  return unwrap(await postJson("/graphdb/push", req));
}

export async function exportFromGraphDb(req: ExportRequest): Promise<DownloadedFile> {
  return unwrapFile(
    await postJson("/graphdb/export", req),
    `${req.connection.repository}.ttl`
  );
}

export { ApiError };
