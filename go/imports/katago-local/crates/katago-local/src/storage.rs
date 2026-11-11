use crate::domain::*;
use anyhow::{Context, Result};
use rusqlite::{params, Connection, OptionalExtension};
use serde_json::{json, Value};
use std::{
    io::Write,
    path::{Path, PathBuf},
    time::Duration,
};

#[derive(Clone)]
pub struct Repository {
    path: PathBuf,
}
pub fn snake(name: &str) -> String {
    let mut out = String::new();
    for c in name.chars() {
        if c.is_ascii_uppercase() {
            out.push('_');
            out.push(c.to_ascii_lowercase());
        } else {
            out.push(c);
        }
    }
    out
}
impl Repository {
    pub fn new(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        if let Some(parent) = path.parent().filter(|p| !p.as_os_str().is_empty()) {
            std::fs::create_dir_all(parent)?;
        }
        let repo = Self { path: path.into() };
        repo.connect()?.execute_batch("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL); CREATE TABLE IF NOT EXISTS analysis_cache(cache_key TEXT PRIMARY KEY,payload_json TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);")?;
        // The original Python schema must remain usable without recreating the database.
        let conn = repo.connect()?;
        let columns = conn
            .prepare("PRAGMA table_info(analysis_cache)")?
            .query_map([], |r| r.get::<_, String>(1))?
            .collect::<std::result::Result<Vec<_>, _>>()?;
        if !columns.iter().any(|c| c == "payload_json") {
            conn.execute(
                "ALTER TABLE analysis_cache ADD COLUMN payload_json TEXT",
                [],
            )?;
        }
        if !columns.iter().any(|c| c == "created_at") {
            conn.execute("ALTER TABLE analysis_cache ADD COLUMN created_at TEXT", [])?;
        }
        Ok(repo)
    }
    fn connect(&self) -> Result<Connection> {
        let conn = Connection::open(&self.path)?;
        conn.busy_timeout(Duration::from_secs(5))?;
        Ok(conn)
    }
    pub fn load(&self, defaults: AppSettings) -> Result<AppSettings> {
        let mut settings = serde_json::to_value(defaults)?;
        let conn = self.connect()?;
        let rows = conn
            .prepare("SELECT key,value FROM settings")?
            .query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))?
            .collect::<std::result::Result<Vec<_>, _>>()?;
        for (key, value) in rows {
            for (name, current) in settings.as_object_mut().unwrap() {
                if snake(name) == key {
                    *current = match current {
                        Value::Bool(_) => Value::Bool(value.eq_ignore_ascii_case("true")),
                        Value::Number(_) => serde_json::from_str(&value)?,
                        _ => Value::String(value.clone()),
                    };
                    break;
                }
            }
        }
        let mut result: AppSettings = serde_json::from_value(settings)?;
        // Older builds persisted an unused use_gpu=true flag. It must not opt
        // users into GPU execution before they explicitly enable the new control.
        if result.gpu_backend.is_empty() {
            result.use_gpu = false;
        }
        result.validate()?;
        Ok(result)
    }
    pub fn save(&self, settings: &AppSettings) -> Result<()> {
        settings.validate()?;
        let mut conn = self.connect()?;
        let tx = conn.transaction()?;
        for (name, value) in serde_json::to_value(settings)?.as_object().unwrap() {
            let text = value
                .as_str()
                .map(str::to_owned)
                .unwrap_or_else(|| value.to_string());
            tx.execute("INSERT INTO settings(key,value) VALUES(?1,?2) ON CONFLICT(key) DO UPDATE SET value=excluded.value",params![snake(name),text])?;
        }
        tx.commit()?;
        Ok(())
    }
    pub fn get(&self, key: &str) -> Result<Option<AnalysisResult>> {
        let payload: Option<String> = self
            .connect()?
            .query_row(
                "SELECT payload_json FROM analysis_cache WHERE cache_key=?1",
                [key],
                |r| r.get(0),
            )
            .optional()?
            .flatten();
        payload
            .map(|text| -> Result<_> {
                let mut value: Value = serde_json::from_str(&text)?;
                if let Some(candidates) = value["candidate_moves"].as_array_mut() {
                    for candidate in candidates {
                        candidate["vertex"] = cache_vertex(&candidate["vertex"])?;
                        if let Some(pv) = candidate["pv"].as_array_mut() {
                            for vertex in pv {
                                *vertex = cache_vertex(vertex)?;
                            }
                        }
                    }
                }
                Ok(serde_json::from_value(value)?)
            })
            .transpose()
    }
    pub fn put(&self, key: &str, result: &AnalysisResult) -> Result<()> {
        let mut value = serde_json::to_value(result)?;
        for candidate in value["candidate_moves"].as_array_mut().unwrap() {
            candidate["vertex"] = legacy_vertex(&candidate["vertex"]);
            for vertex in candidate["pv"].as_array_mut().unwrap() {
                *vertex = legacy_vertex(vertex);
            }
        }
        self.connect()?.execute("INSERT INTO analysis_cache(cache_key,payload_json) VALUES(?1,?2) ON CONFLICT(cache_key) DO UPDATE SET payload_json=excluded.payload_json",params![key,value.to_string()])?;
        Ok(())
    }
}
fn cache_vertex(value: &Value) -> Result<Value> {
    if value.is_null() || value.is_object() {
        return Ok(value.clone());
    }
    if let Some(text) = value.as_str() {
        return Ok(serde_json::to_value(from_gtp(text, 19, 19)?)?);
    }
    let pair = value
        .as_array()
        .filter(|v| v.len() == 2)
        .context("invalid cached vertex")?;
    Ok(json!({"x":pair[0],"y":pair[1]}))
}
fn legacy_vertex(value: &Value) -> Value {
    if value.is_null() {
        Value::Null
    } else {
        json!([value["x"], value["y"]])
    }
}
pub fn atomic_write(target: &Path, bytes: &[u8]) -> Result<PathBuf> {
    let target = std::path::absolute(target)?;
    let parent = target.parent().context("save path has no parent")?;
    let mut temp = tempfile::Builder::new()
        .suffix(".tmp")
        .tempfile_in(parent)?;
    temp.write_all(bytes)?;
    temp.as_file().sync_all()?;
    temp.persist(&target).map_err(|error| error.error)?;
    Ok(target)
}
