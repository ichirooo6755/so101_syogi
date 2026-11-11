import { invoke as tauriInvoke } from "@tauri-apps/api/core";
import type { Vertex } from "@sabaki/shudan";
import type { GameState } from "./game";
import { ApplicationController } from "./application.ts";

export type FlowMode = "play" | "record" | "import";
export type Ruleset = "japanese" | "chinese" | "korean" | "aga" | "new-zealand" | "tromp-taylor";
export type VisitBudget = "light" | "balanced" | "deep";
export type InitialPosition = "start" | "last" | "problem";

export interface AppSettings {
  katagoPath: string;
  openclPath: string;
  cudaPath: string;
  modelPath: string;
  gtpConfigPath: string;
  analysisConfigPath: string;
  cachePolicy: "reuse" | "disabled";
  useGpu: boolean;
  gpuBackend: "" | "opencl" | "cuda";
  gpuDeviceIndex: number;
  gpuName: string;
}

export interface SessionConfig {
  mode: FlowMode;
  boardSize: number;
  ruleset: Ruleset;
  komi: number;
  handicap: number;
  evaluationEnabled: boolean;
  visitBudget?: VisitBudget;
  maxCandidates?: number;
  useAnalysisCache?: boolean;
  source?: string;
  initialPosition?: InitialPosition;
}

export interface SessionState {
  config?: SessionConfig;
  id: string;
  title: string;
  moveCount: number;
  engineStatus: "idle" | "running" | "analyzing" | "error";
  activeSession: boolean;
  mode: FlowMode;
  computation: { id: string; command: string } | null;
  boardSize: number;
  boardHeight: number;
  komi: number;
  ruleset: string;
  metadata: Record<string, string | number | null>;
  game: GameState;
  gameIndex: number;
  gameCount: number;
  games: { index: number; title: string }[];
  currentPath: number[];
  redoPath: number[];
  moveHistory: MoveHistoryEntry[];
  properties: Record<string, string[]>;
  variations: { index: number; properties: Record<string, string[]> }[];
  nodes: { path: number[]; label: string; comment: string; childCount: number }[];
}

export interface MoveHistoryEntry {
  path: number[];
  moveNumber: number;
  color: "black" | "white";
  vertex: string;
  branchDepth: number;
  beforePositionKey: string;
  positionKey: string;
}

export interface MoveHistoryEvaluation {
  positionKey: string;
  winrate: number;
  scoreLead: number;
}

export interface CandidateMove {
  vertex: Vertex | null;
  label: string;
  winrate: number;
  scoreLead: number;
  visits: number;
  pv: string[];
}

export interface AnalysisResult {
  winrate: number;
  scoreLead: number;
  visits: number;
  candidates: CandidateMove[];
}

export interface ReviewPoint {
  moveNumber: number;
  winrate: number;
  scoreLead: number;
}

export async function invokeEngine<T>(command: string, args: Record<string, unknown> = {}): Promise<T> {
  if ("__TAURI_INTERNALS__" in window) {
    return tauriInvoke<T>("backend_command", { command, args });
  }
  let response: Response;
  try {
    response = await fetch("/api/backend", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command, args }),
    });
  } catch {
    throw new Error("Rust backend に接続できません。cargo run -p katago-local -- dev-server を起動してください。");
  }
  if (!response.ok) throw new Error(`Rust backend error: HTTP ${response.status}`);
  const payload = await response.json();
  if (payload.error) throw new Error(payload.error);
  return payload.result as T;
}

let application: ApplicationController | undefined;
export function invokeApplication<T>(command: string, args: Record<string, unknown> = {}): Promise<T> {
  application ??= new ApplicationController(invokeEngine, window.sessionStorage);
  return application.invoke<T>(command, args);
}
