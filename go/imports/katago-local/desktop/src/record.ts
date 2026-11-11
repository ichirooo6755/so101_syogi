import type { Vertex } from "@sabaki/shudan";
import type { FlowMode, InitialPosition, SessionState } from "./backend";
import { columns, createGame, parseVertex, playMove, type GameState, type Stone } from "./game.ts";
import { cloneTree, parseSgf, parseSgfBytes, writeSgf, type SgfNode } from "./sgf.ts";

export type EngineColor = "B" | "W";
export interface EngineSegment {
  initialStones: [EngineColor, string][];
  initialPlayer: EngineColor;
  moves: [EngineColor, string][];
  moveOffset: number;
}
export interface EnginePosition {
  boardXSize: number;
  boardYSize: number;
  komi: number;
  rules: string;
  handicap: number;
  nextPlayer: EngineColor;
  segments: EngineSegment[];
}
export interface ReviewPosition {
  segmentIndex: number;
  turnNumber: number;
  positionKey: string;
}
export interface RecordGame { root: SgfNode; path: number[]; redoPath?: number[] }
export interface RecordDocument {
  id: string;
  mode: FlowMode;
  active: boolean;
  fileName: string | null;
  games: RecordGame[];
  gameIndex: number;
}

const rootOnly = new Set("GM FF CA AP SZ ST".split(" "));
const single = new Set("B W C N PL HA KM GM FF CA AP SZ ST RU PB PW BR WR BT WT DT EV GN GC ON OT PC RE RO SO TM US AN CP BL WL OB OW MN KO GB GW DM UC TE BM DO IT V HO FG PM".split(" "));
const pointLists = new Set("AB AW AE CR MA SL SQ TR TB TW DD VW".split(" "));
const simpleText = new Set("AP CA RU PB PW BR WR BT WT DT EV GN ON OT PC RE RO SO TM US AN CP N LB FG".split(" "));
const setupKeys = ["AB", "AW", "AE", "PL"];
const value = (node: SgfNode, key: string, fallback = "") => node.data[key]?.[0] ?? fallback;
const colorName = (sign: Stone): EngineColor => sign === 1 ? "B" : "W";
export const gtp = (vertex: Vertex | null, height: number) => vertex === null ? "pass" : `${columns[vertex[0]]}${height - vertex[1]}`;

export function rulesPreset(description: string): string | null {
  const name = description.trim().toLowerCase().replace(/[_ ]/g, "-");
  const preset = ({ japan: "japanese", "japanese-rules": "japanese", china: "chinese", nz: "new-zealand", newzealand: "new-zealand" } as Record<string, string>)[name] ?? name;
  return ["japanese", "chinese", "korean", "aga", "new-zealand", "tromp-taylor"].includes(preset) ? preset : null;
}

export function metadata(root: SgfNode, fileName: string | null = null): Record<string, string | number | null> & { boardSize: number; height: number; komi: number; handicap: number; ruleset: string } {
  if (value(root, "GM", "1") !== "1" || !["1", "2", "3", "4"].includes(value(root, "FF", "4"))) throw new Error("GoのSGF FF[1〜4]のみ対応しています");
  const dimensions = value(root, "SZ", "19").split(":");
  if (dimensions.length > 2 || dimensions.some((part) => !/^\d+$/.test(part) || Number(part) < 1 || Number(part) > 25)) throw new Error("SGFの盤サイズは縦横1〜25で指定してください");
  if (Number(dimensions[0]) !== Number(dimensions[dimensions.length - 1])) throw new Error(`正方形の盤面のみ対応しています（${dimensions.join("×")}のSGFは読み込めません）`);
  const komiText = value(root, "KM", "6.5"), handicapText = value(root, "HA", "0");
  const komi = Number(komiText), handicap = Number(handicapText);
  if (!komiText.trim() || !Number.isFinite(komi) || !/^\d+$/.test(handicapText) || !Number.isSafeInteger(handicap)) throw new Error("SGFのコミまたは置き石数が不正です");
  const rules = value(root, "RU", "japanese");
  return {
    boardSize: Number(dimensions[0]), height: Number(dimensions[dimensions.length - 1]), komi, handicap,
    ruleset: rulesPreset(rules) ?? rules, fileName,
    blackName: value(root, "PB", "Black"), whiteName: value(root, "PW", "White"),
    result: value(root, "RE"), gameName: value(root, "GN"), date: value(root, "DT"),
    event: value(root, "EV"), round: value(root, "RO"), place: value(root, "PC"),
    blackRank: value(root, "BR"), whiteRank: value(root, "WR"),
  };
}

