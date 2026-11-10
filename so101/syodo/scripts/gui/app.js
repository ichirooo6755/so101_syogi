"use strict";
const $ = (id) => document.getElementById(id);
let state, token, selectedPose = "upright", mode = "write", initialized = false;
let pending = false, wordTimer, toastTimer, dirtyWrite = false, cameraLoading = false;
let glyphVersion = 0, lastJobState = "idle", lastLog = "", serverOnline = false;
let lastPoseList = "";
let lastLayoutKey = "";
function friendly(text) { return String(text).replaceAll("ID4", "手首の曲げ").replaceAll("ID5", "筆元の回転").replaceAll("ID6", "先端の傾き"); }
const svgNS = "http://www.w3.org/2000/svg";

function toast(message, error = false) {
  $("toast").textContent = friendly(message);
  $("toast").classList.toggle("error", error);
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $("toast").hidden = true; }, error ? 9000 : 3500);
}

async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json", "X-Syodo-Token": token }, body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "操作できませんでした。");
  return data;
}

function showPage(name) {
  document.querySelectorAll(".page").forEach(el => { el.hidden = el.id !== `page-${name}`; });
  document.querySelectorAll(".nav").forEach(el => {
    const active = el.dataset.page === name;
    el.classList.toggle("active", active);
    if (active) el.setAttribute("aria-current", "page"); else el.removeAttribute("aria-current");
  });
}

function fillSettings(s) {
  $("word").value = s.word;
  $("speed").value = s.speed;
  $("camera-enabled").checked = s.camera_enabled;
  $("glyph-mm").value = s.glyph_mm;
  $("paper-depth").value = s.paper_depth_mm ?? "";
  $("paper-width").value = s.paper_width_mm ?? "";
  $("travel-mm").value = s.travel_mm;
  $("ink-mode").value = s.ink_mode;
  $("ink-trips").value = s.ink_trips;
  $("ink-speed").value = s.ink_speed_mm_s;
  $("ink-dwell").value = s.ink_dwell_s;
  $("ink-wait").value = s.ink_wait_s;
  $("ink-lift").value = s.ink_lift_mm;
  $("loadcell-enabled").checked = s.loadcell_enabled;
  $("force-limit").value = s.force_limit_n;
  $("brush-length").value = s.brush_length_mm;
  $("tuft-length").value = s.tuft_mm;
  $("brush-reach").value = s.reach_mm ?? "";
  for (const [id, key] of [["camera-url", "camera_url"], ["follower-port", "follower_port"], ["leader-port", "leader_port"], ["sim-python", "sim_python"], ["hw-python", "hw_python"]]) $(id).value = s[key];
  ["roi-x0", "roi-y0", "roi-x1", "roi-y1"].forEach((id, i) => { $(id).value = s.camera_roi[i]; });
  updateLocalControls();
}

function updateLocalControls() {
  $("speed-value").textContent = `${Number($("speed").value).toFixed(1)} ×`;
  const camera = $("camera-enabled").checked;
  $("camera-mode-hint").textContent = camera ? "映像の受信が途切れたら現在位置に停止します。" : "カメラなしで使用します。";
  $("camera-panel").hidden = !camera;
}

