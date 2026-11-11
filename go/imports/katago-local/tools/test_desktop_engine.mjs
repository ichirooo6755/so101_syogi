/** Real TypeScript -> JSON Lines -> Rust -> KataGo smoke test.
 * Uses a private database and low-memory configs; never edits user settings. */
import assert from "node:assert/strict";
import { spawn, execFileSync } from "node:child_process";
import { mkdtemp, readFile, writeFile, rm, mkdir } from "node:fs/promises";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { ApplicationController } from "../desktop/src/application.ts";
import { BackendComputation } from "../desktop/src/computation.ts";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const artifacts = path.join(root, "artifacts");
await mkdir(artifacts, { recursive: true });
const work = await mkdtemp(path.join(artifacts, "desktop-engine-"));
const report = { status: "failed", checks: [] };
let backend, errorOutput = "";
const pending = new Map();
let sequence = 0;
function invoke(command, args = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timeout = setTimeout(() => { pending.delete(id); reject(new Error(`RPC timeout: ${command}`)); }, 30000);
    pending.set(id, { resolve: (value) => { clearTimeout(timeout); resolve(value); }, reject: (error) => { clearTimeout(timeout); reject(error); } });
    backend.stdin.write(JSON.stringify({ id, command, args }) + "\n");
  });
}
function configText(text, overrides) {
  for (const [key, value] of Object.entries(overrides)) {
    const pattern = new RegExp(`^[ \\t]*${key}[ \\t]*=.*$`, "gm");
    const line = `${key} = ${value}`;
    text = pattern.test(text) ? text.replace(pattern, () => line) : text + "\n" + line;
  }
  return text;
}
try {
  report.version = execFileSync(path.join(root, "vendor/katago/katago.exe"), ["version"], { encoding: "utf8", timeout: 15000, windowsHide: true }).trim();
  backend = spawn(process.env.KATAGO_LOCAL_BACKEND ?? path.join(root, "target/debug", process.platform === "win32" ? "katago-local.exe" : "katago-local"), ["engine-rpc", "--root", root, "--database", path.join(work, "app.sqlite")], { cwd: root, windowsHide: true, stdio: ["pipe", "pipe", "pipe"] });
  backend.stderr.on("data", (bytes) => { errorOutput = (errorOutput + bytes).slice(-4000); });
  backend.on("error", (error) => { for (const request of pending.values()) request.reject(error); pending.clear(); });
  backend.on("exit", () => { for (const request of pending.values()) request.reject(new Error("Rust backend exited: " + errorOutput)); pending.clear(); });
  createInterface({ input: backend.stdout }).on("line", (line) => {
    const response = JSON.parse(line), request = pending.get(response.id);
    if (!request) return;
    pending.delete(response.id);
    if (response.error) request.reject(new Error(response.error)); else request.resolve(response.result);
  });
  const settings = await invoke("get_settings");
  const common = { maxVisits: 8, nnCacheSizePowerOfTwo: 16, nnMutexPoolSizePowerOfTwo: 12, nnMaxBatchSize: 2, logToStderr: false, logDir: path.join(work, "logs").replaceAll("\\", "/") };
  const gtpConfigPath = path.join(work, "gtp.cfg"), analysisConfigPath = path.join(work, "analysis.cfg");
  await writeFile(gtpConfigPath, configText(await readFile(settings.gtpConfigPath, "utf8"), { ...common, numSearchThreads: 2, ponderingEnabled: false, logAllGTPCommunication: false, logSearchInfo: false }));
  await writeFile(analysisConfigPath, configText(await readFile(settings.analysisConfigPath, "utf8"), { ...common, numAnalysisThreads: 1, numSearchThreadsPerAnalysisThread: 2 }));
  await invoke("save_settings", { settings: { gtpConfigPath, analysisConfigPath, threads: 2, cachePolicy: "disabled" } });
  const app = new ApplicationController((command, args = {}) => invoke(command, command === "start_computation" ? { ...args, visits: 8 } : args));
  const local = (command, args) => app.invoke(command, args);
  const compute = async (command, args = {}) => {
    const operation = new BackendComputation(local, command, args, 25);
    const timeout = setTimeout(() => { void operation.cancel().catch(() => {}); }, 45000);
    try { return await operation.result(); }
    finally { clearTimeout(timeout); }
  };
  await local("new_session", { config: { mode: "record", boardSize: 9, komi: 6.5, ruleset: "japanese", handicap: 0, evaluationEnabled: true, visitBudget: "light", maxCandidates: 3, useAnalysisCache: false } });
  await local("play_move", { color: "black", vertex: "D4" });
  const analysis = await compute("analyze_current_position");
  assert.ok(analysis.visits > 0 && analysis.candidates.length > 0);
  assert.equal((await local("get_state")).moveCount, 1);
  report.checks.push("GTP analysis of a TypeScript position without changing its record");
  const reply = await compute("genmove", { color: "white" });
  assert.equal(reply.state.moveCount, reply.move === "resign" ? 1 : 2);
  report.checks.push("AI suggestion committed by TypeScript");
  const operation = new BackendComputation(local, "genmove", {}, 25);
  const before = (await local("get_state")).moveCount;
  await operation.cancel();
  assert.equal((await local("get_state")).moveCount, before);
  report.checks.push("real-engine cancellation leaves the TypeScript record unchanged");
  await local("load_sgf", { text: "(;SZ[13]AB[ma]AW[ai]PL[B];B[mi];AE[ma]PL[W];W[bb]C[日本語])(;SZ[9]GN[second])" });
  const square = await compute("analyze_current_position");
  assert.ok(square.visits > 0);
  const review = await compute("analyze_game");
  assert.deepEqual(review.map((point) => point.moveNumber), [0, 1, 2]);
  report.checks.push("square board and setup segments in GTP and Analysis Engine");
  const beforeHistory = await local("get_state");
  const history = await compute("analyze_move_history");
  for (const entry of beforeHistory.moveHistory) {
    assert.ok(history.some((point) => point.positionKey === entry.beforePositionKey && Number.isFinite(point.scoreLead)));
    assert.ok(history.some((point) => point.positionKey === entry.positionKey && Number.isFinite(point.winrate)));
  }
  assert.deepEqual(await local("get_state"), beforeHistory);
  report.checks.push("move-history evaluations keep setup boundaries and leave the board unchanged");
  await local("undo_move");
  const advanced = await local("redo_move");
  assert.deepEqual(advanced.currentPath, beforeHistory.currentPath);
  assert.deepEqual(advanced.game, beforeHistory.game);
  report.checks.push("undo then redo restores the exact real-engine position");
  const target = path.join(work, "roundtrip.sgf");
  await local("save_sgf", { path: target });
  const restored = await local("load_sgf", { path: target });
  assert.equal(restored.gameCount, 2);
  assert.deepEqual(restored.properties.C, ["日本語"]);
  report.checks.push("Sabaki SGF round trip through opaque Rust file I/O");
  report.status = "passed";
} catch (error) {
  report.error = String(error);
  if (/4551|application control|blocked by.*policy|アクセス.*拒否|EACCES/.test(String(error))) report.status = "blocked";
  if (errorOutput) report.stderr = errorOutput;
  process.exitCode = 1;
} finally {
  if (backend && backend.exitCode === null) {
    backend.stdin.end();
    await new Promise((resolve) => {
      const timeout = setTimeout(() => { backend.kill(); resolve(); }, 10000);
      backend.once("exit", () => { clearTimeout(timeout); resolve(); });
    });
  }
  for (const request of pending.values()) request.reject(new Error("test finished"));
  pending.clear();
  // Delete only the exact scratch directory created under this workspace.
  if (path.dirname(work) === artifacts && path.basename(work).startsWith("desktop-engine-")) await rm(work, { recursive: true, force: true });
  await writeFile(path.join(artifacts, "typescript-engine-test.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify(report, null, 2));
}
