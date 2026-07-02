import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";

import { health } from "../api/client";

type IconKey = "convert" | "discover" | "ontology" | "visualize";

interface NavItem {
  to: string;
  label: string;
  section: "tools" | "reference";
  icon: IconKey;
  badge?: string;
  end?: boolean;
}

const ICONS: Record<IconKey | "search" | "bell", JSX.Element> = {
  convert: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M4 7h11l-3-3" />
      <path d="M20 17H9l3 3" />
    </svg>
  ),
  discover: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  ),
  ontology: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="12" cy="5" r="2.2" />
      <circle cx="5" cy="18" r="2.2" />
      <circle cx="19" cy="18" r="2.2" />
      <path d="M12 7.2v3.6M10.4 12 6.6 16M13.6 12l3.8 4" />
    </svg>
  ),
  visualize: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
      <path d="M10 6.5h4M6.5 10v4M17.5 10v4M10 17.5h4" />
    </svg>
  ),
  search: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  ),
  bell: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.7 21a2 2 0 0 1-3.4 0" />
    </svg>
  ),
};

const navItems: NavItem[] = [
  { to: "/", label: "Convert", section: "tools", icon: "convert", end: true },
  { to: "/discover", label: "Discover", section: "tools", icon: "discover" },
  { to: "/ontology", label: "Ontology", section: "reference", icon: "ontology" },
  { to: "/visualize", label: "State machine", section: "reference", icon: "visualize" },
];

const pageMeta: Record<string, { title: string; crumb: string }> = {
  "/": { title: "Convert", crumb: "Tools · Convert" },
  "/discover": { title: "Discover", crumb: "Tools · Discover" },
  "/ontology": { title: "Ontologies", crumb: "Reference · Ontologies" },
  "/visualize": { title: "ISA-88 state machine", crumb: "Reference · State machine" },
};

interface Connection {
  name: string;
  detail: string;
  state: "ok" | "warn" | "alert";
}

const CONNECTIONS: Connection[] = [
  { name: "fb2skill API", detail: "REST", state: "ok" },
  { name: "OPC UA broker", detail: "4840", state: "ok" },
  { name: "Ontologies", detail: "MAESTRO · CaSkMan", state: "ok" },
];

export default function Layout() {
  const location = useLocation();
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    function poll() {
      health()
        .then(() => !cancelled && setHealthy(true))
        .catch(() => !cancelled && setHealthy(false));
    }
    poll();
    const id = setInterval(poll, 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const meta = pageMeta[location.pathname] ?? { title: "fb2skill", crumb: "" };
  const tools = navItems.filter((n) => n.section === "tools");
  const reference = navItems.filter((n) => n.section === "reference");

  const apiConn: Connection = {
    name: "fb2skill API",
    detail: healthy === null ? "checking…" : healthy ? "healthy" : "unreachable",
    state: healthy === null ? "warn" : healthy ? "ok" : "alert",
  };
  const conns: Connection[] = [apiConn, ...CONNECTIONS.slice(1)];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sb-brand">
          <div className="sb-brand-logo" aria-hidden>
            <img src="/logo-mark.svg" alt="" />
          </div>
          <div className="sb-brand-text">
            <b>
              industri<em>agents</em>
            </b>
            <small>FB2SKILL</small>
          </div>
        </div>

        <div className="sb-section">Tools</div>
        <nav className="sb-nav">
          {tools.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `sb-link${isActive ? " is-active" : ""}`
              }
            >
              <span className="sb-ico">{ICONS[n.icon]}</span>
              <span>{n.label}</span>
              {n.badge && <span className="sb-badge">{n.badge}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="sb-section">Reference</div>
        <nav className="sb-nav">
          {reference.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `sb-link${isActive ? " is-active" : ""}`
              }
            >
              <span className="sb-ico">{ICONS[n.icon]}</span>
              <span>{n.label}</span>
              {n.badge && <span className="sb-badge">{n.badge}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="sb-section">Connections</div>
        <div className="sb-conns">
          {conns.map((c) => (
            <div key={c.name} className="sb-conn">
              <span className={`dot ${c.state}`} />
              <b>{c.name}</b>
              <small>{c.detail}</small>
            </div>
          ))}
        </div>

        <div className="sb-footer">
          <div className="muted">IEC 61499 → CaSk TTL</div>
          <div className="muted">v0.1 · industriagents.com</div>
          <div className="muted">SOC2 · IEC 62443</div>
        </div>
      </aside>

      <header className="topbar">
        <div className="tb-left">
          <span className="tb-crumb">
            IndustriAgents · <b>{meta.crumb || "fb2skill"}</b>
          </span>
        </div>
        <div className="tb-right">
          <div className="tb-search">
            <span
              style={{ color: "var(--cream-faint)", display: "inline-flex" }}
            >
              {ICONS.search}
            </span>
            <input placeholder="Search skills, blocks, files…" />
            <kbd>⌘K</kbd>
          </div>
          <span className="tb-pill">
            <span
              className={`live-dot ${
                healthy === null ? "idle" : healthy ? "ok" : "alert"
              }`}
            />
            {healthy === null
              ? "Connecting"
              : healthy
              ? "Live · API"
              : "API offline"}
          </span>
          <span className="tb-pill">MAESTRO 0.4 · CaSkMan 4.3</span>
        </div>
      </header>

      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