function render(s) {
  state = s; token = s.token || token; serverOnline = true;
  if (!initialized) { fillSettings(s.settings); initialized = true; drawWord(); }
  const busy = s.job.active || pending;
  document.body.classList.toggle("job-running", s.job.active);
  document.querySelector(".activity").classList.toggle("running", s.job.active);
  document.querySelectorAll("button,input").forEach(el => {
    if (el.classList.contains("nav") || el.id === "stop") return;
    el.disabled = busy;
  });
  $("stop").disabled = !s.job.active || s.job.state === "stopping";
  $("stop").textContent = s.job.state === "stopping" ? "停止中…" : "■ 停止";
  $("write").disabled = busy || !s.prepared || dirtyWrite || !s.pressure_ready || !s.air_verified || (s.settings.ink_mode === "automatic" && !s.ink_verified) || !s.follower_present;
  $("air-test").disabled = busy || !s.prepared || dirtyWrite || !s.follower_present;
  $("prepare").disabled = busy || !s.pressure_ready;
  $("bilateral").disabled = busy || !s.ready;
  $("pressure-plan").disabled = busy || !s.ready;
  $("pressure-calibrate").disabled = busy || !s.pressure_plan_ready;
  $("ink-prepare").disabled = busy || !s.ready || s.settings.ink_mode !== "automatic";
  $("ink-test").disabled = busy || !s.ink_prepared;
  const missing = s.poses.filter(p => p.name !== "suzuri_pull" && !p.recorded);
  const done = 12 - missing.length;
  $("setup-progress").textContent = `${done} / 12 記録`;
  $("setup-dot").hidden = s.ready;
  $("ready-note").classList.toggle("good", s.ready);
  $("ready-note").textContent = !s.ready ? "「準備」で筆と机の較正をしてください。" : !s.pressure_ready ? "「準備」で筆圧を合わせてください。" : s.prepared && !dirtyWrite ? s.air_verified ? "空中試験を確認しました。書き始められます。" : "まず空中で試し、接触しなかったことを結果欄に記録してください。" : "準備が整いました。文字を選んで軌道を確認。";
  $("brush-summary").textContent = `筆 ${s.settings.brush_length_mm} mm / 穂 ${s.settings.tuft_mm} mm`;
  $("connection-text").textContent = s.job.active ? "実行中" : s.ready ? "較正済み" : "準備が必要";
  $("connection").firstElementChild.className = `status-dot ${s.job.active ? "running" : s.ready ? "good" : ""}`;
  $("job-label").textContent = s.job.label;
  $("job-dot").className = `status-dot ${s.job.active ? "running" : s.job.state === "error" ? "error" : s.job.state === "done" ? "good" : ""}`;
  const states = { idle: "準備をして、最初の一文字を。", running: "処理中です", stopping: "処理の終了を待っています", done: "完了", error: "ログを確認してください", stopped: "停止しました" };
  $("job-state").textContent = states[s.job.state] || "";
  $("session-review").hidden = !s.last_run || s.job.active;
  $("review-prompt").textContent = s.last_run_action === "air-test" ? "空中移動で紙や硯に触れず、狙った場所を通りましたか？" : s.last_run_action === "ink-test" ? "硯の動きと位置は正しく、周囲に接触しませんでしたか？" : "今の字・教示の結果を記録する";
  $("review-good").textContent = ["air-test", "ink-test"].includes(s.last_run_action) ? "接触なし・正常" : "良い";
  $("camera-calibrate").disabled = busy || !s.ready || !s.settings.camera_enabled;
  $("camera-detect").disabled = busy || !s.ready || !s.settings.camera_enabled || !s.camera_calibrated;
  $("camera-apply").disabled = busy || !s.camera_proposal || !s.ready;
  if (s.camera_proposal) $("camera-detection-status").textContent = `紙の四隅の誤差 ${s.camera_proposal.paper_error_mm.toFixed(1)} mm、中央 ${s.camera_proposal.centre_error_mm.toFixed(1)} mm。画像を確認して反映後、筆圧と空中移動を再確認してください。`;
  const force = s.loadcell;
  $("force-value").textContent = force.valid ? `${force.axis_force_n.toFixed(3)} N` : "— N";
  $("force-raw").textContent = force.raw_counts !== null ? `生値 ${force.raw_counts}` : "生値 —";
  $("force-status").textContent = !force.enabled ? "使用しない設定です" : !force.connected ? force.error || "ESPからの受信待ち" : !force.valid ? "生値を受信中。ゼロ点・換算・別の重りでの確認を完了してください" : `計測方向の力を受信中。時刻の不確かさ ±${(force.clock_uncertainty_s * 1000).toFixed(1)} ms`;
  $("live-force").textContent = force.enabled ? force.valid ? `荷重 ${force.axis_force_n.toFixed(2)} N` : "荷重 未較正・未受信" : "";
  for (const id of ["force-tare", "force-gain", "force-verify"]) $(id).disabled = busy || !force.connected;
  const prompt = s.job.prompt;
  $("job-prompt").hidden = !prompt || s.job.state === "stopping";
  if (prompt) {
    $("prompt-text").textContent = prompt.text;
    $("prompt-continue").hidden = prompt.kind !== "continue";
    $("prompt-lines").hidden = prompt.kind !== "line";
    $("prompt-continue").disabled = pending;
    document.querySelectorAll("[data-line]").forEach(b => { b.disabled = pending; });
    $("job-state").textContent = "入力を待っています";
  }
  const log = s.job.lines.map(l => l.text).join("\n");
  if (log !== lastLog) { $("log").textContent = log; $("log").scrollTop = $("log").scrollHeight; lastLog = log; }
  if (lastJobState !== s.job.state && s.job.state === "error") { $("log-details").open = true; toast("操作に失敗しました。操作ログを確認してください。", true); }
  if (lastJobState !== s.job.state && s.job.state === "done" && s.job.action === "snap") {
    const index = s.poses.findIndex(p => p.name === selectedPose);
    const next = s.poses.slice(index + 1).find(p => !p.recorded && p.name !== "suzuri_pull");
    if (next) selectedPose = next.name;
  }
  if (lastJobState !== s.job.state && s.job.state === "done" && s.job.action === "preview") loadReference();
  if (lastJobState !== s.job.state && s.job.state === "done" && ["camera-calibrate", "camera-detect"].includes(s.job.action)) { $("camera-overlay").src = `/api/camera-overlay?t=${Date.now()}`; $("camera-overlay").hidden = false; }
  lastJobState = s.job.state;
  renderPoses(s, busy);
  $("desk-path").textContent = `較正の保存先：${s.desk_path}`;
  const paper = s.desk.paper;
  $("paper-size").textContent = s.ready && paper ? `書字領域 ${Math.round(paper.height * 1000)} × ${Math.round(paper.width * 1000)} mm` : "書字領域は較正後に表示";
  const ink = s.desk.inkstone_offset_m;
  $("calibration-summary").textContent = s.ready ? "定規の値と位置の較正が一致しました。次に筆圧を合わせます。" : missing.length ? `あと${missing.length}か所の記録が必要です。` : friendly(s.validation_errors.join(" / "));
  if (ink && s.ready) $("calibration-summary").textContent += " 硯の位置も保存されています。";
  $("pressure-summary").textContent = s.pressure_ready ? "筆圧を保存しました。「書く」で文字を選べます。" : s.pressure_plan_ready ? "試験軌道を確認しました。別紙を用意し、墨なしで開始してください。" : s.ready ? "最初に試験軌道を確認します。アームは動きません。" : "位置の較正後に実行できます。";
  $("port-list").textContent = s.ports.length ? `見つかったUSB：${s.ports.join("、")}` : "USB接続中のアームはありません。接続後にポートを設定してください。";
  const layoutKey = JSON.stringify([s.layout, s.prepared, s.prepared_path, $("word").value, $("glyph-mm").value]);
  if (layoutKey !== lastLayoutKey) { lastLayoutKey = layoutKey; drawWord(); }
  if (!busy) $("prepare").disabled = !s.pressure_ready || !localLayout().fits;
}

