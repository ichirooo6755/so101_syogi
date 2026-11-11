import type { Sign, Vertex } from "@sabaki/shudan";

export type Stone = -1 | 1;
interface Position {
  signMap: Sign[][];
  nextSign: Stone;
  ko: Vertex | null;
  lastVertex: Vertex | null;
  captures: { black: number; white: number };
}

export interface GameState extends Position {
  history: Position[];
  moves: { moveNumber: number; color: "black" | "white"; vertex: string; comment?: string }[];
}

export const columns = "ABCDEFGHJKLMNOPQRSTUVWXYZ";
const sameVertex = (left: Vertex | null, right: Vertex) => left?.[0] === right[0] && left[1] === right[1];

export function createGame(size: number, handicap = 0, height = size): GameState {
  if (![size, height].every((value) => Number.isInteger(value) && value >= 1 && value <= 25)) throw new Error("盤の縦横は1〜25で指定してください");
  if (height !== size) throw new Error(`正方形の盤面のみ対応しています（${size}×${height}は使用できません）`);
  if (!Number.isInteger(handicap) || handicap < 0 || handicap > 9 || (handicap > 0 && (height !== size || ![9, 13, 19].includes(size)))) throw new Error("置き石は9・13・19路盤の0〜9子で指定してください");
  const signMap: Sign[][] = Array.from({ length: height }, () => Array<Sign>(size).fill(0));
  const low = size === 9 ? 2 : 3;
  const high = size - low - 1;
  const center = Math.floor(size / 2);
  const points: Vertex[] = [[low, high], [high, low], [high, high], [low, low]];
  if (handicap >= 6) points.push([low, center], [high, center]);
  if (handicap >= 8) points.push([center, low], [center, high]);
  if (handicap === 5 || handicap === 7 || handicap === 9) points.push([center, center]);
  for (const [x, y] of points.slice(0, handicap)) signMap[y][x] = 1;
  return { signMap, nextSign: handicap > 0 ? -1 : 1, ko: null, lastVertex: null, captures: { black: 0, white: 0 }, history: [], moves: [] };
}

export function parseVertex(label: string, size: number, height = size): Vertex | null {
  if (label.trim().toLowerCase() === "pass") return null;
  const match = /^([A-HJ-Z])([1-9]\d*)$/i.exec(label.trim());
  if (!match) throw new Error(`無効な座標: ${label}`);
  const x = columns.indexOf(match[1].toUpperCase());
  const y = height - Number(match[2]);
  if (x >= size || y < 0 || y >= height) throw new Error(`盤外の座標: ${label}`);
  return [x, y];
}

export function playMove(game: GameState, vertex: Vertex | null, options: { color?: Stone; allowSuicide?: boolean; ignoreKo?: boolean; recordHistory?: boolean } = {}): GameState {
  const size = game.signMap[0].length, height = game.signMap.length;
  const color = options.color ?? game.nextSign;
  const signMap = game.signMap.map((row) => [...row]);
  const prisoners = { ...game.captures };
  let ko: Vertex | null = null;
  if (vertex !== null) {
    const [x, y] = vertex;
    if (!Number.isInteger(x) || !Number.isInteger(y) || x < 0 || x >= size || y < 0 || y >= height) {
      throw new Error("盤外には着手できません");
    }
    if (signMap[y][x] !== 0) throw new Error("石のある場所には着手できません");
    if (!options.ignoreKo && sameVertex(game.ko, vertex)) throw new Error("コウの直後には取り返せません");
    signMap[y][x] = color;
    const captures: Vertex[] = [];
    for (const neighbor of neighbors(vertex, size, height)) {
      if (signMap[neighbor[1]][neighbor[0]] !== -color) continue;
      const group = groupAt(signMap, neighbor);
      if (liberties(signMap, group).length > 0) continue;
      captures.push(...group);
      for (const [cx, cy] of group) signMap[cy][cx] = 0;
    }
    const group = groupAt(signMap, vertex);
    const emptyPoints = liberties(signMap, group);
    if (emptyPoints.length === 0) {
      if (!options.allowSuicide) throw new Error("自殺手には着手できません");
      for (const [gx, gy] of group) signMap[gy][gx] = 0;
      prisoners[color === 1 ? "white" : "black"] += group.length;
    }
    prisoners[color === 1 ? "black" : "white"] += captures.length;
    if (captures.length === 1 && group.length === 1 && emptyPoints.length === 1) ko = captures[0];
  }
  const { history, moves, ...previous } = game;
  return {
    signMap,
    nextSign: color === 1 ? -1 : 1,
    ko,
    lastVertex: vertex,
    captures: prisoners,
    history: options.recordHistory === false ? [] : [...history, previous],
    moves: [...moves, {
      moveNumber: moves.length + 1,
      color: color === 1 ? "black" : "white",
      vertex: vertex === null ? "pass" : `${columns[vertex[0]]}${height - vertex[1]}`,
    }],
  };
}

export function undoMove(game: GameState): GameState {
  const previous = game.history[game.history.length - 1];
  return previous ? { ...previous, history: game.history.slice(0, -1), moves: game.moves.slice(0, -1) } : game;
}

function neighbors([x, y]: Vertex, size: number, height = size): Vertex[] {
  return ([[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]] as Vertex[])
    .filter(([nx, ny]) => nx >= 0 && nx < size && ny >= 0 && ny < height);
}

function groupAt(map: Sign[][], start: Vertex): Vertex[] {
  const color = map[start[1]][start[0]];
  const points: Vertex[] = [];
  const pending = [start];
  const seen = new Set<number>();
  while (pending.length > 0) {
    const vertex = pending.pop()!;
    const [x, y] = vertex;
    const key = y * map[0].length + x;
    if (seen.has(key)) continue;
    seen.add(key);
    points.push(vertex);
    pending.push(...neighbors(vertex, map[0].length, map.length).filter(([nx, ny]) => map[ny][nx] === color));
  }
  return points;
}

function liberties(map: Sign[][], group: Vertex[]): Vertex[] {
  const empty = new Map<number, Vertex>();
  for (const point of group) {
    for (const [x, y] of neighbors(point, map[0].length, map.length)) {
      if (map[y][x] === 0) empty.set(y * map[0].length + x, [x, y]);
    }
  }
  return [...empty.values()];
}