export function sgfPoint(text: string, width: number, height: number): Vertex {
  if (!/^[a-y]{2}$/.test(text)) throw new Error(`SGF座標が不正です: ${text}`);
  const vertex: Vertex = [text.charCodeAt(0) - 97, text.charCodeAt(1) - 97];
  if (vertex[0] >= width || vertex[1] >= height) throw new Error(`SGF座標が盤外です: ${text}`);
  return vertex;
}
function sgfMove(text: string, width: number, height: number): Vertex | null {
  return text === "" || (text === "tt" && Math.max(width, height) <= 19) ? null : sgfPoint(text, width, height);
}
export function expandPoints(values: string[], width: number, height: number): Vertex[] {
  const points: Vertex[] = [];
  for (const text of values) {
    const parts = text.split(":"), start = sgfPoint(parts[0], width, height);
    if (parts.length === 1) { points.push(start); continue; }
    if (parts.length !== 2) throw new Error(`SGFの座標範囲が不正です: ${text}`);
    const end = sgfPoint(parts[1], width, height);
    if (start[0] > end[0] || start[1] > end[1]) throw new Error(`SGFの座標範囲が逆です: ${text}`);
    for (let y = start[1]; y <= end[1]; y++) for (let x = start[0]; x <= end[0]; x++) points.push([x, y]);
  }
  return points;
}

export function validateTree(root: SgfNode): void {
  const { boardSize: width, height } = metadata(root), stack = [root];
  while (stack.length) {
    const node = stack.pop()!, props = node.data;
    for (const [key, values] of Object.entries(props)) {
      if (!/^[A-Z]+$/.test(key) || !Array.isArray(values) || !values.length || !values.every((item) => typeof item === "string")) throw new Error(`SGFプロパティが不正です: ${key}`);
      if (single.has(key) && values.length !== 1) throw new Error(`SGFプロパティ ${key} は単一値です`);
      if (node !== root && rootOnly.has(key)) throw new Error(`${key} はSGFルート専用です`);
      if (simpleText.has(key)) props[key] = values.map((item) => item.replace(/\s/g, " "));
    }
    if (props.B && props.W) throw new Error("同じSGFノードに黒白両方の着手は置けません");
    if ((props.B || props.W) && setupKeys.some((key) => key in props)) throw new Error("着手と配置変更は別のSGFノードにしてください");
    if (props.PL && !["B", "W"].includes(value(node, "PL"))) throw new Error("PLはBまたはWで指定してください");
    for (const color of ["B", "W"]) if (props[color]) sgfMove(value(node, color), width, height);
    const setup = new Set<string>();
    for (const key of pointLists) if (props[key]) {
      const points = expandPoints(props[key][0] === "" && !setupKeys.includes(key) ? [] : props[key], width, height);
      if (setupKeys.includes(key)) for (const point of points) {
        const id = point.join(",");
        if (setup.has(id)) throw new Error("SGFの配置指定が重複しています");
        setup.add(id);
      }
    }
    for (const key of ["LB", "AR", "LN"]) for (const text of props[key] ?? []) {
      const separator = text.indexOf(":");
      if (separator < 0) throw new Error(`SGFプロパティ ${key} の複合値が不正です`);
      sgfPoint(text.slice(0, separator), width, height);
      if (key !== "LB") sgfPoint(text.slice(separator + 1), width, height);
    }
    stack.push(...node.children);
  }
}

