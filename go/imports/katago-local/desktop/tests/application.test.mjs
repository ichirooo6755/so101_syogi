import assert from "node:assert/strict";
import test from "node:test";
import { ApplicationController } from "../src/application.ts";
import { BackendComputation } from "../src/computation.ts";

const offline = { mode: "record", boardSize: 9, komi: 6.5, ruleset: "japanese", handicap: 0, evaluationEnabled: false };
const online = { ...offline, evaluationEnabled: true, visitBudget: "light", maxCandidates: 3, useAnalysisCache: true };
const unavailable = async () => { throw new Error("backend must not be called"); };
const memory = () => { const values = new Map(); return { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) }; };

test("setup validation checks previous records and SGF without changing the current document", async () => {
  const app = new ApplicationController(async () => ({ data: Buffer.from("(;SZ[13:9])").toString("base64") }));
  assert.match((await app.invoke("validate_session", { config: { ...offline, initialPosition: "last" } })).issues[0], /前回の棋譜/);
  await assert.rejects(app.invoke("new_session", { config: { ...offline, initialPosition: "last" } }), /前回の棋譜/);
  await app.invoke("new_session", { config: offline });
  await app.invoke("play_move", { color: "black", vertex: "A9" });
  const before = await app.invoke("get_state");
  assert.deepEqual(await app.invoke("validate_session", { config: { ...offline, initialPosition: "last" } }), { issues: [] });
  assert.match((await app.invoke("validate_session", { config: { ...offline, mode: "import" } })).issues[0], /棋譜ファイル/);
  assert.match((await app.invoke("validate_session", { config: { ...offline, mode: "import", source: "rectangle.sgf" } })).issues[0], /正方形/);
  assert.deepEqual(await app.invoke("get_state"), before);
});

test("setup validation reports engine readiness only when AI evaluation is enabled", async () => {
  const calls = [], app = new ApplicationController(async (command) => {
    calls.push(command);
    return { issues: ["モデルが見つかりません。", "GTP設定が見つかりません。"] };
  });
  assert.equal((await app.invoke("validate_session", { config: online })).issues.length, 2);
  assert.deepEqual(calls, ["check_engine_settings"]);
  assert.deepEqual(await app.invoke("validate_session", { config: offline }), { issues: [] });
  assert.equal(calls.length, 1);
  const disconnected = new ApplicationController(async () => { throw new Error("backend unavailable"); });
  assert.match((await disconnected.invoke("validate_session", { config: online })).issues[0], /AI評価.*backend unavailable/);
});

test("all record editing works without the engine backend, including enabled evaluation", async () => {
  const app = new ApplicationController(unavailable);
  await app.invoke("new_session", { config: online });
  await app.invoke("play_move", { color: "black", vertex: "A9" });
  await app.invoke("pass_move", { color: "white" });
  await app.invoke("undo_move");
  await app.invoke("play_move", { color: "white", vertex: "B8" });
  await app.invoke("set_comment", { comment: "local comment" });
  const { text } = await app.invoke("save_sgf");
  assert.match(text, /C\[local comment\]/);
  let state = await app.invoke("load_sgf", { text, initialPosition: "start" });
  assert.equal(state.moveCount, 0);
  state = await app.invoke("goto_node", { path: [0, 1] });
  assert.equal(state.game.signMap[1][1], -1);
  assert.equal(state.properties.C[0], "local comment");
  assert.equal(state.nodes.length, 4);
});

test("a failed edit or malformed import cannot change the current document", async () => {
  const app = new ApplicationController(unavailable);
  await app.invoke("load_sgf", { text: "(;SZ[9];B[aa])" });
  const before = await app.invoke("get_state");
  await assert.rejects(app.invoke("set_node_properties", { properties: { B: ["zz"] } }));
  await assert.rejects(app.invoke("load_sgf", { text: "(;SZ[9]" }));
  await assert.rejects(app.invoke("goto_node", { path: [20] }));
  await assert.rejects(app.invoke("play_move", { color: "black", vertex: "B8" }));
  await assert.rejects(app.invoke("set_node_properties", { properties: JSON.parse('{"__proto__":["invalid"]}') }));
  await assert.rejects(app.invoke("load_sgf", { text: "(;SZ[13:9];B[aa])" }), /正方形/);
  assert.deepEqual(await app.invoke("get_state"), before);
});

test("changing SZ to a rectangle is rejected without altering the board", async () => {
  const app = new ApplicationController(unavailable);
  await app.invoke("load_sgf", { text: "(;SZ[13];B[aa])" });
  const before = await app.invoke("goto_node", { path: [] });
  await assert.rejects(app.invoke("set_node_properties", { properties: { SZ: ["13:9"] } }), /正方形/);
  assert.deepEqual(await app.invoke("get_state"), before);
});

