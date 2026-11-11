import assert from "node:assert/strict";
import test from "node:test";
import { createGame, parseVertex, playMove, undoMove } from "../src/game.ts";

test("a new game is empty and black moves first on every board size", () => {
  for (const size of [9, 13, 19]) {
    const game = createGame(size);
    assert.equal(game.signMap.length, size);
    assert.equal(game.signMap.flat().filter(Boolean).length, 0);
    assert.equal(game.nextSign, 1);
    assert.equal(game.moves.length, 0);
  }
});

test("fixed handicap uses distinct points and white moves first", () => {
  for (const size of [9, 13, 19]) {
    for (let handicap = 1; handicap <= 9; handicap++) {
      const game = createGame(size, handicap);
      assert.equal(game.signMap.flat().filter((sign) => sign === 1).length, handicap);
      assert.equal(game.nextSign, -1);
    }
  }
});

test("moves, passes and undo restore stones, turn, last move and record", () => {
  const initial = createGame(9);
  const first = playMove(initial, [3, 5]);
  const passed = playMove(first, null);
  assert.deepEqual(passed.moves, [
    { moveNumber: 1, color: "black", vertex: "D4" },
    { moveNumber: 2, color: "white", vertex: "pass" },
  ]);
  assert.equal(passed.nextSign, 1);
  assert.equal(passed.lastVertex, null);
  assert.deepEqual(undoMove(passed), first);
  assert.deepEqual(undoMove(first), initial);
  assert.equal(undoMove(initial), initial);
  assert.equal(initial.signMap[5][3], 0);
});

test("capture removes stones and undo restores them", () => {
  const game = createGame(9);
  game.signMap[1][1] = -1;
  game.signMap[0][1] = game.signMap[1][0] = game.signMap[1][2] = 1;
  const captured = playMove(game, [1, 2]);
  assert.equal(captured.signMap[1][1], 0);
  assert.equal(captured.signMap[2][1], 1);
  assert.equal(captured.ko, null);
  assert.deepEqual(undoMove(captured), game);
});

test("suicide, occupied and out of board moves leave the position intact", () => {
  const game = createGame(9);
  game.signMap[0][1] = game.signMap[1][0] = game.signMap[1][2] = game.signMap[2][1] = -1;
  const before = structuredClone(game);
  for (const vertex of [[1, 1], [1, 0], [9, 0], [-1, 0]]) {
    assert.throws(() => playMove(game, vertex));
    assert.deepEqual(game, before);
  }
});

test("ko blocks recapture, a pass clears it, and undo restores it", () => {
  const game = createGame(9);
  for (const [x, y] of [[0, 1], [2, 1], [1, 0]]) game.signMap[y][x] = 1;
  for (const [x, y] of [[1, 1], [0, 2], [2, 2], [1, 3]]) game.signMap[y][x] = -1;
  const captured = playMove(game, [1, 2]);
  assert.deepEqual(captured.ko, [1, 1]);
  assert.throws(() => playMove(captured, [1, 1]), /コウ/);
  const passed = playMove(captured, null);
  assert.equal(passed.ko, null);
  assert.deepEqual(undoMove(passed), captured);
});

test("engine coordinates respect board size and the skipped I column", () => {
  assert.deepEqual(parseVertex("K4", 19), [9, 15]);
  assert.deepEqual(parseVertex("j1", 9), [8, 8]);
  assert.equal(parseVertex("PASS", 9), null);
  for (const value of ["Q14", "A10", "I1", "A0", "resign"]) {
    assert.throws(() => parseVertex(value, 9));
  }
});
