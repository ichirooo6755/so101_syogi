use crate::domain::*;
use anyhow::{bail, ensure, Context, Result};
use std::{
    collections::VecDeque,
    io::{BufRead, BufReader, Write},
    path::PathBuf,
    process::{Child, ChildStdin, Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        mpsc::{self, Receiver},
        Arc, Mutex,
    },
    thread,
    time::Duration,
};

/// Child ownership is independent of stdout: cancellation can always kill a
/// process whose worker is blocked waiting for a protocol response.
#[derive(Default)]
pub struct Cancellation {
    pub cancelled: AtomicBool,
    child: Mutex<Option<Child>>,
}
impl Cancellation {
    pub fn check(&self) -> Result<()> {
        ensure!(
            !self.cancelled.load(Ordering::SeqCst),
            "computation cancelled"
        );
        Ok(())
    }
    pub fn abort(&self) {
        self.cancelled.store(true, Ordering::SeqCst);
        self.kill();
    }
    pub fn kill(&self) {
        if let Ok(mut child) = self.child.lock() {
            if let Some(child) = child.as_mut() {
                let _ = child.kill();
            }
        }
    }
}
pub struct EngineProcess {
    input: Option<ChildStdin>,
    lines: Receiver<std::io::Result<String>>,
    reader: Option<thread::JoinHandle<()>>,
    stderr_reader: Mutex<Option<thread::JoinHandle<()>>>,
    diagnostics: Arc<Mutex<VecDeque<String>>>,
    log_path: PathBuf,
    timeout: Duration,
    pub cancellation: Arc<Cancellation>,
}
impl EngineProcess {
    pub fn start(
        settings: &AppSettings,
        analysis: bool,
        cancellation: Arc<Cancellation>,
    ) -> Result<Self> {
        Self::start_configured(
            settings,
            analysis,
            cancellation,
            "",
            Duration::from_secs(if settings.use_gpu { 300 } else { 120 }),
        )
    }
    pub fn probe(settings: &AppSettings, cancellation: Arc<Cancellation>) -> Result<Self> {
        Self::start_configured(
            settings,
            false,
            cancellation,
            ",nnCacheSizePowerOfTwo=12,nnMutexPoolSizePowerOfTwo=10",
            Duration::from_secs(900),
        )
    }
    fn start_configured(
        settings: &AppSettings,
        analysis: bool,
        cancellation: Arc<Cancellation>,
        extra: &str,
        timeout: Duration,
    ) -> Result<Self> {
        cancellation.check()?;
        let logs = std::env::temp_dir().join("katago-local-logs");
        std::fs::create_dir_all(&logs)?;
        let home_data = logs.join("engine-cache");
        std::fs::create_dir_all(&home_data)?;
        let overrides = if analysis {
            format!(
                "numSearchThreadsPerAnalysisThread={},reportAnalysisWinratesAs=BLACK,logDir={}",
                settings.threads,
                logs.to_string_lossy().replace('\\', "/")
            )
        } else {
            format!(
                "maxVisits={},numSearchThreads={},logDir={}",
                settings.visits,
                settings.threads,
                logs.to_string_lossy().replace('\\', "/")
            )
        };
        let overrides = format!(
            "{overrides},homeDataDir={}{}{extra}",
            home_data.to_string_lossy().replace('\\', "/"),
            crate::compute::device_overrides(settings)?
        );
        let engine_path = crate::compute::executable(settings)?;
        let log_path = logs.join(format!("{}.log", uuid::Uuid::new_v4()));
        let mut log = std::fs::File::create(&log_path)?;
        let mut command = Command::new(engine_path);
        command
            .args([
                if analysis { "analysis" } else { "gtp" },
                "-model",
                &settings.model_path,
                "-config",
                if analysis {
                    &settings.analysis_config_path
                } else {
                    &settings.gtp_config_path
                },
                "-override-config",
                &overrides,
            ])
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x08000000);
        }
        let mut child = command
            .spawn()
            .with_context(|| format!("KataGoを起動できません: {engine_path}"))?;
        let input = child.stdin.take().context("KataGo stdin unavailable")?;
        let output = child.stdout.take().context("KataGo stdout unavailable")?;
        let stderr = child.stderr.take().context("KataGo stderr unavailable")?;
        let diagnostics = Arc::new(Mutex::new(VecDeque::new()));
        let stderr_tail = diagnostics.clone();
        {
            let mut guard = cancellation.child.lock().unwrap_or_else(|p| p.into_inner());
            ensure!(guard.is_none(), "task already owns an engine");
            *guard = Some(child);
        }
        let (sender, lines) = mpsc::channel();
        let reader = thread::spawn(move || {
            for line in BufReader::new(output).lines() {
                let failed = line.is_err();
                if sender.send(line).is_err() || failed {
                    break;
                }
            }
        });
        let stderr_reader = thread::spawn(move || {
            for line in BufReader::new(stderr)
                .lines()
                .map_while(std::result::Result::ok)
            {
                let _ = writeln!(log, "{line}");
                let mut tail = stderr_tail.lock().unwrap_or_else(|p| p.into_inner());
                tail.push_back(line.chars().take(1200).collect());
                while tail.len() > 12 {
                    tail.pop_front();
                }
            }
        });
        let process = Self {
            input: Some(input),
            lines,
            reader: Some(reader),
            stderr_reader: Mutex::new(Some(stderr_reader)),
            diagnostics,
            log_path,
            timeout,
            cancellation,
        };
        process.cancellation.check()?;
        Ok(process)
    }
    pub fn send(&mut self, text: &str) -> Result<()> {
        self.cancellation.check()?;
        let input = self.input.as_mut().context("engine stdin closed")?;
        if let Err(error) = writeln!(input, "{text}").and_then(|_| input.flush()) {
            bail!("{}: {error}", self.failure("KataGoへの送信に失敗しました"));
        }
        Ok(())
    }
    pub fn read_line(&self) -> Result<String> {
        self.cancellation.check()?;
        match self.lines.recv_timeout(self.timeout) {
            Ok(line) => Ok(line?),
            Err(mpsc::RecvTimeoutError::Disconnected) => {
                bail!("{}", self.failure("KataGoが応答せずに終了しました"))
            }
            Err(mpsc::RecvTimeoutError::Timeout) => {
                bail!(
                    "{}",
                    self.failure("KataGoの起動・応答が制限時間を超えました")
                );
            }
        }
    }
    fn failure(&self, message: &str) -> String {
        let code = self
            .cancellation
            .child
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .as_mut()
            .and_then(|child| {
                let status = child.try_wait().ok().flatten();
                status.or_else(|| {
                    let _ = child.kill();
                    child.wait().ok()
                })
            })
            .and_then(|status| status.code());
        if let Some(reader) = self
            .stderr_reader
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .take()
        {
            let _ = reader.join();
        }
        let tail = self
            .diagnostics
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .iter()
            .cloned()
            .collect::<Vec<_>>()
            .join("\n");
        let hint = if code.is_some_and(|code| code as u32 == 0xc0000135) {
            "\n必要なDLLが見つかりません。CUDA／cuDNNランタイムなどを確認してください。"
        } else {
            ""
        };
        let code_label = code
            .map(|code| format!("0x{:08X}", code as u32))
            .unwrap_or_else(|| "不明".into());
        format!(
            "{message}（終了コード: {code_label}）。{hint}\n{tail}\n診断ログ: {}",
            self.log_path.display()
        )
    }
    pub fn command(&mut self, text: &str) -> Result<String> {
        self.send(text)?;
        let mut lines = Vec::new();
        loop {
            let line = self.read_line()?;
            if line.is_empty() {
                break;
            }
            lines.push(line);
        }
        let first = lines.first().context("empty GTP response")?;
        ensure!(
            first.starts_with('=') || first.starts_with('?'),
            "unexpected GTP response: {first}"
        );
        let mut payload = first[1..].trim_start().to_owned();
        for line in &lines[1..] {
            payload.push('\n');
            payload.push_str(line);
        }
        ensure!(first.starts_with('='), "{}", payload.trim());
        Ok(payload.trim().into())
    }
    pub fn initialize(&mut self, position: &Position) -> Result<()> {
        position.validate()?;
        let width = position.board_x_size;
        let height = position.board_y_size;
        self.command(&if width == height {
            format!("boardsize {width}")
        } else {
            format!("boardsize {width} {height}")
        })?;
        self.command(&format!("kata-set-rules {}", position.rules))?;
        self.command(&format!("komi {}", position.komi))?;
        self.command("clear_board")?;
        let segment = position.segments.last().unwrap();
        if !segment.initial_stones.is_empty() {
            let handicap = segment.move_offset == 0
                && position.handicap >= 2
                && segment.initial_stones.len() == position.handicap
                && segment.initial_stones.iter().all(|(c, _)| *c == Color::B);
            let stones = segment
                .initial_stones
                .iter()
                .map(|(color, vertex)| {
                    if handicap {
                        vertex.clone()
                    } else {
                        format!("{} {vertex}", color.name())
                    }
                })
                .collect::<Vec<_>>()
                .join(" ");
            self.command(&format!(
                "{} {stones}",
                if handicap {
                    "set_free_handicap"
                } else {
                    "set_position"
                }
            ))?;
        }
        for (color, vertex) in &segment.moves {
            self.command(&format!("play {} {vertex}", color.name()))?;
        }
        Ok(())
    }
    pub fn analyze(&mut self, position: &Position, visits: u64) -> Result<AnalysisResult> {
        let previous = self.command("kata-get-param maxVisits")?;
        self.command(&format!("kata-set-param maxVisits {visits}"))?;
        let result = self.command(&format!(
            "kata-search_analyze {} 100",
            position.next_player.name()
        ));
        let restore = self.command(&format!("kata-set-param maxVisits {previous}"));
        let raw = result?;
        restore?;
        let candidates = parse_analysis_output(&raw, position.board_x_size, position.board_y_size)?;
        let best = candidates.first();
        Ok(AnalysisResult {
            query_id: uuid::Uuid::new_v4().to_string(),
            winrate: best.map_or(0.5, |c| c.winrate),
            score_lead: best.map_or(0.0, |c| c.score_lead),
            visits: candidates.iter().map(|c| c.visits).sum(),
            candidate_moves: candidates,
        })
    }
}
impl Drop for EngineProcess {
    fn drop(&mut self) {
        self.input.take();
        self.cancellation.kill();
        if let Ok(mut guard) = self.cancellation.child.lock() {
            if let Some(mut child) = guard.take() {
                let _ = child.wait();
            }
        }
        if let Some(reader) = self.reader.take() {
            let _ = reader.join();
        }
        if let Some(reader) = self
            .stderr_reader
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .take()
        {
            let _ = reader.join();
        }
    }
}
pub fn parse_analysis_info_line(
    line: &str,
    width: usize,
    height: usize,
) -> Result<Option<CandidateMove>> {
    let parts: Vec<_> = line.split_whitespace().collect();
    if parts.first() != Some(&"info") {
        return Ok(None);
    }
    let mut vertex = None;
    let mut visits = 0;
    let mut winrate = 0.;
    let mut score_lead: f64 = 0.;
    let mut pv = Vec::new();
    let mut i = 1;
    while i < parts.len() {
        let key = parts[i];
        if matches!(key, "info" | "rootInfo" | "ownership" | "ownershipStdev") {
            break;
        }
        if matches!(key, "move" | "visits" | "winrate" | "scoreLead") {
            ensure!(i + 1 < parts.len(), "missing analysis value for {key}");
            i += 1;
            match key {
                "move" => vertex = Some(from_gtp(parts[i], width, height)?),
                "visits" => visits = parts[i].parse()?,
                "winrate" => {
                    winrate = parts[i].parse::<f64>()?;
                    if winrate > 1. {
                        winrate /= 10000.;
                    }
                }
                "scoreLead" => score_lead = parts[i].parse()?,
                _ => {}
            }
        } else if key == "pv" {
            i += 1;
            while i < parts.len() {
                match from_gtp(parts[i], width, height) {
                    Ok(p) => pv.push(p),
                    Err(_) => break,
                }
                i += 1;
            }
            continue;
        }
        i += 1;
    }
    ensure!(
        winrate.is_finite() && score_lead.is_finite(),
        "non-finite analysis result"
    );
    Ok(vertex.map(|vertex| CandidateMove {
        vertex,
        winrate,
        score_lead,
        visits,
        pv,
    }))
}
pub fn parse_analysis_output(
    text: &str,
    width: usize,
    height: usize,
) -> Result<Vec<CandidateMove>> {
    let Some(line) = text
        .lines()
        .rev()
        .find(|l| l.trim_start().starts_with("info "))
    else {
        return Ok(vec![]);
    };
    let tokens: Vec<_> = line.split_whitespace().collect();
    let mut result = Vec::new();
    let mut index = 0;
    while index < tokens.len() {
        if tokens[index] != "info" {
            index += 1;
            continue;
        }
        let end = (index + 1..tokens.len())
            .find(|&i| tokens[i] == "info")
            .unwrap_or(tokens.len());
        if let Some(item) = parse_analysis_info_line(&tokens[index..end].join(" "), width, height)?
        {
            result.push(item);
        }
        index = end;
    }
    Ok(result)
}
