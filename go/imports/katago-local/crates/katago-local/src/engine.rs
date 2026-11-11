use crate::{
    domain::*,
    protocol::{Cancellation, EngineProcess},
    storage::{atomic_write, snake, Repository},
};
use anyhow::{bail, ensure, Context, Result};
use base64::{engine::general_purpose::STANDARD, Engine};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::Path,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    thread,
    time::UNIX_EPOCH,
};

pub struct Job {
    pub id: String,
    pub cancellation: Arc<Cancellation>,
    response: Mutex<Value>,
    worker: Mutex<Option<thread::JoinHandle<()>>>,
    retained_engine: Mutex<Option<EngineProcess>>,
}
impl Job {
    pub fn response(&self) -> Value {
        self.response
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .clone()
    }
    pub fn cancel(&self) -> Value {
        self.cancellation.abort();
        let mut response = self.response.lock().unwrap_or_else(|p| p.into_inner());
        response["status"] = json!("cancelled");
        response["result"] = Value::Null;
        self.take_engine();
        response.clone()
    }
    pub(crate) fn take_engine(&self) -> Option<EngineProcess> {
        self.retained_engine
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .take()
    }
}
pub struct EngineBackend {
    pub repository: Repository,
    settings: Mutex<AppSettings>,
    jobs: Mutex<Vec<Arc<Job>>>,
    closed: AtomicBool,
    gpu_validated: AtomicBool,
    configuration_cancel: Arc<Cancellation>,
}
impl EngineBackend {
    pub fn new(database: impl AsRef<Path>, root: impl AsRef<Path>) -> Result<Arc<Self>> {
        let root = dunce::canonicalize(root.as_ref()).unwrap_or_else(|_| root.as_ref().to_owned());
        let repository = Repository::new(database)?;
        let settings = repository.load(AppSettings::at(&root))?;
        Ok(Arc::new(Self {
            repository,
            settings: Mutex::new(settings),
            jobs: Mutex::new(vec![]),
            closed: AtomicBool::new(false),
            gpu_validated: AtomicBool::new(false),
            configuration_cancel: Arc::default(),
        }))
    }
    pub fn settings(&self) -> AppSettings {
        self.settings
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .clone()
    }
    pub fn dispatch(self: &Arc<Self>, command: &str, args: &Value) -> Result<Value> {
        ensure!(args.is_object(), "RPC args must be an object");
        ensure!(!self.closed.load(Ordering::SeqCst), "backend is closed");
        match command {
            "get_settings" => Ok(serde_json::to_value(self.settings())?),
            "save_settings" => {
                let jobs = self.jobs.lock().unwrap_or_else(|p| p.into_inner());
                ensure!(
                    !jobs.iter().any(|job| job.response()["status"] == "running"),
                    "AIの処理を中断してから設定を変更してください。"
                );
                let values = args.get("settings").cloned().unwrap_or_else(|| json!({}));
                let supplied = values.as_object().context("unknown settings fields")?;
                let mut guard = self.settings.lock().unwrap_or_else(|p| p.into_inner());
                let mut merged = serde_json::to_value(&*guard)?;
                for (key, value) in supplied {
                    ensure!(
                        !matches!(key.as_str(), "gpuBackend" | "gpuDeviceIndex" | "gpuName"),
                        "GPUの検出結果は手動で変更できません。"
                    );
                    ensure!(merged.get(key).is_some(), "unknown settings fields");
                    merged[key] = value.clone();
                }
                let mut next: AppSettings = serde_json::from_value(merged)?;
                next.validate()?;
                if !next.use_gpu {
                    crate::compute::reset_to_cpu(&mut next);
                } else if !self.gpu_validated.load(Ordering::SeqCst)
                    || !guard.use_gpu
                    || next.model_path != guard.model_path
                    || next.opencl_path != guard.opencl_path
                    || next.cuda_path != guard.cuda_path
                {
                    crate::compute::configure(&mut next, self.configuration_cancel.clone())?;
                }
                ensure!(!self.closed.load(Ordering::SeqCst), "backend is closed");
                self.repository.save(&next)?;
                self.gpu_validated.store(next.use_gpu, Ordering::SeqCst);
                *guard = next;
                Ok(serde_json::to_value(&*guard)?)
            }
            "check_engine_settings" => {
                let settings = self.settings();
                let mut issues = Vec::new();
                let engine_path = crate::compute::executable(&settings);
                if let Err(error) = &engine_path {
                    issues.push(error.to_string());
                }
                for (value, label) in [
                    (engine_path.unwrap_or(""), "KataGo実行ファイル"),
                    (settings.model_path.as_str(), "モデル"),
                    (settings.gtp_config_path.as_str(), "GTP設定"),
                    (settings.analysis_config_path.as_str(), "解析設定"),
                ] {
                    if value.trim().is_empty() {
                        issues.push(format!("{label}が指定されていません。"));
                    } else if !Path::new(value).is_file() {
                        issues.push(format!("{label}が見つかりません: {value}"));
                    } else if std::fs::File::open(value).is_err() {
                        issues.push(format!("{label}を読み込めません: {value}"));
                    }
                }
                Ok(json!({"issues":issues}))
            }
            "read_file" => Ok(
                json!({"data":STANDARD.encode(std::fs::read(args["path"].as_str().context("path must be text")?)?)}),
            ),
            "write_file" => {
                let path = Path::new(args["path"].as_str().context("path must be text")?);
                let text = args["text"].as_str().context("text must be text")?;
                let target = atomic_write(path, text.as_bytes())?;
                Ok(json!({"ok":true,"path":target.to_string_lossy()}))
            }
            "start_computation" => self.start(args, false),
            "get_computation" | "cancel_computation" => {
                let id = args["id"].as_str().context("missing computation id")?;
                let job = self.job(id)?;
                Ok(if command == "cancel_computation" {
                    job.cancel()
                } else {
                    job.response()
                })
            }
            _ => bail!("unknown engine command: {command}"),
        }
    }
    pub fn job(&self, id: &str) -> Result<Arc<Job>> {
        self.jobs
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .iter()
            .find(|j| j.id == id)
            .cloned()
            .context("unknown computation")
    }
    pub(crate) fn start_legacy(self: &Arc<Self>, args: &Value) -> Result<Value> {
        self.start(args, true)
    }
    fn start(self: &Arc<Self>, args: &Value, retain_engine: bool) -> Result<Value> {
        let command = args["command"]
            .as_str()
            .context("missing computation command")?;
        ensure!(
            matches!(
                command,
                "genmove" | "analyze_current_position" | "analyze_game"
            ),
            "unsupported computation"
        );
        let position: Position = serde_json::from_value(args["position"].clone())?;
        position.validate()?;
        let visits = args
            .get("visits")
            .map(Value::as_u64)
            .unwrap_or(Some(800))
            .context("invalid analysis budget")?;
        let count = args
            .get("maxCandidates")
            .map(Value::as_u64)
            .unwrap_or(Some(3))
            .context("invalid analysis budget")?;
        ensure!(
            visits > 0 && (1..=8).contains(&count),
            "invalid analysis budget"
        );
        let mut jobs = self.jobs.lock().unwrap_or_else(|p| p.into_inner());
        ensure!(!self.closed.load(Ordering::SeqCst), "backend is closed");
        ensure!(
            !jobs.iter().any(|j| j.response()["status"] == "running"),
            "a computation is already running"
        );
        let id = uuid::Uuid::new_v4().to_string();
        let job = Arc::new(Job {
            id: id.clone(),
            cancellation: Arc::default(),
            response: Mutex::new(json!({"id":id,"status":"running","result":null,"error":null})),
            worker: Mutex::new(None),
            retained_engine: Mutex::new(None),
        });
        jobs.push(job.clone());
        while jobs.len() > 16 {
            if let Some(index) = jobs.iter().position(|j| {
                j.response()["status"] != "running"
                    && j.worker
                        .lock()
                        .unwrap_or_else(|p| p.into_inner())
                        .as_ref()
                        .is_none_or(thread::JoinHandle::is_finished)
            }) {
                jobs.remove(index);
            } else {
                break;
            }
        }
        let initial = job.response();
        let backend = self.clone();
        let worker_job = job.clone();
        let command = command.to_owned();
        let args = args.clone();
        let mut settings = self.settings();
        settings.visits = visits;
        let handle = thread::Builder::new()
            .name(format!("engine-{command}"))
            .spawn(move || {
                let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    backend.calculate(
                        &command,
                        &args,
                        &settings,
                        &position,
                        worker_job.cancellation.clone(),
                        retain_engine,
                    )
                }))
                .unwrap_or_else(|_| Err(anyhow::anyhow!("engine worker panicked")));
                let mut response = worker_job
                    .response
                    .lock()
                    .unwrap_or_else(|p| p.into_inner());
                if response["status"] == "running"
                    && !worker_job.cancellation.cancelled.load(Ordering::SeqCst)
                {
                    match result {
                        Ok((value, process)) => {
                            *worker_job
                                .retained_engine
                                .lock()
                                .unwrap_or_else(|p| p.into_inner()) = process;
                            response["status"] = json!("completed");
                            response["result"] = value;
                        }
                        Err(error) => {
                            response["status"] = json!("error");
                            response["error"] = json!(format!("{error:#}"));
                        }
                    }
                }
            })?;
        *job.worker.lock().unwrap_or_else(|p| p.into_inner()) = Some(handle);
        Ok(initial)
    }
    fn calculate(
        &self,
        command: &str,
        args: &Value,
        settings: &AppSettings,
        position: &Position,
        cancellation: Arc<Cancellation>,
        retain_engine: bool,
    ) -> Result<(Value, Option<EngineProcess>)> {
        cancellation.check()?;
        // Saved GPU preferences are checked lazily on the first AI request,
        // never during application startup. The job remains cancellable.
        let mut resolved = settings.clone();
        if resolved.use_gpu && !self.gpu_validated.load(Ordering::SeqCst) {
            crate::compute::configure(&mut resolved, cancellation.clone())?;
            let mut guard = self.settings.lock().unwrap_or_else(|p| p.into_inner());
            guard.gpu_backend = resolved.gpu_backend.clone();
            guard.gpu_device_index = resolved.gpu_device_index;
            guard.gpu_name = resolved.gpu_name.clone();
            self.gpu_validated.store(true, Ordering::SeqCst);
        }
        let settings = &resolved;
        if command == "analyze_game" {
            let mut process = EngineProcess::start(settings, true, cancellation)?;
            let detailed = args["includeSegments"] == true;
            let turns = args
                .get("turnsBySegment")
                .map(|value| serde_json::from_value::<Vec<Vec<usize>>>(value.clone()))
                .transpose()?;
            let value =
                review_positions(&mut process, settings, position, detailed, turns.as_deref())?;
            return Ok((value, retain_engine.then_some(process)));
        }
        if command == "genmove" {
            let mut process = EngineProcess::start(settings, false, cancellation.clone())?;
            process.initialize(position)?;
            let value = process.command(&format!("genmove {}", position.next_player.name()))?;
            cancellation.check()?;
            let value = json!(if value.eq_ignore_ascii_case("resign") {
                String::from("resign")
            } else {
                to_gtp(
                    from_gtp(&value, position.board_x_size, position.board_y_size)?,
                    position.board_x_size,
                    position.board_y_size,
                )?
            });
            return Ok((value, retain_engine.then_some(process)));
        }
        let key = cache_key(settings, position)?;
        let use_cache = args
            .get("useCache")
            .and_then(Value::as_bool)
            .unwrap_or(true)
            && settings.cache_policy == "reuse";
        let mut result = if use_cache {
            self.repository.get(&key)?
        } else {
            None
        };
        let mut retained = None;
        if result.is_none() || retain_engine {
            let mut process = EngineProcess::start(settings, false, cancellation.clone())?;
            process.initialize(position)?;
            if result.is_none() {
                let analysis = process.analyze(position, settings.visits)?;
                cancellation.check()?;
                if use_cache {
                    self.repository.put(&key, &analysis)?;
                }
                result = Some(analysis);
            }
            retained = retain_engine.then_some(process);
        }
        cancellation.check()?;
        let value = format_analysis(
            result.as_ref().unwrap(),
            position,
            args.get("maxCandidates")
                .and_then(Value::as_u64)
                .unwrap_or(3) as usize,
        )?;
        Ok((value, retained))
    }
    pub fn close(&self) {
        self.closed.store(true, Ordering::SeqCst);
        self.configuration_cancel.abort();
        let jobs = self.jobs.lock().unwrap_or_else(|p| p.into_inner()).clone();
        for job in &jobs {
            if job.response()["status"] == "running" {
                job.cancel();
            } else {
                job.cancellation.kill();
                job.take_engine();
            }
        }
        for job in &jobs {
            if let Some(handle) = job.worker.lock().unwrap_or_else(|p| p.into_inner()).take() {
                let _ = handle.join();
            }
        }
    }
}
pub fn format_analysis(
    result: &AnalysisResult,
    position: &Position,
    count: usize,
) -> Result<Value> {
    let mut candidates = Vec::new();
    for item in result.candidate_moves.iter().take(count) {
        candidates.push(json!({"vertex":item.vertex.map(|p|[p.x,p.y]),"label":to_gtp(item.vertex,position.board_x_size,position.board_y_size)?,"winrate":item.winrate,"scoreLead":item.score_lead,"visits":item.visits,"pv":item.pv.iter().map(|&p|to_gtp(p,position.board_x_size,position.board_y_size)).collect::<Result<Vec<_>>>()?}));
    }
    Ok(
        json!({"winrate":result.winrate,"scoreLead":result.score_lead,"visits":result.visits,"candidates":candidates}),
    )
}
pub fn cache_key(settings: &AppSettings, position: &Position) -> Result<String> {
    let mut settings = serde_json::to_value(settings)?
        .as_object()
        .unwrap()
        .iter()
        .map(|(key, value)| (snake(key), value.clone()))
        .collect::<serde_json::Map<_, _>>();
    // Preserve the existing CPU cache format; GPU results include the actual
    // backend and device so switching hardware cannot reuse a mismatched entry.
    if settings["gpu_backend"] == "" {
        for field in [
            "opencl_path",
            "cuda_path",
            "gpu_backend",
            "gpu_device_index",
            "gpu_name",
        ] {
            settings.remove(field);
        }
    }
    let signature = |path: &Value| -> Option<Value> {
        let metadata = std::fs::metadata(path.as_str()?).ok()?;
        if !metadata.is_file() {
            return None;
        }
        Some(json!([
            metadata
                .modified()
                .ok()?
                .duration_since(UNIX_EPOCH)
                .ok()?
                .as_nanos() as u64,
            metadata.len()
        ]))
    };
    let identity = json!([
        position,
        settings,
        signature(&settings["model_path"]),
        signature(&settings["gtp_config_path"])
    ]);
    // Match Python json.dumps(sort_keys=True, separators=(",",":")) including
    // its default ASCII escaping, so existing analysis cache entries are reused.
    let ascii = ascii_json(&identity);
    Ok(format!(
        "ts-position:{:x}",
        Sha256::digest(ascii.as_bytes())
    ))
}
pub(crate) fn ascii_json(value: &Value) -> String {
    let mut ascii = String::new();
    for ch in value.to_string().chars() {
        if ch.is_ascii() {
            ascii.push(ch);
        } else {
            let mut units = [0u16; 2];
            for unit in ch.encode_utf16(&mut units) {
                ascii.push_str(&format!("\\u{unit:04x}"));
            }
        }
    }
    ascii
}
pub fn review(
    settings: &AppSettings,
    position: &Position,
    cancellation: Arc<Cancellation>,
) -> Result<Value> {
    let mut process = EngineProcess::start(settings, true, cancellation.clone())?;
    review_process(&mut process, settings, position)
}
pub fn review_process(
    process: &mut EngineProcess,
    settings: &AppSettings,
    position: &Position,
) -> Result<Value> {
    review_positions(process, settings, position, false, None)
}

