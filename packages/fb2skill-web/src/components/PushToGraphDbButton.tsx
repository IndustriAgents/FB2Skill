import { useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../api/client";
import { useGraphDb } from "../state/graphdb";
import type { PushItem, PushItemResult } from "../types/api";

interface Props {
  /** Items to push. `graph` may be omitted to use the configured template. */
  items: PushItem[];
  label?: string;
  small?: boolean;
  onDone?: (results: PushItemResult[] | null, error: string | null) => void;
}

/**
 * "Push to GraphDB" action. Disabled (with a hint) until a connection is
 * configured on the GraphDB page. Reports results through `onDone`; render
 * them with <PushResultList/>.
 */
export default function PushToGraphDbButton({ items, label, small, onDone }: Props) {
  const gdb = useGraphDb();
  const [busy, setBusy] = useState(false);

  async function run() {
    if (!gdb.configured || items.length === 0) return;
    setBusy(true);
    try {
      const results = await gdb.push(
        items.map((it) => ({ ...it, graph: it.graph === undefined ? gdb.graphFor(it.name) : it.graph }))
      );
      onDone?.(results, null);
    } catch (e) {
      onDone?.(null, e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const text = label ?? (items.length > 1 ? `Push ${items.length} to GraphDB` : "Push to GraphDB");

  if (!gdb.configured) {
    return (
      <Link
        to="/graphdb"
        className={`btn is-ghost${small ? " is-sm" : ""}`}
        title="Configure a GraphDB connection first"
      >
        {text} · configure
      </Link>
    );
  }

  return (
    <button
      type="button"
      className={`btn${small ? " is-sm" : ""}`}
      onClick={run}
      disabled={busy || items.length === 0}
      title={`${gdb.mode} → ${gdb.connection.repository}`}
    >
      {busy ? "Pushing…" : text}
    </button>
  );
}

export function PushResultList({
  results,
  error,
}: {
  results: PushItemResult[] | null;
  error: string | null;
}) {
  if (!results && !error) return null;
  return (
    <div
      className="text-mono"
      style={{
        fontSize: 11.5,
        border: "1px solid var(--line)",
        borderRadius: 8,
        padding: "8px 12px",
        display: "flex",
        flexDirection: "column",
        gap: 4,
      }}
    >
      {error && <span style={{ color: "var(--alert)" }}>✕ {error}</span>}
      {results?.map((r) => (
        <div key={`${r.name}:${r.graph ?? ""}`} style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
          <span style={{ color: r.ok ? "var(--ok)" : "var(--alert)" }}>{r.ok ? "✓" : "✕"}</span>
          <span style={{ color: "var(--accent)" }}>{r.name}</span>
          <span style={{ color: "var(--cream-faint)" }}>{r.graph ?? "default graph"}</span>
          {r.ok && typeof r.triples === "number" && (
            <span style={{ color: "var(--cream-dim)" }}>{r.triples} triples</span>
          )}
          {!r.ok && r.error && <span style={{ color: "var(--alert)" }}>{r.error}</span>}
        </div>
      ))}
    </div>
  );
}
