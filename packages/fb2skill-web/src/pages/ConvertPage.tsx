import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

import { ApiError, convertProject } from "../api/client";
import type { ConvertResponse } from "../types/api";
import TtlViewer from "../components/TtlViewer";
import ZipUploader from "../components/ZipUploader";

interface FormState {
  endpoint_url: string;
  base_iri: string;
  resource: string;
  namespace_index: number;
  only: string;
  opcua_xml_rel_path: string;
  ontology: string;
}

const DEFAULTS: FormState = {
  endpoint_url: "opc.tcp://host.docker.internal:4840",
  base_iri: "http://www.ltu.se/aut/ontologies/FESTO_DS_skills",
  resource: "soft_dPAC_PLC1",
  namespace_index: 2,
  only: "",
  opcua_xml_rel_path: "",
  ontology: "maestro",
};

export default function ConvertPage() {
  const location = useLocation();
  const handoff = location.state as { only?: string } | null;

  const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState<FormState>(DEFAULTS);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<ConvertResponse | null>(null);
  const [activeSkill, setActiveSkill] = useState<string | null>(null);

  useEffect(() => {
    if (handoff?.only) setForm((f) => ({ ...f, only: handoff.only! }));
  }, [handoff]);

  async function submit() {
    if (!file) {
      setErr("Pick a zip first");
      return;
    }
    setBusy(true);
    setErr(null);
    setResult(null);
    try {
      const r = await convertProject(file, form);
      setResult(r);
      setActiveSkill(r.skills[0]?.name ?? null);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  function download(name: string, ttl: string) {
    const blob = new Blob([ttl], { type: "text/turtle" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${name}.ttl`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadAll() {
    if (!result) return;
    result.skills.forEach((s) => download(s.name, s.ttl));
  }

  const activeTtl = result?.skills.find((s) => s.name === activeSkill)?.ttl;

  return (
    <div>
      <div className="view-head">
        <div>
          <h1>
            <em>Convert</em> project to skills
          </h1>
          <p className="view-sub">
            Upload an IEC 61499 project zip and render one skill TTL per
            detected <code>BasicSKILL</code> function block, in the CaSkMan or
            MAESTRO vocabulary.
          </p>
        </div>
        <div className="view-actions" style={{ display: "flex", gap: 8 }}>
          {result && result.skills.length > 0 && (
            <button type="button" className="btn" onClick={downloadAll}>
              Download all .ttl
            </button>
          )}
          <button
            type="button"
            className="btn is-primary"
            onClick={submit}
            disabled={busy || !file}
          >
            {busy ? "Converting…" : "Convert"}
          </button>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1.2fr)",
          gap: 18,
        }}
      >
        <div className="card">
          <div className="card-head">
            <h3>Source &amp; parameters</h3>
            <span className="card-meta">POST /convert</span>
          </div>
          <div
            className="card-body"
            style={{ display: "flex", flexDirection: "column", gap: 16 }}
          >
            <ZipUploader onFile={setFile} file={file} />

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 12,
              }}
            >
              <Field
                label="OPC UA endpoint URL"
                value={form.endpoint_url}
                onChange={(v) => setForm({ ...form, endpoint_url: v })}
                wide
              />
              <Field
                label="Resource name"
                value={form.resource}
                onChange={(v) => setForm({ ...form, resource: v })}
              />
              <Field
                label="Namespace index"
                value={String(form.namespace_index)}
                onChange={(v) =>
                  setForm({ ...form, namespace_index: parseInt(v) || 2 })
                }
              />
              <Field
                label="Base IRI"
                value={form.base_iri}
                onChange={(v) => setForm({ ...form, base_iri: v })}
                wide
              />
              <SelectField
                label="Target ontology"
                value={form.ontology}
                onChange={(v) => setForm({ ...form, ontology: v })}
                options={[
                  { value: "maestro", label: "MAESTRO (default)" },
                  { value: "caskman", label: "CaSkMan" },
                ]}
              />
              <Field
                label="Only (CSV filter)"
                value={form.only}
                onChange={(v) => setForm({ ...form, only: v })}
                placeholder="skLoad,skPush"
              />
              <Field
                label="opcua_xml_rel_path (optional)"
                value={form.opcua_xml_rel_path}
                onChange={(v) =>
                  setForm({ ...form, opcua_xml_rel_path: v })
                }
                placeholder="auto-detect under bin/Deploy/"
              />
            </div>

            {err && (
              <div
                className="text-mono"
                style={{
                  fontSize: 12,
                  color: "var(--alert)",
                  background: "rgba(255,87,96,0.06)",
                  border: "1px solid rgba(255,87,96,0.3)",
                  borderRadius: 8,
                  padding: "8px 12px",
                }}
              >
                {err}
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-head">
            <h3>
              {result
                ? `Rendered skills (${result.skills.length})`
                : "Rendered skills"}
            </h3>
            {result && result.failures.length > 0 && (
              <span className="pill is-alert">
                {result.failures.length} failed
              </span>
            )}
            {!result && <span className="card-meta">awaiting input</span>}
          </div>
          <div className="card-body flush">
            {!result ? (
              <div
                style={{
                  padding: "60px 24px",
                  textAlign: "center",
                  color: "var(--cream-faint)",
                  fontSize: 13,
                }}
              >
                Conversion output will appear here.
              </div>
            ) : (
              <>
                {result.skills.length === 0 ? (
                  <div
                    style={{
                      padding: "40px 24px",
                      textAlign: "center",
                      color: "var(--cream-dim)",
                      fontSize: 13,
                    }}
                  >
                    No BasicSKILL function blocks were rendered.
                  </div>
                ) : (
                  <>
                    <div
                      className="tabs"
                      style={{ padding: "0 16px", borderBottom: "1px solid var(--line)" }}
                    >
                      {result.skills.map((s) => (
                        <button
                          key={s.name}
                          type="button"
                          onClick={() => setActiveSkill(s.name)}
                          className={`tab${activeSkill === s.name ? " is-active" : ""}`}
                        >
                          {s.name}
                        </button>
                      ))}
                    </div>
                    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
                      {activeTtl && <TtlViewer ttl={activeTtl} maxHeight="58vh" />}
                      {activeSkill && activeTtl && (
                        <div style={{ display: "flex", justifyContent: "flex-end" }}>
                          <button
                            type="button"
                            className="btn is-sm"
                            onClick={() => download(activeSkill, activeTtl)}
                          >
                            Download {activeSkill}.ttl
                          </button>
                        </div>
                      )}
                    </div>
                  </>
                )}
                {result.failures.length > 0 && (
                  <details
                    style={{
                      borderTop: "1px solid var(--line)",
                      padding: "12px 18px",
                      fontSize: 12,
                      color: "var(--cream-dim)",
                    }}
                  >
                    <summary style={{ cursor: "pointer" }}>
                      Failures ({result.failures.length})
                    </summary>
                    <ul style={{ marginTop: 8, fontSize: 11.5, listStyle: "none", padding: 0 }}>
                      {result.failures.map((f) => (
                        <li key={f.name} style={{ padding: "4px 0" }}>
                          <span style={{ color: "var(--accent)", fontFamily: "var(--mono)" }}>
                            {f.name}:
                          </span>{" "}
                          {f.error}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
                {result.warnings.length > 0 && (
                  <ul
                    style={{
                      borderTop: "1px solid var(--line)",
                      padding: "10px 18px",
                      margin: 0,
                      listStyle: "none",
                      fontSize: 11.5,
                      color: "var(--warn)",
                      fontFamily: "var(--mono)",
                    }}
                  >
                    {result.warnings.map((w, i) => (
                      <li key={i}>⚠ {w}</li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  wide,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  wide?: boolean;
}) {
  return (
    <div className="field" style={wide ? { gridColumn: "1 / -1" } : undefined}>
      <label>{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
  wide,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  wide?: boolean;
}) {
  return (
    <div className="field" style={wide ? { gridColumn: "1 / -1" } : undefined}>
      <label>{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