fn review_positions(
    process: &mut EngineProcess,
    settings: &AppSettings,
    position: &Position,
    detailed: bool,
    requested: Option<&[Vec<usize>]>,
) -> Result<Value> {
    if let Some(turns) = requested {
        ensure!(
            detailed && turns.len() == position.segments.len(),
            "invalid analysis turns"
        );
    }
    let mut queries = BTreeMap::new();
    let mut expected = 0;
    for (index, segment) in position.segments.iter().enumerate() {
        let turns: BTreeSet<usize> = requested
            .map(|turns| turns[index].iter().copied().collect())
            .unwrap_or_else(|| (0..=segment.moves.len()).collect());
        ensure!(
            turns.iter().all(|&turn| turn <= segment.moves.len()),
            "invalid analysis turn"
        );
        if turns.is_empty() {
            continue;
        }
        let id = uuid::Uuid::new_v4().to_string();
        process.send(&json!({"id":id,"boardXSize":position.board_x_size,"boardYSize":position.board_y_size,"komi":position.komi,"rules":position.rules,"maxVisits":settings.visits,"initialStones":segment.initial_stones,"initialPlayer":segment.initial_player,"moves":segment.moves,"analyzeTurns":turns}).to_string())?;
        expected += turns.len();
        queries.insert(id, (index, segment, turns));
    }
    let mut seen = BTreeSet::new();
    let mut points: BTreeMap<usize, (usize, Value)> = BTreeMap::new();
    let mut detailed_points: BTreeMap<(usize, usize), Value> = BTreeMap::new();
    while seen.len() < expected {
        let result: Value = serde_json::from_str(&process.read_line()?)?;
        let Some(id) = result["id"].as_str() else {
            continue;
        };
        let Some((index, segment, turns)) = queries.get(id) else {
            continue;
        };
        if let Some(error) = result.get("error") {
            bail!("{error}");
        }
        if result["isDuringSearch"] == true || result.get("rootInfo").is_none() {
            continue;
        }
        let turn = result["turnNumber"]
            .as_u64()
            .context("invalid analysis turn")? as usize;
        ensure!(turns.contains(&turn), "unexpected analysis turn");
        let winrate = result["rootInfo"]["winrate"]
            .as_f64()
            .context("invalid analysis winrate")?;
        let score = result["rootInfo"]["scoreLead"]
            .as_f64()
            .context("invalid analysis score")?;
        ensure!(
            winrate.is_finite() && (0.0..=1.0).contains(&winrate) && score.is_finite(),
            "non-finite analysis result"
        );
        seen.insert((id.to_owned(), turn));
        let number = segment.move_offset + turn;
        if detailed {
            detailed_points.insert((*index, turn), json!({"segmentIndex":index,"turnNumber":turn,"moveNumber":number,"winrate":winrate,"scoreLead":score}));
        }
        if points
            .get(&number)
            .is_none_or(|(previous, _)| index >= previous)
        {
            points.insert(
                number,
                (
                    *index,
                    json!({"moveNumber":number,"winrate":winrate,"scoreLead":score}),
                ),
            );
        }
    }
    process.cancellation.check()?;
    if detailed {
        return Ok(Value::Array(detailed_points.into_values().collect()));
    }
    Ok(Value::Array(
        points.into_values().map(|(_, point)| point).collect(),
    ))
}
