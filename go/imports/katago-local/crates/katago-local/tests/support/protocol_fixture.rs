//! A real child process used to test protocol, cache and cancellation behavior.
use serde_json::{json, Value};
use std::{
    io::{BufRead, Write},
    time::Duration,
};
fn main() {
    let args: Vec<_> = std::env::args().collect();
    let analysis = args.get(1).is_some_and(|s| s == "analysis");
    let model = args
        .windows(2)
        .find(|p| p[0] == "-model")
        .map(|p| p[1].as_str())
        .unwrap_or("");
    let config = args
        .windows(2)
        .find(|p| p[0] == "-config")
        .map(|p| p[1].as_str())
        .unwrap_or("");
    let mut query_index = 0;
    if model.contains("compute-fixture") {
        let mut launches = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(format!("{model}.launches"))
            .unwrap();
        writeln!(launches, "{}", json!(args)).unwrap();
        if model.contains("startup-fail")
            || (model.contains("reject-cuda")
                && args.iter().any(|arg| arg.contains("cudaDeviceToUse=")))
        {
            eprintln!("fixture GPU runtime initialization failed");
            std::process::exit(1);
        }
    }
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        if !config.is_empty() {
            let mut log = std::fs::OpenOptions::new()
                .create(true)
                .append(true)
                .open(format!("{config}.log"))
                .unwrap();
            writeln!(log, "{line}").unwrap();
        }
        if model.contains("slow")
            && (line.starts_with("genmove") || line.starts_with("kata-search_analyze") || analysis)
        {
            std::thread::sleep(Duration::from_secs(30));
        }
        if model.contains("eof") {
            return;
        }
        if analysis {
            let request: Value = serde_json::from_str(&line).unwrap();
            let turns = request["analyzeTurns"].as_array().unwrap();
            let id = &request["id"];
            println!("{}", json!({"id":id,"isDuringSearch":true}));
            for turn in turns.iter().rev() {
                println!(
                    "{}",
                    json!({"id":id,"turnNumber":turn,"rootInfo":{"winrate":0.6,"scoreLead":query_index*100+turn.as_u64().unwrap(),"visits":8}})
                );
            }
            query_index += 1;
        } else if line.starts_with("genmove") {
            println!("= B8\n");
        } else if line.starts_with("kata-search_analyze") {
            println!("= info move C7 visits 1 winrate 0.4 scoreLead -1 pv C7 pass\ninfo move B8 visits 8 winrate 0.6 scoreLead 2 pv B8 pass info move pass visits 2 winrate 0.5 scoreLead 0 pv pass\n");
        } else if line == "kata-get-param maxVisits" {
            println!("= 800\n");
        } else if line == "quit" {
            println!("=\n");
            return;
        } else {
            println!("=\n");
        }
        std::io::stdout().flush().unwrap();
    }
}
