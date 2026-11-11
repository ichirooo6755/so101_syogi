#![cfg(feature = "test-fixtures")]
use katago_local::{
    domain::*,
    engine::{cache_key, EngineBackend},
    protocol::parse_analysis_output,
    ApplicationBackend,
};
use serde_json::{json, Value};
use std::{
    path::Path,
    sync::Arc,
    time::{Duration, Instant},
};
fn position() -> Value {
    json!({"boardXSize":9,"boardYSize":9,"komi":6.5,"rules":"japanese","nextPlayer":"W","handicap":0,"segments":[{"initialStones":[],"initialPlayer":"B","moves":[["B","A9"]],"moveOffset":0}]})
}
fn make_backend(dir: &Path) -> Arc<EngineBackend> {
    let backend = EngineBackend::new(dir.join("app.sqlite"), katago_local::project_root()).unwrap();
    backend.dispatch("save_settings",&json!({"settings":{"katagoPath":env!("CARGO_BIN_EXE_protocol-fixture"),"modelPath":"fixture","gtpConfigPath":dir.join("gtp.cfg"),"analysisConfigPath":dir.join("analysis.cfg")}})).unwrap();
    backend
}
fn complete(backend: &Arc<EngineBackend>, id: &Value) -> Value {
    let deadline = Instant::now() + Duration::from_secs(5);
    loop {
        let response = backend
            .dispatch("get_computation", &json!({"id":id}))
            .unwrap();
        if response["status"] != "running" {
            return response;
        }
        assert!(Instant::now() < deadline, "computation timed out");
        std::thread::sleep(Duration::from_millis(5));
    }
}
#[test]
fn finite_analysis_cache_and_position_specific_budgets() {
    let dir = tempfile::tempdir().unwrap();
    let backend = make_backend(dir.path());
    for visits in [100, 100, 200] {
        let job=backend.dispatch("start_computation",&json!({"command":"analyze_current_position","position":position(),"visits":visits})).unwrap();
        let result = complete(&backend, &job["id"]);
        assert_eq!(result["status"], "completed", "{result}");
        assert_eq!(result["result"]["visits"], 10);
        assert_eq!(result["result"]["candidates"][0]["label"], "B8");
        assert_eq!(
            result["result"]["candidates"][0]["pv"],
            json!(["B8", "pass"])
        );
    }
    let log = std::fs::read_to_string(dir.path().join("gtp.cfg.log")).unwrap();
    assert_eq!(
        log.lines()
            .filter(|l| l.starts_with("kata-search_analyze"))
            .count(),
        2
    );
    assert_eq!(
        log.lines()
            .filter(|l| *l == "kata-set-param maxVisits 800")
            .count(),
        2
    );
    backend.close();
}
#[test]
fn cancellation_releases_blocking_reads_and_completed_results() {
    let dir = tempfile::tempdir().unwrap();
    let backend = make_backend(dir.path());
    backend
        .dispatch("save_settings", &json!({"settings":{"modelPath":"slow"}}))
        .unwrap();
    let job = backend
        .dispatch(
            "start_computation",
            &json!({"command":"genmove","position":position()}),
        )
        .unwrap();
    assert!(backend
        .dispatch(
            "start_computation",
            &json!({"command":"genmove","position":position()})
        )
        .is_err());
    std::thread::sleep(Duration::from_millis(100));
    let before = Instant::now();
    let response = backend
        .dispatch("cancel_computation", &json!({"id":job["id"]}))
        .unwrap();
    assert_eq!(response["status"], "cancelled");
    assert!(response["result"].is_null());
    backend.close();
    assert!(before.elapsed() < Duration::from_secs(3));
    let backend = make_backend(dir.path());
    backend
        .dispatch(
            "save_settings",
            &json!({"settings":{"modelPath":"fixture"}}),
        )
        .unwrap();
    let job = backend
        .dispatch(
            "start_computation",
            &json!({"command":"genmove","position":position()}),
        )
        .unwrap();
    assert_eq!(complete(&backend, &job["id"])["result"], "B8");
    let cancelled = backend
        .dispatch("cancel_computation", &json!({"id":job["id"]}))
        .unwrap();
    assert_eq!(cancelled["status"], "cancelled");
    assert!(cancelled["result"].is_null());
    backend.close();
}
#[test]
fn exact_setup_stones_handicap_and_review_segment_priority() {
    let dir = tempfile::tempdir().unwrap();
    let backend = make_backend(dir.path());
    let mut source = position();
    source["segments"] = json!([{"initialStones":[["B","A9"],["W","C7"]],"initialPlayer":"W","moves":[["W","B8"]],"moveOffset":0}]);
    let job = backend
        .dispatch(
            "start_computation",
            &json!({"command":"genmove","position":source}),
        )
        .unwrap();
    assert_eq!(complete(&backend, &job["id"])["status"], "completed");
    let log = std::fs::read_to_string(dir.path().join("gtp.cfg.log")).unwrap();
    assert!(log.contains("set_position B A9 W C7"));
    assert_eq!(log.lines().filter(|l| l.starts_with("play ")).count(), 1);
    source["handicap"] = json!(2);
    source["segments"][0]["initialStones"] = json!([["B", "A9"], ["B", "C7"]]);
    let job = backend
        .dispatch(
            "start_computation",
            &json!({"command":"genmove","position":source}),
        )
        .unwrap();
    assert_eq!(complete(&backend, &job["id"])["status"], "completed");
    assert!(std::fs::read_to_string(dir.path().join("gtp.cfg.log"))
        .unwrap()
        .contains("set_free_handicap A9 C7"));
    let mut source = position();
    source["segments"].as_array_mut().unwrap().push(json!({"initialStones":[["W","B8"]],"initialPlayer":"B","moves":[["B","D6"]],"moveOffset":1}));
    let job = backend
        .dispatch(
            "start_computation",
            &json!({"command":"analyze_game","position":source}),
        )
        .unwrap();
    let result = complete(&backend, &job["id"]);
    assert_eq!(result["status"], "completed", "{result}");
    assert_eq!(
        result["result"]
            .as_array()
            .unwrap()
            .iter()
            .map(|p| p["moveNumber"].as_u64().unwrap())
            .collect::<Vec<_>>(),
        [0, 1, 2]
    );
    assert_eq!(result["result"][1]["scoreLead"], 100.0);
    backend.close();
}
#[test]
fn malformed_positions_and_settings_are_rejected() {
    let dir = tempfile::tempdir().unwrap();
    let backend = make_backend(dir.path());
    for (key, value) in [
        ("boardXSize", json!(26)),
        ("komi", Value::Null),
        ("nextPlayer", json!("X")),
    ] {
        let mut source = position();
        source[key] = value;
        assert!(backend
            .dispatch(
                "start_computation",
                &json!({"command":"genmove","position":source})
            )
            .is_err());
    }
    for (key, value) in [
        ("visits", json!(0)),
        ("threads", json!(true)),
        ("cachePolicy", json!("unknown")),
        ("unknown", json!(1)),
    ] {
        let before = backend.dispatch("get_settings", &json!({})).unwrap();
        assert!(backend
            .dispatch("save_settings", &json!({"settings":{key:value}}))
            .is_err());
        assert_eq!(
            backend.dispatch("get_settings", &json!({})).unwrap(),
            before
        );
    }
    backend.close();
}

