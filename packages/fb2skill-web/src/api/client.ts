import type {
  ConvertRequestFields,
  ConvertResponse,
  OntologiesResponse,
  SkillListResponse,
} from "../types/api";

const apiBase = ""; // same-origin in dev (vite proxy) and prod (static mount)

class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(`HTTP ${status}: ${detail}`);
  }
}

async function unwrap<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
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

export { ApiError };
