import type { AppSettings, InitialPosition, MoveHistoryEvaluation, SessionConfig, SessionState } from "./backend";
import { cloneDocument, editRecord, enginePosition, exportRecord, importRecord, newRecord, nodeAt, playRecord, recordSnapshot, replay, type RecordDocument, type ReviewPosition } from "./record.ts";

export interface EngineTransport { <T>(command: string, args?: Record<string, unknown>): Promise<T> }
export interface SessionStorage { getItem(key: string): string | null; setItem(key: string, value: string): void }
interface EngineJob { id: string; status: "running" | "completed" | "cancelled" | "error"; result: unknown; error?: string }
interface LocalJob {
  command: string;
  revision: number;
  origin: RecordDocument;
  response: EngineJob;
  accepted?: unknown;
  acceptedRevision?: number;
  reviewPositions?: ReviewPosition[];
}
const storageKey = "katago-local-document-v1";
const jobStorageKey = "katago-local-engine-job-v1";
const visits = { light: 100, balanced: 800, deep: 2400 };
const edits = new Set(["play_move", "pass_move", "undo_move", "redo_move", "goto_node", "select_game", "set_comment", "set_node_properties"]);

/** One authoritative document, shared by all React views. The Rust engine only receives
 * explicit engine snapshots and opaque file contents, never editing commands. */
export class ApplicationController {
  private transport: EngineTransport;
  private storage?: SessionStorage;
  private document = newRecord();
  private config: SessionConfig = { mode: "play", boardSize: 19, komi: 6.5, ruleset: "japanese", handicap: 0, evaluationEnabled: false };
  private revision = 0;
  private jobs = new Map<string, LocalJob>();
  private activeJob: string | null = null;
  private starting = false;
  private recovery: Promise<unknown> = Promise.resolve();

  constructor(transport: EngineTransport, storage?: SessionStorage) {
    this.transport = transport; this.storage = storage;
    const saved = storage?.getItem(storageKey);
    if (saved) {
      try {
        const state = JSON.parse(saved);
        const document = importRecord(state.sgf, "start", state.fileName);
        document.id = state.id; document.mode = state.mode; document.active = state.active;
        document.gameIndex = state.gameIndex;
        document.games.forEach((game, index) => {
          game.path = state.paths[index];
          const redo = state.redoPaths?.[index] ?? [];
          if (!Array.isArray(redo)) throw new Error("戻した手順が不正です");
          nodeAt(game, [...game.path, ...redo]);
          game.redoPath = redo;
        });
        recordSnapshot(document);
        this.validateConfig(state.config);
        this.document = document; this.config = state.config;
      } catch { /* An unreadable recovery snapshot must not prevent opening SGF. */ }
    }
    const savedJob = storage?.getItem(jobStorageKey);
    if (savedJob) {
      try {
        const job = JSON.parse(savedJob);
        // Reloading must not leave an unreachable engine job behind. Editing
        // stays local; only the next AI request waits for this best-effort stop.
        if (typeof job.id === "string") this.recovery = transport("cancel_computation", { id: job.id })
          .catch(() => undefined).then(() => storage?.setItem(jobStorageKey, ""));
      } catch { /* Ignore an unreadable job token. */ }
    }
  }

  private validateConfig(config: SessionConfig): void {
    if (!config || !["play", "record", "import"].includes(config.mode)) throw new Error("セッションの種類が不正です");
    if (config.evaluationEnabled) {
      if (typeof config.visitBudget !== "string" || !Object.prototype.hasOwnProperty.call(visits, config.visitBudget) || !Number.isInteger(config.maxCandidates) || config.maxCandidates! < 1 || config.maxCandidates! > 8) throw new Error("評価には探索量と1〜8個の候補数を指定してください");
    } else if (["visitBudget", "maxCandidates", "useAnalysisCache"].some((key) => key in config)) throw new Error("評価OFF時にはAIの設定を指定しないでください");
  }

  private snapshot(): SessionState {
    const job = this.activeJob ? this.jobs.get(this.activeJob) : null;
    const state = recordSnapshot(this.document, job ? { id: this.activeJob!, command: job.command } : null);
    return { ...state, config: { ...this.config, mode: state.mode, boardSize: state.boardSize, komi: state.komi, ruleset: state.ruleset as SessionConfig["ruleset"] } };
  }

  private commit(document: RecordDocument, config = this.config): SessionState {
    const snapshot = recordSnapshot(document);
    if (this.storage) {
      this.storage.setItem(storageKey, JSON.stringify({
        sgf: exportRecord(document, false), paths: document.games.map((game) => game.path), redoPaths: document.games.map((game) => game.redoPath ?? []), gameIndex: document.gameIndex,
        id: document.id, mode: document.mode, active: document.active, fileName: document.fileName, config,
      }));
    }
    this.document = document; this.config = { ...config }; this.revision++;
    return { ...snapshot, config: { ...this.config, mode: snapshot.mode, boardSize: snapshot.boardSize, komi: snapshot.komi, ruleset: snapshot.ruleset as SessionConfig["ruleset"] } };
  }

