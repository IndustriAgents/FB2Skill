import { useEffect, useMemo, useState } from "react";

import { fetchOntologies, fetchOntologyFile } from "../api/client";
import type { OntologyInfo, PushItemResult } from "../types/api";
import PushToGraphDbButton, { PushResultList } from "../components/PushToGraphDbButton";
import TtlViewer from "../components/TtlViewer";

export default function OntologyPage() {
  const [ontologies, setOntologies] = useState<OntologyInfo[] | null>(null);
  const [selected, setSelected] = useState<string>("maestro");
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [ttl, setTtl] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [pushResults, setPushResults] = useState<PushItemResult[] | null>(null);
  const [pushErr, setPushErr] = useState<string | null>(null);

  const current = ontologies?.find((o) => o.id === selected) ?? null;

  useEffect(() => {
    fetchOntologies()
      .then((r) => {
        setOntologies(r.ontologies);
        const first = r.ontologies.find((o) => o.id === "maestro") ?? r.ontologies[0];
        if (first) setActiveFile(first.groups[0]?.files[0] ?? null);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  function selectOntology(o: OntologyInfo) {
    setSelected(o.id);
    setActiveFile(o.groups[0]?.files[0] ?? null);
  }

  useEffect(() => {
    if (!activeFile) return;
    let stale = false;
    setTtl(null);
    setErr(null);
    fetchOntologyFile(selected, activeFile)
      .then((t) => {
        if (!stale) setTtl(t);
      })
      .catch((e) => {
        if (!stale) setErr(String(e));
      });
    return () => {
      stale = true;
    };
  }, [selected, activeFile]);

  const stats = useMemo(() => {
    if (!ttl) return null;
    const prefixCount = (ttl.match(/^@prefix /gm) || []).length;
    const classCount = (ttl.match(/\b(a|rdf:type)\s+owl:Class\b/g) || []).length;
    const subjects = new Set<string>();
    ttl.split(/\.\s*\n/).forEach((stmt) => {
      const m = stmt.match(/^\s*([:\w][\w:.\-]*)/m);
      if (m) subjects.add(m[1]);
    });
    return {
      bytes: new Blob([ttl]).size,
      prefixCount,
      classCount,
      subjectCount: subjects.size,
    };
  }, [ttl]);

  function download() {
    if (!ttl || !activeFile) return;
    const blob = new Blob([ttl], { type: "text/turtle" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = activeFile.split("/").pop()!;
    a.click();
    URL.revokeObjectURL(url);
  }

  const isMulti = (current?.groups.length ?? 0) > 1;

  return (
    <div>
      <div className="view-head">
        <div>
          <h1>
            <em>{current?.label ?? "Ontology"}</em> ontology
          </h1>
          <p className="view-sub">
            {current
              ? `${current.label} ${current.version}` +
                (current.baseIri ? ` · ${current.baseIri}` : "")
              : "Bundled target ontologies."}
          </p>
        </div>
        <div className="view-actions" style={{ display: "flex", gap: 8 }}>
          {ontologies && (
            <div className="tabs" style={{ borderBottom: "none" }}>
              {ontologies.map((o) => (
                <button
                  key={o.id}
                  type="button"
                  onClick={() => selectOntology(o)}
                  className={`tab${selected === o.id ? " is-active" : ""}`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          )}
          {ttl && activeFile && (
            <>
              <PushToGraphDbButton
                items={[
                  {
                    name: activeFile.split("/").pop()!,
                    graph: `urn:fb2skill:ontology:${selected}`,
                    ontology_file: { ontology_id: selected, file_path: activeFile },
                  },
                ]}
                onDone={(r, e) => {
                  setPushResults(r);
                  setPushErr(e);
                }}
              />
              <button type="button" className="btn" onClick={download}>
                Download .ttl
              </button>
            </>
          )}
        </div>
      </div>

      {(pushResults || pushErr) && (
        <div style={{ marginBottom: 16 }}>
          <PushResultList results={pushResults} error={pushErr} />
        </div>
      )}

      {err && (
        <div
          className="text-mono"
          style={{
            fontSize: 12,
            color: "var(--alert)",
            background: "rgba(255,87,96,0.06)",
            border: "1px solid rgba(255,87,96,0.3)",
            borderRadius: 8,
            padding: "10px 14px",
            marginBottom: 16,
          }}
        >
          {err}
        </div>
      )}

      {stats && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: 12,
            marginBottom: 18,
          }}
        >
          <Stat
            label="Size"
            value={(stats.bytes / 1024).toFixed(0)}
            unit="KB"
          />
          <Stat label="@prefix lines" value={stats.prefixCount} />
          <Stat label="owl:Class refs" value={stats.classCount} />
          <Stat label="Subjects (approx.)" value={stats.subjectCount} />
        </div>
      )}

      <div
        style={
          isMulti
            ? {
                display: "grid",
                gridTemplateColumns: "230px minmax(0, 1fr)",
                gap: 18,
                alignItems: "start",
              }
            : undefined
        }
      >
        {isMulti && current && (
          <div className="card">
            <div className="card-head">
              <h3>Modules</h3>
              <span className="card-meta">{current.version}</span>
            </div>
            <div
              className="card-body"
              style={{ padding: "8px 0", maxHeight: "68vh", overflowY: "auto" }}
            >
              {current.groups.map((g) => (
                <div key={g.id} style={{ padding: "6px 0" }}>
                  <div
                    style={{
                      padding: "4px 16px",
                      fontSize: 10.5,
                      letterSpacing: "0.08em",
                      textTransform: "uppercase",
                      color: "var(--cream-faint)",
                    }}
                  >
                    {g.label}
                  </div>
                  {g.files.map((f) => (
                    <button
                      key={f}
                      type="button"
                      onClick={() => setActiveFile(f)}
                      style={{
                        display: "block",
                        width: "100%",
                        textAlign: "left",
                        padding: "5px 16px",
                        fontSize: 12,
                        fontFamily: "var(--mono)",
                        background:
                          activeFile === f
                            ? "rgba(255,255,255,0.06)"
                            : "transparent",
                        color:
                          activeFile === f
                            ? "var(--accent)"
                            : "var(--cream-dim)",
                        border: "none",
                        cursor: "pointer",
                      }}
                    >
                      {f.split("/").pop()}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="card">
          <div className="card-head">
            <h3>Turtle source</h3>
            <span className="card-meta">
              {activeFile ?? "select a file"}
            </span>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            {ttl ? (
              <TtlViewer ttl={ttl} maxHeight="68vh" />
            ) : !err ? (
              <div
                style={{
                  padding: "48px 16px",
                  textAlign: "center",
                  color: "var(--cream-faint)",
                  fontSize: 13,
                }}
              >
                Loading ontology…
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  unit,
}: {
  label: string;
  value: string | number;
  unit?: string;
}) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-val">
        {value}
        {unit && <span className="unit">{unit}</span>}
      </div>
    </div>
  );
}