test("reload restores every collection, selected branch, cursor and file name", async () => {
  const storage = memory(), app = new ApplicationController(unavailable, storage);
  await app.invoke("new_session", { config: offline });
  await app.invoke("load_sgf", { text: "(;SZ[9];B[aa](;W[bb])(;W[cc]))(;SZ[13];B[dd])" });
  await app.invoke("goto_node", { path: [0, 1] });
  await app.invoke("select_game", { index: 1 });
  await app.invoke("undo_move");
  const restored = new ApplicationController(unavailable, storage);
  assert.deepEqual(await restored.invoke("get_state"), await app.invoke("get_state"));
  const state = await restored.invoke("select_game", { index: 0 });
  assert.deepEqual(state.currentPath, [0, 1]);
});

test("file I/O passes opaque bytes/text and save failures preserve the file name", async () => {
  const calls = [], app = new ApplicationController(async (command, args) => {
    calls.push([command, args]);
    if (command === "read_file") return { data: Buffer.from("(;SZ[13]PB[黒];B[aa])").toString("base64") };
    if (args.path === "bad.sgf") throw new Error("write failed");
    return { path: "saved.sgf" };
  });
  await app.invoke("load_sgf", { path: "source.sgf" });
  await assert.rejects(app.invoke("save_sgf", { path: "bad.sgf" }), /write failed/);
  assert.equal((await app.invoke("get_state")).metadata.fileName, "source.sgf");
  await app.invoke("save_sgf", { path: "saved.sgf" });
  assert.equal((await app.invoke("get_state")).metadata.fileName, "saved.sgf");
  assert.deepEqual(calls.map(([command]) => command), ["read_file", "write_file", "write_file"]);
  assert.match(calls[2][1].text, /PB\[黒\]/);
});

function engine(result = "B8") {
  const calls = [];
  return { calls, invoke: async (command, args) => {
    calls.push([command, args]);
    if (command === "start_computation") return { id: "job", status: "running", result: null };
    if (command === "cancel_computation") return { id: "job", status: "cancelled", result: null };
    return { id: "job", status: "completed", result };
  } };
}

test("AI receives an explicit position, and its move is committed only on acceptance", async () => {
  const remote = engine(), app = new ApplicationController(remote.invoke);
  await app.invoke("new_session", { config: online });
  await app.invoke("play_move", { color: "black", vertex: "A9" });
  await app.invoke("start_computation", { command: "genmove", args: { color: "white" } });
  assert.deepEqual(remote.calls[0][1].position.segments[0].moves, [["B", "A9"]]);
  assert.equal(remote.calls[0][1].position.nextPlayer, "W");
  await app.invoke("get_computation", { id: "job" });
  assert.equal((await app.invoke("get_state")).moveCount, 1);
  const result = await app.invoke("accept_computation", { id: "job" });
  assert.equal(result.state.moveCount, 2);
  assert.equal(result.state.game.signMap[1][1], -1);
  assert.deepEqual(await app.invoke("accept_computation", { id: "job" }), result);
});

test("cancelling a completed but unaccepted AI reply leaves the record untouched", async () => {
  const remote = engine("resign"), app = new ApplicationController(remote.invoke);
  await app.invoke("new_session", { config: online });
  const before = await app.invoke("get_state");
  await app.invoke("start_computation", { command: "genmove" });
  await app.invoke("get_computation", { id: "job" });
  await app.invoke("cancel_computation", { id: "job" });
  assert.deepEqual(await app.invoke("get_state"), before);
  await assert.rejects(app.invoke("accept_computation", { id: "job" }));
});

test("reload cancels its previous engine job while keeping the document editable", async () => {
  const remote = engine(), storage = memory(), app = new ApplicationController(remote.invoke, storage);
  await app.invoke("new_session", { config: online });
  await app.invoke("play_move", { color: "black", vertex: "A9" });
  await app.invoke("start_computation", { command: "genmove" });
  const restored = new ApplicationController(remote.invoke, storage);
  const state = await restored.invoke("set_comment", { comment: "after reload" });
  assert.equal(state.moveCount, 1);
  assert.equal(state.computation, null);
  assert.ok(remote.calls.some(([command, args]) => command === "cancel_computation" && args.id === "job"));
});

test("resignation updates RE without adding a pass; late cancellation restores it", async () => {
  const remote = engine("resign"), app = new ApplicationController(remote.invoke);
  await app.invoke("new_session", { config: online });
  await app.invoke("start_computation", { command: "genmove" });
  await app.invoke("get_computation", { id: "job" });
  const result = await app.invoke("accept_computation", { id: "job" });
  assert.equal(result.state.metadata.result, "W+R");
  assert.equal(result.state.moveCount, 0);
  await app.invoke("cancel_computation", { id: "job" });
  assert.equal((await app.invoke("get_state")).metadata.result, "");
});