export function nodeAt(game: RecordGame, path = game.path): SgfNode {
  let node = game.root;
  for (const index of path) {
    if (!Number.isInteger(index) || index < 0 || !node.children[index]) throw new Error("棋譜ノードの位置が不正です");
    node = node.children[index];
  }
  return node;
}

function initialPositionKey(game: RecordGame): string {
  const info = metadata(game.root);
  return JSON.stringify([info.boardSize, info.height, info.komi, info.ruleset, info.handicap]);
}

function advancePositionKey(key: string, node: SgfNode): string {
  if (!["B", "W", ...setupKeys].some((name) => name in node.data)) return key;
  const keys = ["B", "W", ...setupKeys, "KO"].filter((name) => name in node.data);
  return keys.length ? key + JSON.stringify(keys.map((name) => [name, node.data[name]])) : key;
}

export function replay(game: RecordGame): { board: GameState; segments: EngineSegment[]; reviewPositions: ReviewPosition[] } {
  const meta = metadata(game.root), width = meta.boardSize, height = meta.height;
  let board = createGame(width, 0, height);
  board.nextSign = meta.handicap >= 2 ? -1 : 1;
  const stones = (): [EngineColor, string][] => board.signMap.flatMap((row, y) => row.flatMap((sign, x) => sign === 0 ? [] : [[colorName(sign as Stone), gtp([x, y], height)] as [EngineColor, string]]));
  const segment = (): EngineSegment => ({ initialStones: stones(), initialPlayer: colorName(board.nextSign), moves: [], moveOffset: board.moves.length });
  const segments = [segment()];
  let positionKey = initialPositionKey(game);
  const reviewPositions: ReviewPosition[] = [{ segmentIndex: 0, turnNumber: 0, positionKey }];
  const nodes = [game.root];
  let cursor = game.root;
  for (const index of game.path) { cursor = nodeAt({ root: cursor, path: [index] }); nodes.push(cursor); }
  for (const node of nodes) {
    const props = node.data;
    positionKey = advancePositionKey(positionKey, node);
    if (setupKeys.some((key) => key in props)) {
      board = { ...board, signMap: board.signMap.map((row) => [...row]), ko: null, lastVertex: null };
      for (const [key, sign] of [["AE", 0], ["AB", 1], ["AW", -1]] as const) for (const [x, y] of expandPoints(props[key] ?? [], width, height)) board.signMap[y][x] = sign;
      if (props.PL) board.nextSign = value(node, "PL") === "B" ? 1 : -1;
      const last = segments[segments.length - 1];
      if (!last.moves.length && last.moveOffset === board.moves.length) {
        segments[segments.length - 1] = segment();
        reviewPositions.pop();
      }
      else segments.push(segment());
      reviewPositions.push({ segmentIndex: segments.length - 1, turnNumber: 0, positionKey });
    }
    for (const color of ["B", "W"] as const) if (props[color]) {
      const vertex = sgfMove(value(node, color), width, height);
      board = playMove(board, vertex, { color: color === "B" ? 1 : -1, allowSuicide: ["new-zealand", "tromp-taylor"].includes(meta.ruleset), ignoreKo: "KO" in props, recordHistory: false });
      if (props.C) board.moves[board.moves.length - 1].comment = value(node, "C");
      segments[segments.length - 1].moves.push([color, gtp(vertex, height)]);
      reviewPositions.push({ segmentIndex: segments.length - 1, turnNumber: segments[segments.length - 1].moves.length, positionKey });
    }
  }
  if (!("B" in cursor.data || "W" in cursor.data)) board.lastVertex = null;
  return { board, segments, reviewPositions };
}

function initialPath(root: SgfNode, initial: InitialPosition): number[] {
  const path: number[] = [];
  if (initial === "start") return path;
  if (!["last", "problem"].includes(initial)) throw new Error("読み込み位置が不正です");
  while (root.children.length && (initial !== "problem" || root.children.length === 1)) { path.push(0); root = root.children[0]; }
  return path;
}

