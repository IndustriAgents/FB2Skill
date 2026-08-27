import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { ApiError, pushToGraphDb, testGraphDb } from "../api/client";
import type {
  GraphDBConnection,
  PushItem,
  PushItemResult,
  PushMode,
  TestConnectionResponse,
} from "../types/api";

export interface ConnectionForm {
  base_url: string;
  repository: string;
  username: string;
  password: string;
  remember_password: boolean;
}

export type GraphDbStatus = "unconfigured" | "untested" | "ok" | "error";

interface Persisted {
  connection: Omit<ConnectionForm, "password">;
  graphTemplate: string;
  mode: PushMode;
}

interface GraphDbState {
  connection: ConnectionForm;
  setConnection: (patch: Partial<ConnectionForm>) => void;
  graphTemplate: string;
  setGraphTemplate: (v: string) => void;
  mode: PushMode;
  setMode: (m: PushMode) => void;
  status: GraphDbStatus;
  configured: boolean;
  lastTest: TestConnectionResponse | null;
  lastMessage: string | null;
  testing: boolean;
  test: () => Promise<TestConnectionResponse | null>;
  push: (items: PushItem[]) => Promise<PushItemResult[]>;
  /** Named graph for a skill, from the template ("" = default graph). */
  graphFor: (name: string) => string | null;
  /** Backend-shaped connection payload. */
  toConnection: () => GraphDBConnection;
}

const STORAGE_KEY = "fb2skill.graphdb";
const SESSION_PW_KEY = "fb2skill.graphdb.pw";

const DEFAULT_CONNECTION: ConnectionForm = {
  base_url: "http://localhost:7200",
  repository: "",
  username: "",
  password: "",
  remember_password: false,
};
const DEFAULT_TEMPLATE = "urn:fb2skill:skill:{name}";

function load(): { form: ConnectionForm; graphTemplate: string; mode: PushMode } {
  let form = { ...DEFAULT_CONNECTION };
  let graphTemplate = DEFAULT_TEMPLATE;
  let mode: PushMode = "append";
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const p = JSON.parse(raw) as Partial<Persisted>;
      if (p.connection) form = { ...form, ...p.connection, password: "" };
      if (typeof p.graphTemplate === "string") graphTemplate = p.graphTemplate;
      if (p.mode === "append" || p.mode === "replace") mode = p.mode;
    }
    if (form.remember_password) {
      form.password = sessionStorage.getItem(SESSION_PW_KEY) ?? "";
    }
  } catch {
    /* storage unavailable */
  }
  return { form, graphTemplate, mode };
}

const Ctx = createContext<GraphDbState | null>(null);

export function GraphDbProvider({ children }: { children: ReactNode }) {
  const initial = useMemo(load, []);
  const [connection, setConn] = useState<ConnectionForm>(initial.form);
  const [graphTemplate, setGraphTemplate] = useState(initial.graphTemplate);
  const [mode, setMode] = useState<PushMode>(initial.mode);
  const [lastTest, setLastTest] = useState<TestConnectionResponse | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [tested, setTested] = useState<"ok" | "error" | null>(null);

  // Persist everything except the password (session-only, opt-in).
  useEffect(() => {
    try {
      const { password, ...rest } = connection;
      const p: Persisted = { connection: rest, graphTemplate, mode };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
      if (connection.remember_password) sessionStorage.setItem(SESSION_PW_KEY, password);
      else sessionStorage.removeItem(SESSION_PW_KEY);
    } catch {
      /* storage unavailable */
    }
  }, [connection, graphTemplate, mode]);

  const configured = connection.base_url.trim() !== "" && connection.repository.trim() !== "";

  const setConnection = useCallback((patch: Partial<ConnectionForm>) => {
    setConn((c) => ({ ...c, ...patch }));
    setTested(null);
  }, []);

  const toConnection = useCallback((): GraphDBConnection => {
    return {
      base_url: connection.base_url.trim(),
      repository: connection.repository.trim(),
      username: connection.username.trim() || null,
      password: connection.username.trim() ? connection.password : null,
    };
  }, [connection]);

  const test = useCallback(async () => {
    if (!configured) return null;
    setTesting(true);
    try {
      const r = await testGraphDb(toConnection());
      setLastTest(r);
      setLastMessage(r.message);
      setTested(r.ok ? "ok" : "error");
      return r;
    } catch (e) {
      setLastTest(null);
      setLastMessage(e instanceof ApiError ? e.message : String(e));
      setTested("error");
      return null;
    } finally {
      setTesting(false);
    }
  }, [configured, toConnection]);

  const graphFor = useCallback(
    (name: string) => {
      const g = graphTemplate.replace(/\{name\}/g, name).trim();
      return g === "" ? null : g;
    },
    [graphTemplate]
  );

  const push = useCallback(
    async (items: PushItem[]) => {
      const r = await pushToGraphDb({ connection: toConnection(), mode, items });
      setTested(r.results.every((x) => x.ok) ? "ok" : tested === "ok" ? "ok" : "error");
      return r.results;
    },
    [toConnection, mode, tested]
  );

  const status: GraphDbStatus = !configured
    ? "unconfigured"
    : tested === null
    ? "untested"
    : tested;

  const value: GraphDbState = {
    connection,
    setConnection,
    graphTemplate,
    setGraphTemplate,
    mode,
    setMode,
    status,
    configured,
    lastTest,
    lastMessage,
    testing,
    test,
    push,
    graphFor,
    toConnection,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useGraphDb(): GraphDbState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useGraphDb must be used inside <GraphDbProvider>");
  return v;
}