function localLayout() {
  const depth = state?.layout.depth_mm || 0, width = state?.layout.width_mm || 0;
  const count = Array.from($("word").value.trim()).length;
  const maximum = Math.max(0, Math.min(width - 30, (depth - 30) / Math.max(count, 1)));
  const size = Number($("glyph-mm").value);
  return { depth, width, count, maximum, size, fits: count >= 1 && count <= 2 && size >= 60 && size <= maximum };
}

function renderPoses(s, busy) {
  const list = $("pose-list");
  const signature = JSON.stringify([s.poses, selectedPose, busy]);
  if (signature !== lastPoseList) {
  lastPoseList = signature;
  list.replaceChildren();
  for (const p of s.poses) {
    const button = document.createElement("button");
    button.className = `pose-button ${p.name === selectedPose ? "selected" : ""}`;
    button.disabled = busy;
    button.setAttribute("aria-pressed", String(p.name === selectedPose));
    const check = document.createElement("span"); check.className = `pose-check ${p.recorded ? "recorded" : ""}`; check.textContent = p.recorded ? "✓" : "";
    const text = document.createElement("span"); text.textContent = p.label;
    button.append(check, text);
    if (p.name === "suzuri_pull") { const note = document.createElement("span"); note.className = "optional"; note.textContent = "任意"; button.append(note); }
    button.addEventListener("click", () => { selectedPose = p.name; renderPoses(state, false); });
    list.append(button);
  }
  }
  const p = s.poses.find(p => p.name === selectedPose);
  $("pose-title").textContent = p.label;
  $("pose-hint").textContent = p.hint;
  $("pose-recorded").textContent = p.recorded ? "記録済み" : "未記録";
  $("pose-recorded").classList.toggle("good", p.recorded);
  const positions = { paper_near_left: [93,276], paper_near_right: [287,276], paper_far_left: [93,42], paper_far_right: [287,42], suzuri_pool: [346,162], suzuri_pull: [346,211] };
  const [x,y] = positions[p.name] || [190,159];
  $("pose-marker").setAttribute("cx", x); $("pose-marker").setAttribute("cy", y);
  $("desk-diagram").hidden = p.name === "sim_home";
  $("reference-panel").hidden = p.name !== "sim_home";
  $("snap").textContent = p.recorded ? "この位置で記録し直す ＋" : "この位置を記録 ＋";
}