export function importRecord(source: string | Uint8Array, initial: InitialPosition = "last", fileName: string | null = null): RecordDocument {
  const roots = typeof source === "string" ? parseSgf(source) : parseSgfBytes(source);
  roots.forEach(validateTree);
  const games = roots.map((root) => ({ root, path: initialPath(root, initial) }));
  games.forEach(replay);
  return { id: crypto.randomUUID(), mode: "import", active: true, fileName, games, gameIndex: 0 };
}

export function newRecord(size = 19, komi = 6.5, rules = "japanese", handicap = 0): RecordDocument {
  if (!Number.isFinite(komi) || !rulesPreset(rules)) throw new Error("コミまたはルールが不正です");
  const board = createGame(size, handicap);
  const root: SgfNode = { id: 0, parentId: null, children: [], data: { GM: ["1"], FF: ["4"], CA: ["UTF-8"], SZ: [String(size)], KM: [String(komi)], RU: [rules] } };
  if (handicap) {
    root.data.HA = [String(handicap)]; root.data.PL = ["W"];
    root.data.AB = board.signMap.flatMap((row, y) => row.flatMap((sign, x) => sign === 1 ? [String.fromCharCode(97 + x, 97 + y)] : []));
  }
  return { id: crypto.randomUUID(), mode: "play", active: false, fileName: null, games: [{ root, path: [] }], gameIndex: 0 };
}

export function cloneDocument(document: RecordDocument): RecordDocument {
  return { ...document, games: document.games.map((game) => ({ root: cloneTree(game.root), path: [...game.path], ...(game.redoPath ? { redoPath: [...game.redoPath] } : {}) })) };
}
export const exportRecord = (document: RecordDocument, normalize = true) => writeSgf(document.games.map((game) => game.root), normalize);

export function playRecord(document: RecordDocument, color: string, label: string): void {
  const game = document.games[document.gameIndex], { board } = replay(game);
  const expected = colorName(board.nextSign), requested = ({ black: "B", white: "W" } as Record<string, string>)[color] ?? color;
  if (expected !== requested) throw new Error(`現在の手番は${expected === "B" ? "黒" : "白"}です`);
  const meta = metadata(game.root), vertex = parseVertex(label, meta.boardSize, meta.height);
  playMove(board, vertex, { allowSuicide: ["new-zealand", "tromp-taylor"].includes(meta.ruleset), recordHistory: false });
  const parent = nodeAt(game), sgf = vertex === null ? "" : String.fromCharCode(vertex[0] + 97, vertex[1] + 97);
  let index = parent.children.findIndex((node) => node.data[expected]?.[0] === sgf && node.data[expected].length === 1);
  if (index < 0) { index = parent.children.length; parent.children.push({ id: crypto.randomUUID(), parentId: parent.id, data: { [expected]: [sgf] }, children: [] }); }
  game.path.push(index);
  game.redoPath = [];
}

export function editRecord(document: RecordDocument, command: string, args: Record<string, unknown>): void {
  const game = document.games[document.gameIndex];
  if (command === "play_move" || command === "pass_move") playRecord(document, String(args.color), command === "pass_move" ? "pass" : String(args.vertex));
  else if (command === "undo_move") {
    if (game.path.length) game.redoPath = [game.path.pop()!, ...(game.redoPath ?? [])];
  } else if (command === "redo_move") {
    const variation = Number(args.variation ?? game.redoPath?.[0] ?? 0);
    if (!Number.isInteger(variation) || variation < 0 || !nodeAt(game).children[variation]) throw new Error("進める手がありません");
    game.path.push(variation);
    game.redoPath = args.variation === undefined ? (game.redoPath ?? []).slice(1) : [];
  }
  else if (command === "goto_node") {
    if (!Array.isArray(args.path)) throw new Error("棋譜ノードの位置が不正です");
    game.path = [...args.path];
    game.redoPath = [];
  } else if (command === "select_game") {
    if (!Number.isInteger(args.index) || Number(args.index) < 0 || !document.games[Number(args.index)]) throw new Error("棋譜の選択位置が不正です");
    document.gameIndex = Number(args.index);
  } else if (command === "set_comment" || command === "set_node_properties") {
    const properties = command === "set_comment" ? { C: args.comment ? [args.comment] : [] } : args.properties;
    if (!properties || Array.isArray(properties) || typeof properties !== "object") throw new Error("SGFプロパティはオブジェクトで指定してください");
    const node = nodeAt(game);
    for (const [key, values] of Object.entries(properties)) {
      if (!/^[A-Z]+$/.test(key)) throw new Error(`SGFプロパティ名が不正です: ${key}`);
      if (!Array.isArray(values) || !values.every((item) => typeof item === "string")) throw new Error("SGFプロパティは文字列配列で指定してください");
      if (values.length) node.data[key] = [...values]; else delete node.data[key];
    }
    validateTree(game.root);
    if (command === "set_node_properties") game.redoPath = [];
  } else throw new Error(`未知の棋譜操作: ${command}`);
  nodeAt(document.games[document.gameIndex]);
  replay(document.games[document.gameIndex]);
}

