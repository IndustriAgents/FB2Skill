import { useState } from "react";

import { ApiError, exportFromGraphDb, listGraphDbGraphs, saveBlob } from "../api/client";
import { useGraphDb } from "../state/graphdb";

const WHOLE_REPO = "";

export default function GraphDbPage() {
  const gdb = useGraphDb();
  const c = gdb.connection;

  const [graphs, setGraphs] = useState<string[] | null>(null);
  const [graphsErr, setGraphsErr] = useState<string | null>(null);
  const [exportGraph, setExportGraph] = useState<string>(WHOLE_REPO);
  const [infer, setInfer] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportErr, setExportErr] = useState<string | null>(null);

  async function refreshGraphs() {
    setGraphsErr(null);
    try {
      const r = await listGraphDbGraphs(gdb.toConnection());
      setGraphs(r.graphs);
    } catch (e) {
      setGraphs(null);
      setGraphsErr(e instanceof ApiError ? e.message : String(e));
    }
  }

  async function doExport() {
    setExporting(true);
    setExportErr(null);
    try {
      const f = await exportFromGraphDb({
        connection: gdb.toConnection(),
        graph: exportGraph === WHOLE_REPO ? null : exportGraph,
        infer,
      });
      saveBlob(f.blob, f.filename);
    } catch (e) {
      setExportErr(e instanceof ApiError ? e.message : String(e));
    } finally {
      setExporting(false);
    }
  }

  const statusPill =
    gdb.status === "ok" ? (
      <span className="pill is-ok">connected</span>
    ) : gdb.status === "error" ? (
      <span className="pill is-alert">error</span>
    ) : gdb.status === "untested" ? (
      <span className="pill is-accent">untested</span>
    ) : (
      <span className="pill">not configured</span>
    );

  return (
    <div>
      <div className="view-head">
        <div>
          <h1>
            <em>GraphDB</em> connection
          </h1>
          <p className="view-sub">
            Connect to an Ontotext GraphDB repository to push rendered skills and
            ontologies directly, or download Turtle back out of a named graph.
            Credentials are sent with each request and never stored on the server.
          </p>
        </div>
        <div className="view-actions" style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {statusPill}
          <button
            type="button"
            className="btn is-primary"
            onClick={() => void gdb.test()}
            disabled={!gdb.configured || gdb.testing}
          >
            {gdb.testing ? "Testing…" : "Test connection"}
          </button>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1.2fr) minmax(0, 1fr)",
          gap: 18,
          alignItems: "start",
        }}
      >
        {/* Connection */}
        <div className="card">
          <div className="card-head">
            <h3>Connection</h3>
            <span className="card-meta">POST /graphdb/test</span>
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <Field
                label="GraphDB URL"
                value={c.base_url}
                onChange={(v) => gdb.setConnection({ base_url: v })}
                placeholder="http://localhost:7200"
                wide
              />
              <Field
                label="Repository id"
                value={c.repository}
                onChange={(v) => gdb.setConnection({ repository: v })}
                placeholder="fb2skill"
                wide
              />
              <Field
                label="Username (optional)"
                value={c.username}
                onChange={(v) => gdb.setConnection({ username: v })}
              />
              <Field
                label="Password"
                value={c.password}
                onChange={(v) => gdb.setConnection({ password: v })}
                type="password"
              />
              <label
                style={{
                  gridColumn: "1 / -1",
                  display: "flex",
                  gap: 8,
                  alignItems: "center",
                  fontSize: 12,
                  color: "var(--cream-dim)",
                }}
              >
                <input
                  type="checkbox"
                  checked={c.remember_password}
                  onChange={(e) => gdb.setConnection({ remember_password: e.target.checked })}
                />
                Keep password for this browser session
              </label>
            </div>

            {gdb.lastMessage && (
              <div
                className="text-mono"
                style={{
                  fontSize: 12,
                  color: gdb.status === "ok" ? "var(--ok)" : "var(--alert)",
                  background:
                    gdb.status === "ok" ? "rgba(136,206,2,0.06)" : "rgba(255,87,96,0.06)",
                  border: `1px solid ${
                    gdb.status === "ok" ? "rgba(136,206,2,0.3)" : "rgba(255,87,96,0.3)"
                  }`,
                  borderRadius: 8,
                  padding: "8px 12px",
                }}
              >
                {gdb.lastMessage}
                {gdb.lastTest?.protocol && (
                  <span style={{ color: "var(--cream-faint)" }}>
                    {" "}
                    · RDF4J protocol {gdb.lastTest.protocol}
                  </span>
                )}
              </div>
            )}

            {gdb.lastTest && gdb.lastTest.repositories.length > 0 && (
              <div>
                <div
                  style={{
                    fontSize: 10.5,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    color: "var(--cream-faint)",
                    marginBottom: 6,
                  }}
                >
                  Repositories on server
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {gdb.lastTest.repositories.map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      className={`pill${r.id === c.repository ? " is-accent" : ""}`}
                      style={{ cursor: "pointer" }}
                      title={r.title ?? r.id}
                      onClick={() => gdb.setConnection({ repository: r.id })}
                    >
                      {r.id}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {/* Upload settings */}
          <div className="card">
            <div className="card-head">
              <h3>Upload settings</h3>
              <span className="card-meta">POST /graphdb/push</span>
            </div>
            <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <Field
                label="Named graph template ({name} = skill name; empty = default graph)"
                value={gdb.graphTemplate}
                onChange={gdb.setGraphTemplate}
                placeholder="urn:fb2skill:skill:{name}"
                wide
              />
              <div className="field">
                <label>Mode</label>
                <div className="tabs" style={{ borderBottom: "none" }}>
                  <button
                    type="button"
                    className={`tab${gdb.mode === "append" ? " is-active" : ""}`}
                    onClick={() => gdb.setMode("append")}
                    title="Add triples; existing statements are kept"
                  >
                    Append
                  </button>
                  <button
                    type="button"
                    className={`tab${gdb.mode === "replace" ? " is-active" : ""}`}
                    onClick={() => gdb.setMode("replace")}
                    title="Clear the target graph first, then upload"
                  >
                    Replace
                  </button>
                </div>
                <div style={{ fontSize: 11.5, color: "var(--cream-faint)", marginTop: 4 }}>
                  {gdb.mode === "append"
                    ? "Triples are added to the target graph. Re-pushing identical data is a no-op."
                    : "The target graph is cleared before upload. With an empty template this clears the default graph."}
                </div>
              </div>
            </div>
          </div>

          {/* Export */}
          <div className="card">
            <div className="card-head">
              <h3>Download from GraphDB</h3>
              <span className="card-meta">POST /graphdb/export</span>
            </div>
            <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div className="field">
                <label>Graph</label>
                <div style={{ display: "flex", gap: 8 }}>
                  <select
                    value={exportGraph}
                    onChange={(e) => setExportGraph(e.target.value)}
                    style={{ flex: 1 }}
                  >
                    <option value={WHOLE_REPO}>Whole repository</option>
                    {graphs?.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="btn is-sm"
                    onClick={refreshGraphs}
                    disabled={!gdb.configured}
                  >
                    {graphs ? "Refresh graphs" : "Load graphs"}
                  </button>
                </div>
                {graphs && graphs.length === 0 && (
                  <div style={{ fontSize: 11.5, color: "var(--cream-faint)", marginTop: 4 }}>
                    No named graphs in this repository.
                  </div>
                )}
                {graphsErr && (
                  <div style={{ fontSize: 11.5, color: "var(--alert)", marginTop: 4 }}>{graphsErr}</div>
                )}
              </div>
              <label
                style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 12, color: "var(--cream-dim)" }}
              >
                <input type="checkbox" checked={infer} onChange={(e) => setInfer(e.target.checked)} />
                Include inferred statements
              </label>
              {exportErr && (
                <div className="text-mono" style={{ fontSize: 12, color: "var(--alert)" }}>
                  {exportErr}
                </div>
              )}
              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className="btn"
                  onClick={doExport}
                  disabled={!gdb.configured || exporting}
                >
                  {exporting ? "Downloading…" : "Download .ttl"}
                </button>
              </div>
            </div>
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
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  wide?: boolean;
  type?: "text" | "password";
}) {
  return (
    <div className="field" style={wide ? { gridColumn: "1 / -1" } : undefined}>
      <label>{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete={type === "password" ? "current-password" : "off"}
      />
    </div>
  );
}