async function loadReference() {
  const response = await fetch("/api/reference-side");
  if (!response.ok) return;
  const previous = $("reference-image").src;
  $("reference-image").src = URL.createObjectURL(await response.blob());
  $("reference-image").hidden = false;
  if (previous.startsWith("blob:")) URL.revokeObjectURL(previous);
}

async function drawWord() {
  const word = $("word").value.trim();
  const version = ++glyphVersion;
  const count = Array.from(word).length;
  const layout = localLayout();
  $("layout-hint").textContent = !layout.depth ? "まず「準備」で書く長方形を実測してください。" : !layout.fits ? `${layout.size} mm角では入りません。今の領域では最大${layout.maximum.toFixed(1)} mm角です。` : `${layout.size} mm角 × ${count}文字。紙の余白は各辺15 mm。`;
  $("paper").className = "paper measured-paper";
  const prepared = state?.prepared && !dirtyWrite;
  $("planned-image").hidden = !prepared;
  $("paper").hidden = prepared;
  if (prepared) { const source = `/api/layout-preview?run=${encodeURIComponent(state.prepared_path)}`; if (!$("planned-image").src.endsWith(source)) $("planned-image").src = source; return; }
  if (!count || count > 2 || !token || !layout.depth || !layout.width) { $("paper").textContent = "紙の実測値を設定すると、実寸に対応する配置を表示します。"; return; }
  $("paper").style.aspectRatio = `${layout.width} / ${layout.depth}`;
  try {
    const glyphs = await api("/api/glyphs", { word });
    if (version !== glyphVersion) return;
    const missing = glyphs.filter(g => !g.paths.length);
    const sheet = document.createElementNS(svgNS, "svg"); sheet.setAttribute("viewBox", `0 0 ${layout.width} ${layout.depth}`);
    for (let i = 0; i < glyphs.length; i++) {
      const g = glyphs[i];
      const size = layout.size, x = (layout.width - size) / 2, y = 15 + (layout.depth - 30) / count * (i + .5) - size / 2;
      const frame = document.createElementNS(svgNS, "rect");
      for (const [k,v] of Object.entries({x,y,width:size,height:size,fill:"none",stroke:layout.fits ? "#d8dfce" : "#b47260","stroke-width":.5})) frame.setAttribute(k,v);
      sheet.append(frame);
      const svg = document.createElementNS(svgNS, "svg");
      for (const [k,v] of Object.entries({x,y,width:size,height:size,viewBox:"0 0 109 109","aria-label":g.char,role:"img"})) svg.setAttribute(k,v);
      if (g.paths.length) {
        for (const d of g.paths) { const path = document.createElementNS(svgNS, "path"); path.setAttribute("d", d); svg.append(path); }
      } else {
        const text = document.createElementNS(svgNS, "text"); text.setAttribute("x", "54.5"); text.setAttribute("y", "82"); text.setAttribute("text-anchor", "middle"); text.setAttribute("class", "fallback"); text.textContent = g.char; svg.append(text);
      }
      sheet.append(svg);
    }
    $("paper").replaceChildren(sheet);
    $("preview-label").textContent = missing.length ? `筆順データなし：${missing.map(g => g.char).join("・")}` : "実寸の配置見本";
  } catch (error) { if (version === glyphVersion) toast(error.message, true); }
}

