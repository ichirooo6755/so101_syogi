import assert from "node:assert/strict";
import test from "node:test";
import iconv from "iconv-lite";
import { editRecord, enginePosition, exportRecord, importRecord, newRecord, recordSnapshot } from "../src/record.ts";

test("Sabaki preserves collections, every variation, comments and unknown properties", () => {
  const document = importRecord(String.raw`(;SZ[9]C[root]PB[黒]XX[a\:b][c];B[aa](;C[annotation];W[bb]LB[bb:A\:B]TR[cc:dd])(;W[ee]N[side]))(;SZ[13]GN[second];B[ff])`);
  assert.equal(document.games.length, 2);
  editRecord(document, "goto_node", { path: [0, 1] });
  editRecord(document, "set_comment", { comment: "edited ] \\\ntext" });
  const restored = importRecord(exportRecord(document));
  assert.deepEqual(restored.games[0].root.children[0].children[0].data.C, ["annotation"]);
  assert.deepEqual(restored.games[0].root.children[0].children[1].data.C, ["edited ] \\\ntext"]);
  assert.deepEqual(restored.games[0].root.data.XX, ["a:b", "c"]);
  assert.deepEqual(restored.games[0].root.children[0].children[0].children[0].data.LB, ["bb:A:B"]);
  assert.equal(exportRecord(restored), exportRecord(document));
});

test("undo retains continuations and playing an existing move reuses its branch", () => {
  const document = newRecord(9);
  editRecord(document, "play_move", { color: "black", vertex: "A9" });
  editRecord(document, "play_move", { color: "white", vertex: "B8" });
  editRecord(document, "undo_move", {});
  editRecord(document, "play_move", { color: "white", vertex: "C7" });
  editRecord(document, "undo_move", {});
  editRecord(document, "play_move", { color: "white", vertex: "B8" });
  const state = recordSnapshot(document);
  assert.deepEqual(state.currentPath, [0, 0]);
  assert.equal(document.games[0].root.children[0].children.length, 2);
  assert.equal(state.game.signMap[1][1], -1);
  assert.equal(state.game.signMap[2][2], 0);
  assert.equal(importRecord(exportRecord(document)).games[0].root.children[0].children.length, 2);
});

test("setup edits, compressed stones and PL create exact engine segments", () => {
  const document = importRecord("(;SZ[9]HA[3]AB[aa:ab][cc]AW[ee]PL[W];W[ff];AE[aa]AB[hh]PL[B];B[ii])");
  const state = recordSnapshot(document), position = enginePosition(document);
  assert.equal(state.game.signMap[0][0], 0);
  assert.equal(state.game.signMap[1][0], 1);
  assert.equal(state.game.signMap[4][4], -1);
  assert.equal(state.game.captures.black, 0);
  assert.equal(position.nextPlayer, "W");
  assert.equal(position.segments.length, 2);
  assert.deepEqual(position.segments.map((segment) => [segment.initialPlayer, segment.moveOffset, segment.moves]), [["W", 0, [["W", "F4"]]], ["B", 1, [["B", "J1"]]]]);
  assert.ok(position.segments[1].initialStones.some(([color, vertex]) => color === "B" && vertex === "H2"));
});

test("square and 25-line boards, consecutive colors and legacy passes replay", () => {
  let document = importRecord("(;SZ[13:13];B[mi];B[aa];W[])");
  let state = recordSnapshot(document);
  assert.equal(state.boardHeight, 13);
  assert.equal(state.game.signMap[8][12], 1);
  assert.deepEqual(state.game.moves.map((move) => move.vertex), ["N5", "A13", "pass"]);
  document = importRecord("(;SZ[25];B[yy];W[tt])");
  assert.deepEqual(recordSnapshot(document).game.moves.map((move) => move.vertex), ["Z1", "U6"]);
  assert.equal(recordSnapshot(importRecord("(;SZ[19];B[tt])")).game.moves[0].vertex, "pass");
});

test("rectangular SGF is rejected, including an unselected collection member", () => {
  for (const text of ["(;SZ[13:9])", "(;SZ[9:13])", "(;SZ[19];B[aa])(;SZ[13:9])"]) {
    assert.throws(() => importRecord(text), /正方形/);
  }
});

test("NZ suicide removes the group and updates captured stones", () => {
  const document = importRecord("(;SZ[3]RU[NZ]AW[ab][ba][cb][bc]PL[B];B[bb])");
  const state = recordSnapshot(document);
  assert.equal(state.game.signMap[1][1], 0);
  assert.equal(state.game.captures.white, 1);
});

test("SGF charsets are decoded per collection member before Sabaki tokenization", () => {
  const bytes = Buffer.concat([
    iconv.encode("(;PB[ソ]CA[Shift_JIS]C[日本語]SZ[9])", "shift_jis"),
    iconv.encode("(;CA[ISO-8859-1]PB[André]SZ[13])", "latin1"),
    Buffer.from("(;CA[UTF-8]PB[白]SZ[19])"),
  ]);
  const document = importRecord(bytes);
  assert.deepEqual(document.games.map((game) => game.root.data.PB[0]), ["ソ", "André", "白"]);
  assert.equal(document.games[0].root.data.C[0], "日本語");
  assert.deepEqual(importRecord(exportRecord(document)).games.map((game) => game.root.data.PB[0]), ["ソ", "André", "白"]);
  const fake = Buffer.from(String.raw`(;PB[A]C[CA[Shift_JIS\] 日本語]SZ[9])`);
  assert.equal(importRecord(fake).games[0].root.data.C[0], "CA[Shift_JIS] 日本語");
});

test("invalid and truncated SGF, including invalid side branches, is rejected", () => {
  for (const text of ["", "garbage", ";B[aa]", "(;SZ[9]", "()", "(;SZ[0])", "(;SZ[26])", "(;KM[nan])", "(;SZ[9];B[aa]W[bb])", "(;SZ[9]AB[aa]AW[aa])", "(;GM[2])", "(;SZ[9];B[aa](;W[bb])(;W[zz]))", "(;SZ[9]C[a]C[b])", "(;SZ[9](;B[aa]);W[bb])", "(;SZ[9];SZ[13])", "(;SZ[9]LB[aa])", "(;SZ[9]PL[red])"]) {
    assert.throws(() => importRecord(text), undefined, text);
  }
});

test("unknown rules stay editable and fail explicitly when requesting KataGo", () => {
  const document = importRecord("(;SZ[9]RU[House rules];B[aa])");
  editRecord(document, "set_comment", { comment: "kept" });
  assert.match(exportRecord(document), /RU\[House rules\]/);
  assert.throws(() => enginePosition(document), /KataGo/);
});

test("a long record retains every annotation node on a Sabaki round trip", () => {
  const document = importRecord("(;SZ[9]" + ";C[node]".repeat(1800) + ")");
  assert.equal(document.games[0].path.length, 1800);
  assert.equal(importRecord(exportRecord(document)).games[0].path.length, 1800);
});