  private assertEditable(): void {
    if (this.activeJob || this.starting) throw new Error("AIの処理を中断してから棋譜を変更してください");
  }

  private rememberJob(): void {
    this.storage?.setItem(jobStorageKey, this.activeJob ? JSON.stringify({ id: this.activeJob }) : "");
  }

  private async source(args: Record<string, unknown>): Promise<string | Uint8Array> {
    if (typeof args.text === "string") return args.text;
    let data = args.data;
    if (data === undefined) data = (await this.transport<{ data: string }>("read_file", { path: args.path })).data;
    if (typeof data !== "string") throw new Error("SGFファイルの内容が不正です");
    const binary = atob(data);
    return Uint8Array.from(binary, (char) => char.charCodeAt(0));
  }

  private async prepareSession(config: SessionConfig): Promise<RecordDocument> {
    this.validateConfig(config);
    if (config.mode === "import") {
      if (!config.source?.trim()) throw new Error("棋譜ファイルを指定してください。");
      return importRecord(await this.source({ path: config.source }), config.initialPosition, config.source);
    }
    if (config.mode === "record" && config.initialPosition === "last") {
      if (!this.document.active) throw new Error("前回の棋譜がありません。開始位置を「空の盤」に変更してください。");
      return cloneDocument(this.document);
    }
    return newRecord(config.boardSize, config.komi, config.ruleset, config.handicap);
  }