async function perform(action, extra = {}, save = true) {
  if (pending || state?.job.active || !serverOnline) return;
  pending = true; render(state);
  try {
    if (save) await saveWriting();
    const next = await api("/api/action", { action, ...extra });
    pending = false; render(next);
    if (["prepare", "solve", "sync-limits", "preview", "camera-test"].includes(action)) $("log-details").open = true;
  } catch (error) { pending = false; render(state); toast(error.message, true); }
}

async function saveWriting() {
  state = await api("/api/settings", { word: $("word").value.trim(), speed: Number($("speed").value), glyph_mm: Number($("glyph-mm").value), camera_enabled: $("camera-enabled").checked });
  dirtyWrite = false;
}

async function saveConnections() {
  return api("/api/settings", {
    follower_port: $("follower-port").value, leader_port: $("leader-port").value,
    sim_python: $("sim-python").value, hw_python: $("hw-python").value,
    camera_url: $("camera-url").value,
    loadcell_enabled: $("loadcell-enabled").checked, force_limit_n: Number($("force-limit").value),
    camera_roi: ["roi-x0", "roi-y0", "roi-x1", "roi-y1"].map(id => Number($(id).value)),
  });
}

function changedWriting() { dirtyWrite = true; updateLocalControls(); if (state) render(state); }
document.querySelectorAll(".nav").forEach(b => b.addEventListener("click", () => showPage(b.dataset.page)));
document.querySelectorAll("[data-word]").forEach(b => b.addEventListener("click", () => { $("word").value = b.dataset.word; changedWriting(); drawWord(); }));
$("word").addEventListener("input", () => { changedWriting(); clearTimeout(wordTimer); wordTimer = setTimeout(drawWord, 180); });
$("speed").addEventListener("input", changedWriting);
$("glyph-mm").addEventListener("input", () => { changedWriting(); drawWord(); });
$("camera-enabled").addEventListener("change", async () => {
  changedWriting();
  if (pending || state.job.active) return;
  try { await saveWriting(); render(state); if ($("camera-enabled").checked) { $("camera-panel").open = true; cameraFrame(); } }
  catch (e) { toast(e.message, true); }
});
for (const next of ["write", "bilateral"]) $("mode-" + next).addEventListener("click", () => {
  mode = next;
  $("automatic-controls").hidden = mode !== "write";
  $("bilateral-controls").hidden = mode !== "bilateral";
  for (const n of ["write", "bilateral"]) { $("mode-" + n).classList.toggle("selected", n === mode); $("mode-" + n).setAttribute("aria-pressed", String(n === mode)); }
});
$("prepare").addEventListener("click", () => perform("prepare"));
$("write").addEventListener("click", () => perform("write"));
$("air-test").addEventListener("click", () => perform("air-test"));
$("bilateral").addEventListener("click", () => perform("bilateral"));
$("snap").addEventListener("click", () => perform("snap", { pose: selectedPose }, false));
$("limp").addEventListener("click", () => perform("limp", {}, false));
$("preview-home").addEventListener("click", () => perform("preview", {}, false));
$("solve").addEventListener("click", () => perform("solve", {}, false));
$("sync-limits").addEventListener("click", () => perform("sync-limits", {}, false));
$("validate").addEventListener("click", () => perform("validate", {}, false));
$("ink-prepare").addEventListener("click", () => perform("ink-prepare", {}, false));
$("ink-test").addEventListener("click", () => perform("ink-test", {}, false));
$("pressure-plan").addEventListener("click", () => perform("pressure-plan", {}, false));
$("pressure-calibrate").addEventListener("click", () => perform("pressure-calibrate", {}, false));
$("stop").addEventListener("click", async () => { try { render(await api("/api/stop", {})); } catch(e) { toast(e.message, true); } });
$("brush-form").addEventListener("submit", async e => {
  e.preventDefault();
  try { render(await api("/api/settings", { brush_length_mm: Number($("brush-length").value), tuft_mm: Number($("tuft-length").value), reach_mm: Number($("brush-reach").value) })); toast("筆を保存しました。位置を記録してください。"); }
  catch (error) { toast(error.message, true); }
});
$("connection-form").addEventListener("submit", async e => { e.preventDefault(); try { render(await saveConnections()); toast("接続設定を保存しました。"); } catch (error) { toast(error.message, true); } });
$("paper-form").addEventListener("submit", async e => { e.preventDefault(); try { render(await api("/api/settings", {paper_depth_mm:Number($("paper-depth").value),paper_width_mm:Number($("paper-width").value),travel_mm:Number($("travel-mm").value)})); toast("実測値を保存しました。この長方形の四隅を記録してください。"); } catch(error) { toast(error.message,true); } });
$("ink-form").addEventListener("submit", async e => { e.preventDefault(); try { render(await api("/api/settings", {ink_mode:$("ink-mode").value,ink_trips:Number($("ink-trips").value),ink_speed_mm_s:Number($("ink-speed").value),ink_dwell_s:Number($("ink-dwell").value),ink_wait_s:Number($("ink-wait").value),ink_lift_mm:Number($("ink-lift").value)})); toast("硯の設定を保存しました。経路を確認してから試せます。"); } catch(error) {toast(error.message,true);} });
$("loadcell-enabled").addEventListener("change", async () => { try { render(await saveConnections()); } catch(e) {toast(e.message,true);} });
for (const [id, action, mass] of [["force-tare","tare",null],["force-gain","gain","force-mass"],["force-verify","verify","force-check-mass"]]) $(id).addEventListener("click", async () => { try { render(await api("/api/loadcell-calibrate", {action,mass_g:mass ? Number($(mass).value) : null})); toast("ロードセルの較正を保存しました。"); } catch(e) {toast(e.message,true);} });
for (const [id,result] of [["review-good","good"],["review-bad","bad"]]) $(id).addEventListener("click", async () => { try { render(await api("/api/review",{result})); toast("実物の評価を記録しました。"); } catch(e) {toast(e.message,true);} });
$("camera-test").addEventListener("click", async () => { try { render(await saveConnections()); perform("camera-test", {}, false); } catch(error) { toast(error.message, true); } });
$("esp-flash").addEventListener("click", () => perform("esp-flash", {port: $("esp-port").value.trim()}, false));
for (const id of ["camera-calibrate", "camera-detect", "camera-apply"]) $(id).addEventListener("click", () => perform(id, {}, false));

