use crate::{ApplicationBackend, EngineBackend};
use anyhow::{ensure, Context, Result};
use serde_json::{json, Value};
use std::{
    io::{BufRead, Write},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    time::Duration,
};

pub fn serve_lines(
    input: impl BufRead,
    mut output: impl Write,
    dispatch: impl Fn(&str, &Value) -> Result<Value>,
) -> Result<()> {
    for line in input.lines() {
        let line = line?;
        let mut id = Value::Null;
        let result = (|| -> Result<Value> {
            let request: Value = serde_json::from_str(&line)?;
            ensure!(request.is_object(), "RPC request must be an object");
            id = request["id"].clone();
            let args = request.get("args").cloned().unwrap_or_else(|| json!({}));
            ensure!(args.is_object(), "RPC args must be an object");
            dispatch(
                request["command"]
                    .as_str()
                    .context("command must be text")?,
                &args,
            )
        })();
        let response = match result {
            Ok(value) => json!({"id":id,"result":value}),
            Err(error) => json!({"id":id,"error":format!("{error:#}")}),
        };
        writeln!(output, "{response}")?;
        output.flush()?;
    }
    Ok(())
}
pub fn engine_rpc(backend: Arc<EngineBackend>) -> Result<()> {
    let result = serve_lines(std::io::stdin().lock(), std::io::stdout().lock(), |c, a| {
        backend.dispatch(c, a)
    });
    backend.close();
    result
}
pub fn application_rpc(backend: ApplicationBackend) -> Result<()> {
    let result = serve_lines(std::io::stdin().lock(), std::io::stdout().lock(), |c, a| {
        backend.dispatch(c, a)
    });
    backend.close();
    result
}
pub fn dev_server(backend: Arc<EngineBackend>, port: u16, shutdown: Arc<AtomicBool>) -> Result<()> {
    use std::io::Read;
    let server =
        tiny_http::Server::http(("127.0.0.1", port)).map_err(|error| anyhow::anyhow!("{error}"))?;
    eprintln!("Rust backend: http://127.0.0.1:{port}");
    while !shutdown.load(Ordering::SeqCst) {
        let Some(mut request) = server.recv_timeout(Duration::from_millis(100))? else {
            continue;
        };
        let header = |name: &'static str| {
            request
                .headers()
                .iter()
                .find(|h| h.field.equiv(name))
                .map(|h| h.value.as_str().to_owned())
        };
        if request.method() != &tiny_http::Method::Post
            || request.url() != "/api/backend"
            || header("Content-Type")
                .as_deref()
                .unwrap_or("")
                .split(';')
                .next()
                != Some("application/json")
        {
            request.respond(tiny_http::Response::empty(404))?;
            continue;
        }
        if let Some(origin) = header("Origin") {
            let allowed = [
                "http://127.0.0.1:1420",
                "http://localhost:1420",
                "http://127.0.0.1:5173",
                "http://localhost:5173",
            ];
            if !allowed.contains(&origin.as_str()) {
                request.respond(tiny_http::Response::empty(403))?;
                continue;
            }
        }
        let result = (|| -> Result<Value> {
            let mut bytes = Vec::new();
            request
                .as_reader()
                .take(8 * 1024 * 1024 + 1)
                .read_to_end(&mut bytes)?;
            ensure!(
                !bytes.is_empty() && bytes.len() <= 8 * 1024 * 1024,
                "invalid request size"
            );
            let args: Value = serde_json::from_slice(&bytes)?;
            ensure!(args.is_object(), "request must be an object");
            backend.dispatch(
                args["command"].as_str().context("command must be text")?,
                args.get("args").unwrap_or(&json!({})),
            )
        })();
        let body = match result {
            Ok(value) => json!({"result":value}),
            Err(error) => json!({"error":format!("{error:#}")}),
        };
        request.respond(
            tiny_http::Response::from_string(body.to_string()).with_header(
                tiny_http::Header::from_bytes("Content-Type", "application/json; charset=utf-8")
                    .unwrap(),
            ),
        )?;
    }
    backend.close();
    Ok(())
}
