declare module "@sabaki/sgf" {
  export interface SgfNode {
    id: number | string;
    parentId: number | string | null;
    data: Record<string, string[]>;
    children: SgfNode[];
  }
  export interface Token { type: string; value: string; pos: number; row: number; col: number }
  export function parse(contents: string): SgfNode[];
  export function stringify(nodes: SgfNode[], options?: { linebreak?: string; indent?: string }): string;
  export function tokenizeIter(contents: string): IterableIterator<Token>;
  const sgf: { parse: typeof parse; stringify: typeof stringify; tokenizeIter: typeof tokenizeIter };
  export default sgf;
}