async function respond(value) {
  if (!state.job.prompt || pending) return;
  const id = state.job.prompt.id;
  pending = true; render(state);
  try { const next = await api("/api/respond", { id, value }); pending = false; render(next); }
  catch (e) { pending = false; render(state); toast(e.message, true); }
}
$("prompt-continue").addEventListener("click", () => respond(""));
document.querySelectorAll("[data-line]").forEach(b => b.addEventListener("click", () => respond(b.dataset.line)));

async function poll() {
  try { const next = await api("/api/state"); render(next); }
  catch (error) {
    serverOnline = false;
    $("connection-text").textContent = "GUIとの接続が切れました";
    $("connection").firstElementChild.className = "status-dot error";
    document.querySelectorAll("button,input").forEach(el => { if (!el.classList.contains("nav")) el.disabled = true; });
    $("job-state").textContent = "GUIに再接続中。アームの状態は確認できません。";
  }
  setTimeout(poll, 800);
}

async function cameraFrame() {
  if (!state || !serverOnline || !state.settings.camera_enabled || !$("camera-panel").open || $("page-write").hidden || document.hidden || cameraLoading) return;
  cameraLoading = true;
  try {
    const response = await fetch("/api/camera");
    if (!response.ok) { const result = await response.json(); throw new Error(result.error); }
    const old = $("camera-image").src;
    $("camera-image").src = URL.createObjectURL(await response.blob());
    $("camera-image").hidden = false; $("camera-placeholder").hidden = true;
    $("camera-status").textContent = "映像を受信中";
    if (old.startsWith("blob:")) URL.revokeObjectURL(old);
  } catch (error) {
    $("camera-image").hidden = true; $("camera-placeholder").hidden = false;
    $("camera-placeholder").textContent = "映像を受信できません。接続設定を確認してください。";
    $("camera-status").textContent = "接続できません";
  } finally { cameraLoading = false; }
}
$("camera-panel").addEventListener("toggle", cameraFrame);
setInterval(cameraFrame, 1500);
poll();

$("export-learning").addEventListener("click", () => perform("export-learning", {}, false));
