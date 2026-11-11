// @sabaki/sgf also exports Node-only parseFile/parseBuffer. The desktop uses
// parse(string) and its TextDecoder adapter, without Node or codec polyfills.
export const encodingExists = () => false;
export const detect = () => ({ encoding: "UTF-8", confidence: 1 });
export function readFileSync(): never { throw new Error("ファイルの読込はアプリのファイルAPIを使用してください"); }
export function decode(): never { throw new Error("文字コードの変換はSGFのTextDecoderアダプターを使用してください"); }
export const encode = decode;
