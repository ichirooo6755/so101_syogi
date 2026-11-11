"""YaneuraOu USI adapter; no robot connection or motor commands."""
import os
from pathlib import Path
import queue
import subprocess
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
RESPONSE_TIMEOUT = 30


def engine_path():
    configured = os.environ.get('SHOGI_ENGINE_PATH')
    default = ROOT / 'vendor' / 'YaneuraOu' / 'engine' / (
        'yaneuraou.exe' if os.name == 'nt' else 'yaneuraou')
    return Path(configured).expanduser().resolve() if configured else default


def bestmove(sfen, legal_moves):
    """Return a legal USI move, or None on resignation/no move.

    Paths are passed directly to Popen and USI, never through a shell.
    The engine runs beside its binary so its default eval/ path is stable.
    """
    engine = engine_path()
    if not engine.is_file():
        raise ValueError('やねうら王が見つかりません。SHOGI_ENGINE_PATH と README を確認してください')
    evaluation = os.environ.get('SHOGI_EVAL_DIR')
    if evaluation:
        evaluation = str(Path(evaluation).expanduser().resolve())
        if not Path(evaluation).is_dir():
            raise ValueError('SHOGI_EVAL_DIR に評価関数のディレクトリを指定してください')
        if '\n' in evaluation or '\r' in evaluation:
            raise ValueError('評価関数のパスに改行は使えません')
    proc = subprocess.Popen(
        [str(engine)], cwd=str(engine.parent), stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    lines = queue.Queue()

    def read_output():
        try:
            for line in proc.stdout:
                lines.put(line.strip())
        finally:
            lines.put(None)

    reader = threading.Thread(target=read_output, daemon=True)

    def send(line):
        proc.stdin.write(line + '\n')
        proc.stdin.flush()

    def wait_for(prefix):
        deadline = time.monotonic() + RESPONSE_TIMEOUT
        while True:
            try:
                line = lines.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise ValueError('やねうら王の応答がありません。評価関数と設定を確認してください') from exc
            if line is None:
                raise ValueError('やねうら王が応答前に終了しました。評価関数と設定を確認してください')
            if line.startswith(prefix):
                return line

    try:
        reader.start()
        send('usi')
        wait_for('usiok')
        if evaluation:
            send('setoption name EvalDir value ' + evaluation)
        send('isready')
        wait_for('readyok')
        send('usinewgame')
        send('position sfen ' + sfen)
        # Robot reach must not filter the engine's legal moves.
        send('go movetime 500')
        result = wait_for('bestmove ').split()[1]
        if result in ('resign', '(none)', '0000'):
            return None
        if result not in legal_moves:
            raise ValueError('エンジンの手が合法手と一致しません')
        return result
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=3)
        reader.join(timeout=1)
        proc.stdin.close()
        proc.stdout.close()
