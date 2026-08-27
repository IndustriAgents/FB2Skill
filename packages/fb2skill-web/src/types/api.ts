// Mirror of fb2skill-rest pydantic schemas.

export interface SkillTtl {
  name: string;
  ttl: string;
}

export interface Failure {
  name: string;
  error: string;
}

export interface ConvertResponse {
  skills: SkillTtl[];
  warnings: string[];
  failures: Failure[];
}

export interface SkillListResponse {
  skills: string[];
  warnings: string[];
}

export interface ConvertRequestFields {
  endpoint_url: string;
  base_iri: string;
  resource: string;
  namespace_index?: number;
  only?: string;
  opcua_xml_rel_path?: string;
  ontology?: string;
}

export interface OntologyGroup {
  id: string;
  label: string;
  files: string[];
}

export interface OntologyInfo {
  id: string;
  label: string;
  version: string;
  license?: string | null;
  baseIri?: string | null;
  source?: string | null;
  groups: OntologyGroup[];
}

export interface OntologiesResponse {
  ontologies: OntologyInfo[];
}

// --- GraphDB integration (schemas/graphdb.py) ---

export interface GraphDBConnection {
  base_url: string;
  repository: string;
  username?: string | null;
  password?: string | null;
  timeout_s?: number;
}

export interface RepositoryInfo {
  id: string;
  title?: string | null;
}

export interface TestConnectionResponse {
  ok: boolean;
  protocol?: string | null;
  repository_found: boolean;
  repository_healthy: boolean;
  repositories: RepositoryInfo[];
  message: string;
}

export interface GraphListResponse {
  graphs: string[];
}

export interface OntologyFileRef {
  ontology_id: string;
  file_path: string;
}

export type PushMode = "append" | "replace";

export interface PushItem {
  name: string;
  graph?: string | null;
  ttl?: string;
  ontology_file?: OntologyFileRef;
}

export interface PushRequest {
  connection: GraphDBConnection;
  mode: PushMode;
  items: PushItem[];
}

export interface PushItemResult {
  name: string;
  graph?: string | null;
  ok: boolean;
  triples?: number | null;
  error?: string | null;
}

export interface PushResponse {
  results: PushItemResult[];
}

export interface ExportRequest {
  connection: GraphDBConnection;
  graph?: string | null;
  infer?: boolean;
}

// --- Server-side downloads (schemas/export.py) ---

export interface ExportZipRequest {
  skills: SkillTtl[];
  include_ontology?: OntologyFileRef[];
}
