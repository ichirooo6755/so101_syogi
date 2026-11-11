import sgf, { type SgfNode } from "@sabaki/sgf";
const { parse, stringify, tokenizeIter } = sgf;

export type { SgfNode } from "@sabaki/sgf";

/** Sabaki builds the tree. This guard rejects incomplete/ambiguous input that
 * its deliberately permissive parser would otherwise repair silently. */
export function parseSgf(text: string): SgfNode[] {
  text = text.replace(/^\uFEFF/, "");
  const frames: { node: boolean; branches: boolean; properties: Set<string> }[] = [];
  let property: string | null = null, hasValue = true, roots = 0;
  for (const token of tokenizeIter(text)) {
    if (property && !hasValue && token.type !== "c_value_type") throw new Error(`SGFプロパティ ${property} に値がありません`);
    const frame = frames[frames.length - 1];
    if (token.type === "parenthesis") {
      if (token.value === "(") {
        if (frame) { if (!frame.node) throw new Error("SGFノードがありません"); frame.branches = true; }
        else roots++;
        frames.push({ node: false, branches: false, properties: new Set() });
      } else {
        if (!frame?.node) throw new Error("SGFの括弧またはノードが不正です");
        frames.pop();
      }
      property = null;
    } else if (token.type === "semicolon") {
      if (!frame || frame.branches) throw new Error("SGFの分岐構造が不正です");
      frame.node = true; frame.properties = new Set(); property = null;
    } else if (token.type === "prop_ident") {
      if (!frame?.node || frame.branches) throw new Error("SGFプロパティの位置が不正です");
      property = token.value.replace(/[a-z]/g, "");
      if (!property || frame.properties.has(property)) throw new Error(`重複または不正なSGFプロパティ: ${property}`);
      frame.properties.add(property); hasValue = false;
    } else if (token.type === "c_value_type") {
      if (!property) throw new Error("SGFの値にプロパティ名がありません");
      hasValue = true;
    } else throw new Error(`SGFの${token.row + 1}行${token.col + 1}列が不正です`);
  }
  if (!roots || frames.length || (property && !hasValue)) throw new Error("SGFが空か、途中で切れています");
  return parse(text);
}

export function cloneTree(source: SgfNode): SgfNode {
  const copy = (node: SgfNode): SgfNode => ({ id: node.id, parentId: node.parentId, data: Object.fromEntries(Object.entries(node.data).map(([key, values]) => [key, [...values]])), children: [] });
  const root = copy(source), stack: [SgfNode, SgfNode][] = [[source, root]];
  while (stack.length) {
    const [from, to] = stack.pop()!;
    for (const child of from.children) { const cloned = copy(child); to.children.push(cloned); stack.push([child, cloned]); }
  }
  return root;
}

export function writeSgf(roots: SgfNode[], normalize = true): string {
  const output = roots.map(cloneTree);
  if (normalize) for (const root of output) Object.assign(root.data, { GM: ["1"], FF: ["4"], CA: ["UTF-8"] });
  return stringify(output, { linebreak: "", indent: "" });
}

const charset = (name: string) => ({ "shift-jis": "shift_jis", "sjis": "shift_jis", "cp932": "shift_jis", "utf8": "utf-8", "latin1": "iso-8859-1" }[name.toLowerCase()] ?? name.toLowerCase());

/** Decode before lexing: a Shift-JIS trail byte can equal an SGF backslash.
 * Only collection framing is scanned here; Sabaki parses every decoded tree. */
function decodeFirst(bytes: Uint8Array, encoding: string): { text: string; consumed: number } {
  const latin1 = ["iso-8859-1", "iso8859-1"].includes(encoding);
  const decoder = latin1 ? null : new TextDecoder(encoding, { fatal: true });
  let depth = 0, inValue = false, escaped = false;
  const chars: string[] = [];
  for (let index = 0; index < bytes.length; index++) {
    const chunk = decoder ? decoder.decode(bytes.subarray(index, index + 1), { stream: true }) : String.fromCharCode(bytes[index]);
    for (const char of chunk) {
      chars.push(char);
      if (inValue) {
        if (escaped) escaped = false;
        else if (char === "\\") escaped = true;
        else if (char === "]") inValue = false;
      } else if (char === "[") inValue = true;
      else if (char === "(") depth++;
      else if (char === ")") {
        if (--depth < 0) throw new Error("SGFの括弧が不正です");
        if (!depth) { decoder?.decode(); return { text: chars.join(""), consumed: index + 1 }; }
      } else if (!depth && !/\s|\uFEFF/.test(char)) throw new Error("SGFは棋譜ツリーから開始してください");
    }
  }
  throw new Error("SGFが途中で切れています");
}

export function parseSgfBytes(bytes: Uint8Array): SgfNode[] {
  const roots: SgfNode[] = [];
  while (bytes.some((byte) => ![9, 10, 13, 32].includes(byte))) {
    let ascii = "";
    for (const byte of bytes) ascii += String.fromCharCode(byte);
    const declarations = [...ascii.matchAll(/CA\s*\[([A-Za-z0-9_.:-]+)\]/g)].map((match) => charset(match[1]));
    let accepted = false;
    for (const encoding of new Set([...declarations, "utf-8", "iso-8859-1"])) {
      try {
        const { text, consumed } = decodeFirst(bytes, encoding);
        const [root] = parseSgf(text), declared = root.data.CA?.[0];
        if (declared ? charset(declared) !== encoding : !["utf-8", "iso-8859-1"].includes(encoding)) continue;
        roots.push(root); bytes = bytes.subarray(consumed); accepted = true; break;
      } catch { /* Try the next charset; never commit a partial collection. */ }
    }
    if (!accepted) throw new Error("SGFの文字コードまたは内容を読み取れません");
  }
  if (!roots.length) throw new Error("SGFが空です");
  return roots;
}