test("navigation confirmation holds an AI result until it is accepted or cancelled", async () => {
  const remote = engine(), app = new ApplicationController(remote.invoke);
  await app.invoke("new_session", { config: online });
  const invoke = (command, args) => app.invoke(command, args);
  const operation = new BackendComputation(invoke, "genmove", {}, 1);
  let paused = true;
  const result = operation.result(() => paused);
  await new Promise((resolve) => setTimeout(resolve, 15));
  assert.equal((await app.invoke("get_state")).moveCount, 0);
  await operation.cancel();
  paused = false;
  await assert.rejects(result, /中断/);
  assert.equal((await app.invoke("get_state")).moveCount, 0);
});

test("undo and redo restore the exact variation after multiple steps and a reload", async () => {
  const storage = memory(), app = new ApplicationController(unavailable, storage);
  await app.invoke("load_sgf", { text: "(;SZ[9];B[aa](;W[bb])(;W[cc];B[];W[dd]))" });
  await app.invoke("goto_node", { path: [0, 1, 0, 0] });
  const before = await app.invoke("get_state");
  for (let i = 0; i < 3; i++) await app.invoke("undo_move");
  await app.invoke("set_comment", { comment: "comment preserves the forward path" });
  const restored = new ApplicationController(unavailable, storage);
  for (let i = 0; i < 3; i++) await restored.invoke("redo_move");
  const after = await restored.invoke("get_state");
  assert.deepEqual(after.currentPath, before.currentPath);
  assert.deepEqual({ ...after.game, moves: after.game.moves.map(({ comment, ...move }) => move) }, before.game);
  assert.equal(after.game.moves[0].comment, "comment preserves the forward path");
  assert.deepEqual(after.redoPath, []);
  await assert.rejects(restored.invoke("redo_move"), /進める手/);
  assert.deepEqual(await restored.invoke("get_state"), after);
});

test("a new move replaces the forward route while preserving the old branch", async () => {
  const app = new ApplicationController(unavailable);
  await app.invoke("load_sgf", { text: "(;SZ[9];B[aa];W[bb];B[cc])" });
  await app.invoke("undo_move");
  const undone = await app.invoke("get_state");
  await assert.rejects(app.invoke("play_move", { color: "black", vertex: "A9" }));
  assert.deepEqual(await app.invoke("get_state"), undone);
  let state = await app.invoke("play_move", { color: "black", vertex: "D6" });
  assert.deepEqual(state.redoPath, []);
  assert.equal(state.moveHistory.length, 4);
  await app.invoke("undo_move");
  state = await app.invoke("redo_move");
  assert.equal(state.game.moves[2].vertex, "D6");
  state = await app.invoke("goto_node", { path: [0, 0, 0] });
  assert.equal(state.game.moves[2].vertex, "C7");
});

test("move-history analysis maps requested segment turns to the correct positions without moving the board", async () => {
  let request;
  const app = new ApplicationController(async (command, args) => {
    if (command === "start_computation") { request = args; return { id: "history", status: "running", result: null }; }
    return { id: "history", status: "completed", result: request.turnsBySegment.flatMap((turns, segmentIndex) => turns.map((turnNumber) => ({ segmentIndex, turnNumber, winrate: 0.5, scoreLead: segmentIndex * 100 + turnNumber }))).reverse() };
  });
  await app.invoke("new_session", { config: online });
  await app.invoke("load_sgf", { text: "(;SZ[9];B[aa];AE[aa]PL[W];W[bb])" });
  const before = await app.invoke("get_state");
  const keys = before.moveHistory.flatMap((entry) => [entry.beforePositionKey, entry.positionKey]);
  await app.invoke("start_computation", { command: "analyze_move_history", args: { positionKeys: keys } });
  await app.invoke("get_computation", { id: "history" });
  const result = await app.invoke("accept_computation", { id: "history" });
  assert.equal(request.includeSegments, true);
  assert.deepEqual(request.turnsBySegment, [[0, 1], [0, 1]]);
  assert.equal(result.find((point) => point.positionKey === before.moveHistory[0].positionKey).scoreLead, 1);
  assert.equal(result.find((point) => point.positionKey === before.moveHistory[1].beforePositionKey).scoreLead, 100);
  assert.deepEqual(await app.invoke("get_state"), before);
  await app.invoke("start_computation", { command: "analyze_move_history", args: { positionKeys: [before.moveHistory[1].positionKey] } });
  assert.deepEqual(request.turnsBySegment, [[], [1]]);
});
