import type { MoveHistoryEntry, MoveHistoryEvaluation, SessionState } from "./backend";

export const pathKey = (path: number[]) => JSON.stringify(path);
export const pathContains = (path: number[], ancestor: number[]) => ancestor.length <= path.length && ancestor.every((part, index) => path[index] === part);

/** Follow the selected variation, continuing through its first child to its end. */
export function historyLine(session: SessionState, throughEnd = true): { path: number[]; entries: MoveHistoryEntry[] } {
  const nodes = new Map(session.nodes.map((node) => [pathKey(node.path), node]));
  const path = [...session.currentPath];
  if (throughEnd) {
    for (const index of session.redoPath) {
      if (!nodes.has(pathKey([...path, index]))) break;
      path.push(index);
    }
    while ((nodes.get(pathKey(path))?.childCount ?? 0) > 0) path.push(0);
  }
  return { path, entries: session.moveHistory.filter((entry) => pathContains(path, entry.path)) };
}

export function judgeMove(entry: MoveHistoryEntry, before?: MoveHistoryEvaluation, after?: MoveHistoryEvaluation): { label: string; kind: string; loss: number | null } {
  if (!before || !after || !Number.isFinite(before.scoreLead) || !Number.isFinite(after.scoreLead)) return { label: "未解析", kind: "unrated", loss: null };
  // Analysis Engine values are explicitly reported from Black's perspective.
  const loss = Math.max(0, (before.scoreLead - after.scoreLead) * (entry.color === "black" ? 1 : -1));
  if (loss < 1) return { label: "良手", kind: "good", loss };
  if (loss < 3) return { label: "疑問手", kind: "inaccuracy", loss };
  if (loss < 6) return { label: "悪手", kind: "mistake", loss };
  return { label: "大悪手", kind: "blunder", loss };
}
