import assert from "node:assert/strict";
import test from "node:test";
import { editRecord, importRecord, recordSnapshot, replay } from "../src/record.ts";
import { historyLine, judgeMove } from "../src/moveReview.ts";

test("move history contains only actual moves, GTP coordinates, passes and separate variations", () => {
  const document = importRecord("(;SZ[9]C[root];B[aa];C[note](;W[bb];B[])(;W[cc]))");
  const state = recordSnapshot(document);
  assert.deepEqual(state.moveHistory.map(({ moveNumber, color, vertex }) => [moveNumber, color, vertex]), [[1, "black", "A9"], [2, "white", "B8"], [3, "black", "pass"], [2, "white", "C7"]]);
  const first = state.moveHistory[0];
  const sides = state.moveHistory.filter((entry) => entry.moveNumber === 2);
  assert.equal(sides[0].beforePositionKey, first.positionKey);
  assert.equal(sides[1].beforePositionKey, first.positionKey);
  assert.notEqual(sides[0].positionKey, sides[1].positionKey);
  assert.equal(sides[1].branchDepth, 1);
});

test("history follows the undone variation and keeps future moves available", () => {
  const document = importRecord("(;SZ[9];B[aa](;W[bb])(;W[cc];B[dd]))");
  editRecord(document, "goto_node", { path: [0, 1, 0] });
  editRecord(document, "undo_move", {});
  editRecord(document, "undo_move", {});
  const line = historyLine(recordSnapshot(document));
  assert.deepEqual(line.path, [0, 1, 0]);
  assert.deepEqual(line.entries.map((entry) => entry.vertex), ["A9", "C7", "D6"]);
  assert.deepEqual(historyLine(recordSnapshot(document), false).entries.map((entry) => entry.vertex), ["A9"]);
});

test("setup boundaries retain both before and after positions at the same move number", () => {
  const document = importRecord("(;SZ[9];B[aa];AE[aa]AB[bb]PL[W];W[cc])");
  const state = recordSnapshot(document);
  const positions = replay(document.games[0]).reviewPositions;
  assert.deepEqual(positions.map(({ segmentIndex, turnNumber }) => [segmentIndex, turnNumber]), [[0, 0], [0, 1], [1, 0], [1, 1]]);
  assert.equal(state.moveHistory[0].positionKey, positions[1].positionKey);
  assert.equal(state.moveHistory[1].beforePositionKey, positions[2].positionKey);
  assert.notEqual(positions[1].positionKey, positions[2].positionKey);
  editRecord(document, "set_comment", { comment: "only a comment" });
  assert.deepEqual(replay(document.games[0]).reviewPositions, positions);
  editRecord(document, "goto_node", { path: [] });
  editRecord(document, "set_node_properties", { properties: { KM: ["7.5"] } });
  assert.notEqual(recordSnapshot(document).moveHistory[0].positionKey, state.moveHistory[0].positionKey);
});

test("move quality uses the player's score loss, including White and threshold boundaries", () => {
  const value = (scoreLead) => ({ positionKey: "", scoreLead, winrate: 0.5 });
  for (const [loss, label] of [[0, "良手"], [0.99, "良手"], [1, "疑問手"], [3, "悪手"], [6, "大悪手"]]) {
    assert.equal(judgeMove({ color: "black" }, value(10), value(10 - loss)).label, label);
    assert.equal(judgeMove({ color: "white" }, value(10), value(10 + loss)).label, label);
  }
  assert.equal(judgeMove({ color: "black" }, undefined, value(10)).label, "未解析");
  assert.equal(judgeMove({ color: "white" }, value(10), value(8)).loss, 0);
});