#[test]
fn history_review_preserves_segment_boundaries_and_only_requests_missing_turns() {
    let dir = tempfile::tempdir().unwrap();
    let backend = make_backend(dir.path());
    let mut source = position();
    source["segments"].as_array_mut().unwrap().push(json!({"initialStones":[["W","B8"]],"initialPlayer":"B","moves":[["B","D6"]],"moveOffset":1}));
    let job = backend.dispatch("start_computation", &json!({"command":"analyze_game","position":source,"includeSegments":true,"turnsBySegment":[[1],[0,1]]})).unwrap();
    let response = complete(&backend, &job["id"]);
    assert_eq!(response["status"], "completed", "{response}");
    let result = response["result"].as_array().unwrap();
    assert_eq!(result.len(), 3);
    assert_eq!(result[0]["moveNumber"], 1);
    assert_eq!(result[1]["moveNumber"], 1);
    assert_eq!(result[0]["scoreLead"], 1.0);
    assert_eq!(result[1]["scoreLead"], 100.0);
    assert_eq!(result[2]["segmentIndex"], 1);
    assert_eq!(result[2]["turnNumber"], 1);
    let log = std::fs::read_to_string(dir.path().join("analysis.cfg.log")).unwrap();
    let queries: Vec<Value> = log
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect();
    assert_eq!(queries[0]["analyzeTurns"], json!([1]));
    assert_eq!(queries[1]["analyzeTurns"], json!([0, 1]));
    backend.close();
}
#[test]
fn engine_eof_is_reported_as_a_protocol_error() {
    let dir = tempfile::tempdir().unwrap();
    let backend = make_backend(dir.path());
    backend
        .dispatch("save_settings", &json!({"settings":{"modelPath":"eof"}}))
        .unwrap();
    let job = backend
        .dispatch(
            "start_computation",
            &json!({"command":"genmove","position":position()}),
        )
        .unwrap();
    let response = complete(&backend, &job["id"]);
    assert_eq!(response["status"], "error");
    assert!(
        response["error"]
            .as_str()
            .unwrap()
            .contains("応答せずに終了"),
        "{response}"
    );
    backend.close();
}
#[test]
fn legacy_async_genmove_can_be_rolled_back_after_completion() {
    let dir = tempfile::tempdir().unwrap();
    let backend =
        ApplicationBackend::new(dir.path().join("db.sqlite"), katago_local::project_root())
            .unwrap();
    backend.dispatch("save_settings",&json!({"settings":{"katagoPath":env!("CARGO_BIN_EXE_protocol-fixture"),"modelPath":"fixture","gtpConfigPath":dir.path().join("gtp.cfg")}})).unwrap();
    backend
        .dispatch(
            "new_session",
            &json!({"config":{"mode":"record","boardSize":9,"evaluationEnabled":false}}),
        )
        .unwrap();
    backend
        .dispatch("play_move", &json!({"color":"black","vertex":"A9"}))
        .unwrap();
    let before = backend.dispatch("get_state", &json!({})).unwrap();
    let job = backend
        .dispatch(
            "start_computation",
            &json!({"command":"genmove","args":{"color":"white"}}),
        )
        .unwrap();
    let deadline = Instant::now() + Duration::from_secs(5);
    loop {
        let response = backend
            .dispatch("get_computation", &json!({"id":job["id"]}))
            .unwrap();
        if response["status"] != "running" {
            assert_eq!(response["status"], "completed", "{response}");
            assert_eq!(response["result"]["state"]["moveCount"], 2);
            break;
        }
        assert!(Instant::now() < deadline);
        std::thread::sleep(Duration::from_millis(5));
    }
    backend
        .dispatch("cancel_computation", &json!({"id":job["id"]}))
        .unwrap();
    assert_eq!(backend.dispatch("get_state", &json!({})).unwrap(), before);
    backend.close();
}
#[test]
fn analysis_parser_uses_final_snapshot_and_validates_coordinates() {
    let parsed=parse_analysis_output("info move A9 visits 10 winrate 4000 scoreLead -1 pv A9\ninfo move B8 visits 8 winrate 0.6 scoreLead 2 pv B8 pass info move pass visits 2 winrate 0.5 scoreLead 0 pv pass",9,9).unwrap();
    assert_eq!(parsed.len(), 2);
    assert_eq!(parsed[0].visits, 8);
    assert_eq!(parsed[0].vertex, Some(Point { x: 1, y: 1 }));
    assert_eq!(parsed[0].pv, vec![Some(Point { x: 1, y: 1 }), None]);
    assert!(parse_analysis_output("info move Z1 visits 1", 9, 9).is_err());
    let settings = AppSettings::at(Path::new("missing"));
    let source: Position = serde_json::from_value(position()).unwrap();
    assert_ne!(
        cache_key(&settings, &source).unwrap(),
        cache_key(
            &AppSettings {
                visits: settings.visits + 1,
                ..settings.clone()
            },
            &source
        )
        .unwrap()
    );
}