  private async validateSession(config: SessionConfig): Promise<{ issues: string[] }> {
    const issues: string[] = [];
    try {
      const document = await this.prepareSession(config);
      recordSnapshot(document);
      if (config.evaluationEnabled) enginePosition(document);
    } catch (error) {
      issues.push(error instanceof Error ? error.message : String(error));
    }
    if (config?.evaluationEnabled) {
      try {
        const engine = await this.transport<{ issues: string[] }>("check_engine_settings");
        issues.push(...engine.issues);
      } catch (error) {
        issues.push(`AI評価の準備を確認できません: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
    return { issues };
  }

  private async start(args: Record<string, unknown>): Promise<EngineJob> {
    this.assertEditable();
    const command = String(args.command);
    if (!["genmove", "analyze_current_position", "analyze_game", "analyze_move_history"].includes(command)) throw new Error("未対応のAI処理です");
    if (!this.config.evaluationEnabled) throw new Error("AI評価をONにしてください");
    const options = (args.args ?? {}) as Record<string, unknown>;
    const target = cloneDocument(this.document);
    let reviewPositions: ReviewPosition[] | undefined;
    let turnsBySegment: number[][] | undefined;
    if (command === "analyze_move_history") {
      const game = target.games[target.gameIndex];
      if (options.path !== undefined) {
        if (!Array.isArray(options.path)) throw new Error("棋譜ノードの位置が不正です");
        game.path = [...options.path];
      }
      let node = nodeAt(game);
      while (node.children.length) { game.path.push(0); node = node.children[0]; }
      const replayed = replay(game);
      reviewPositions = replayed.reviewPositions;
      if (options.positionKeys !== undefined) {
        if (!Array.isArray(options.positionKeys) || !options.positionKeys.length || !options.positionKeys.every((key) => typeof key === "string" && reviewPositions!.some((point) => point.positionKey === key))) throw new Error("解析対象の局面が不正です");
        const wanted = new Set(options.positionKeys);
        reviewPositions = reviewPositions.filter((point) => wanted.has(point.positionKey));
      }
      turnsBySegment = replayed.segments.map((_, index) => reviewPositions!.filter((point) => point.segmentIndex === index).map((point) => point.turnNumber));
    }
    const position = enginePosition(target);
    if (command === "genmove" && options.color !== undefined && options.color !== (position.nextPlayer === "B" ? "black" : "white")) throw new Error("AI応手の手番が違います");
    const origin = cloneDocument(this.document), revision = this.revision;
    this.starting = true;
    try {
      await this.recovery;
      const response = await this.transport<EngineJob>("start_computation", {
        command: command === "analyze_move_history" ? "analyze_game" : command, position, visits: visits[this.config.visitBudget!], maxCandidates: this.config.maxCandidates,
        useCache: this.config.useAnalysisCache ?? true,
        ...(reviewPositions ? { includeSegments: true, turnsBySegment } : {}),
      });
      this.jobs.set(response.id, { command, revision, origin, response, reviewPositions });
      this.activeJob = response.id;
      this.rememberJob();
      for (const [id, job] of this.jobs) if (this.jobs.size > 16 && id !== this.activeJob && job.response.status !== "running") this.jobs.delete(id);
      return response;
    } finally { this.starting = false; }
  }

  private async job(command: string, id: string): Promise<unknown> {
    const job = this.jobs.get(id);
    if (!job) throw new Error("AI処理が見つかりません");
    if (command === "cancel_computation") {
      const response = await this.transport<EngineJob>(command, { id });
      job.response = response;
      if (this.activeJob === id) this.activeJob = null;
      this.rememberJob();
      if (job.acceptedRevision === this.revision) this.commit(job.origin);
      return { id, status: "cancelled", state: this.snapshot() };
    }
    if (command === "get_computation") {
      job.response = await this.transport<EngineJob>(command, { id });
      if (["error", "cancelled"].includes(job.response.status) && this.activeJob === id) { this.activeJob = null; this.rememberJob(); }
      return job.response;
    }
    if (job.acceptedRevision !== undefined) return job.accepted;
    if (job.response.status !== "completed") throw new Error("AI処理が完了していません");
    if (this.activeJob !== id || this.revision !== job.revision) throw new Error("古い局面のAI結果を破棄しました");
    this.activeJob = null;
    this.rememberJob();
    if (job.command === "genmove") {
      const candidate = cloneDocument(this.document), state = recordSnapshot(candidate), move = String(job.response.result);
      const color = state.game.nextSign === 1 ? "black" : "white";
      if (move === "resign") candidate.games[candidate.gameIndex].root.data.RE = [state.game.nextSign === 1 ? "W+R" : "B+R"];
      else playRecord(candidate, color, move);
      job.accepted = { move, state: this.commit(candidate) };
    } else if (job.command === "analyze_move_history") {
      const points = job.response.result as { segmentIndex: number; turnNumber: number; winrate: number; scoreLead: number }[];
      if (!Array.isArray(points) || points.length !== job.reviewPositions!.length) throw new Error("棋譜の解析結果が不足しています");
      const seen = new Set<string>();
      job.accepted = points.map((point): MoveHistoryEvaluation => {
        const target = job.reviewPositions!.find((item) => item.segmentIndex === point.segmentIndex && item.turnNumber === point.turnNumber);
        if (!target || seen.has(target.positionKey) || !Number.isFinite(point.winrate) || point.winrate < 0 || point.winrate > 1 || !Number.isFinite(point.scoreLead)) throw new Error("棋譜の解析結果が不正です");
        seen.add(target.positionKey);
        return { positionKey: target.positionKey, winrate: point.winrate, scoreLead: point.scoreLead };
      });
    } else job.accepted = job.response.result;
    job.acceptedRevision = this.revision;
    return job.accepted;
  }

  async invoke<T>(command: string, args: Record<string, unknown> = {}): Promise<T> {
    return await this.dispatch(command, args) as T;
  }

  private async dispatch(command: string, args: Record<string, unknown>): Promise<unknown> {
    if (command === "get_state") return this.snapshot();
    if (["get_settings", "save_settings"].includes(command)) return this.transport<AppSettings>(command, args);
    if (command === "validate_session") return this.validateSession(args.config as SessionConfig);
    if (command === "start_computation") return this.start(args);
    if (["get_computation", "cancel_computation", "accept_computation"].includes(command)) return this.job(command, String(args.id));
    this.assertEditable();
    if (command === "configure_analysis") {
      const config = args.config as SessionConfig;
      this.validateConfig(config);
      return this.commit(this.document, config);
    }
    if (command === "new_session") {
      const config = args.config as SessionConfig;
      this.validateConfig(config);
      const revision = this.revision;
      const candidate = await this.prepareSession(config);
      if (revision !== this.revision) throw new Error("読み込み中に棋譜が変更されました");
      candidate.id = crypto.randomUUID(); candidate.mode = config.mode; candidate.active = true;
      return this.commit(candidate, config);
    }
    if (command === "load_sgf") {
      const revision = this.revision;
      const source = await this.source(args);
      const candidate = importRecord(source, args.initialPosition as InitialPosition | undefined, typeof args.path === "string" ? args.path : null);
      if (revision !== this.revision) throw new Error("読み込み中に棋譜が変更されました");
      return this.commit(candidate);
    }
    if (command === "save_sgf") {
      const text = exportRecord(this.document), revision = this.revision;
      let path = this.document.fileName;
      if (args.path) {
        const result = await this.transport<{ path: string }>("write_file", { path: args.path, text });
        path = result.path;
        if (revision === this.revision) this.commit({ ...this.document, fileName: path });
      }
      return { ok: true, text, path };
    }
    if (edits.has(command)) {
      const candidate = cloneDocument(this.document);
      editRecord(candidate, command, args);
      return this.commit(candidate);
    }
    throw new Error(`未知のアプリ操作: ${command}`);
  }
}
