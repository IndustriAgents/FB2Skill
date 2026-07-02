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