export function enginePosition(document: RecordDocument): EnginePosition {
  const game = document.games[document.gameIndex], meta = metadata(game.root), rules = rulesPreset(meta.ruleset);
  if (!rules) throw new Error(`KataGoに対応するルールがありません: ${meta.ruleset}`);
  const { board, segments } = replay(game);
  return { boardXSize: meta.boardSize, boardYSize: meta.height, komi: meta.komi, rules, handicap: meta.handicap, nextPlayer: colorName(board.nextSign), segments };
}

export function recordSnapshot(document: RecordDocument, computation: SessionState["computation"] = null): SessionState {
  const game = document.games[document.gameIndex], meta = metadata(game.root, document.fileName), node = nodeAt(game), { board } = replay(game);
  const nodes: SessionState["nodes"] = [], moveHistory: SessionState["moveHistory"] = [];
  const stack: [SgfNode, number[], number, number, string][] = [[game.root, [], 0, 0, initialPositionKey(game)]];
  while (stack.length) {
    const [entry, path, previousMoveNumber, branchDepth, beforePositionKey] = stack.pop()!;
    const positionKey = advancePositionKey(beforePositionKey, entry);
    const color = entry.data.B ? "black" : entry.data.W ? "white" : null;
    const moveNumber = previousMoveNumber + (color ? 1 : 0);
    if (color) moveHistory.push({ path, moveNumber, color, vertex: gtp(sgfMove(value(entry, color === "black" ? "B" : "W"), meta.boardSize, meta.height), meta.height), branchDepth, beforePositionKey, positionKey });
    const move = entry.data.B ? `B ${value(entry, "B")}` : entry.data.W ? `W ${value(entry, "W")}` : "局面";
    nodes.push({ path, label: value(entry, "N", move), comment: value(entry, "C"), childCount: entry.children.length });
    for (let index = entry.children.length - 1; index >= 0; index--) stack.push([entry.children[index], [...path, index], moveNumber, branchDepth + (index > 0 ? 1 : 0), positionKey]);
  }
  return {
    id: document.id, title: String(meta.gameName || document.fileName || (document.mode === "play" ? "新規対局" : "棋譜セッション")),
    activeSession: document.active, mode: document.mode, engineStatus: computation ? "analyzing" : "idle", computation,
    moveCount: board.moves.length, boardSize: meta.boardSize, boardHeight: meta.height, komi: meta.komi, ruleset: meta.ruleset,
    metadata: meta, game: board, gameIndex: document.gameIndex, gameCount: document.games.length,
    games: document.games.map((entry, index) => { const info = metadata(entry.root); return { index, title: String(info.gameName || `${info.blackName} / ${info.whiteName}`) }; }),
    currentPath: [...game.path], redoPath: [...(game.redoPath ?? [])], properties: Object.fromEntries(Object.entries(node.data).map(([key, values]) => [key, [...values]])),
    variations: node.children.map((child, index) => ({ index, properties: Object.fromEntries(Object.entries(child.data).map(([key, values]) => [key, [...values]])) })), nodes, moveHistory,
  };
}
