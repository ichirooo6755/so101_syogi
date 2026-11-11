export interface BackendTransport {
  <T>(command: string, args?: Record<string, unknown>): Promise<T>;
}

interface JobResult<T> {
  id: string;
  status: "running" | "completed" | "cancelled" | "error";
  result: T;
  error?: string;
}

export class ComputationCancelled extends Error {
  constructor() { super("処理を中断しました"); }
}

const delay = (milliseconds: number) => new Promise<void>((resolve) => setTimeout(resolve, milliseconds));

/** Keep cancellation addressable even before the start request has returned. */
export class BackendComputation<T> {
  cancelled = false;
  private started: Promise<JobResult<T>>;
  private invoke: BackendTransport;
  private interval: number;

  constructor(invoke: BackendTransport, command: string, args: Record<string, unknown> = {}, interval = 250) {
    this.invoke = invoke; this.interval = interval;
    this.started = invoke<JobResult<T>>("start_computation", { command, args });
  }

  async result(paused: () => boolean = () => false): Promise<T> {
    let job = await this.started;
    while (!this.cancelled) {
      if (job.status === "completed") {
        // A leave confirmation may be open. Keep the result pending until the
        // user stays, or cancel it (including a reply racing cancellation).
        while (paused() && !this.cancelled) await delay(this.interval);
        if (this.cancelled) break;
        return this.invoke<T>("accept_computation", { id: job.id });
      }
      if (job.status === "cancelled") throw new ComputationCancelled();
      if (job.status === "error") throw new Error(job.error || "AIの処理に失敗しました");
      await delay(this.interval);
      if (this.cancelled) break;
      job = await this.invoke<JobResult<T>>("get_computation", { id: job.id });
    }
    throw new ComputationCancelled();
  }

  async cancel<TState>(): Promise<{ status: string; state: TState }> {
    this.cancelled = true;
    const job = await this.started;
    return this.invoke("cancel_computation", { id: job.id });
  }
}
