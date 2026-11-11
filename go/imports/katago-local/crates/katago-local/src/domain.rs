use anyhow::{bail, ensure, Result};
use serde::{Deserialize, Serialize};
use std::{collections::BTreeMap, path::Path};

pub const COLUMNS: &str = "ABCDEFGHJKLMNOPQRSTUVWXYZ";

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Color {
    B,
    W,
}
impl Color {
    pub fn opponent(self) -> Self {
        if self == Self::B {
            Self::W
        } else {
            Self::B
        }
    }
    pub fn name(self) -> &'static str {
        if self == Self::B {
            "B"
        } else {
            "W"
        }
    }
    pub fn sign(self) -> i8 {
        if self == Self::B {
            1
        } else {
            -1
        }
    }
    pub fn parse(value: &str) -> Result<Self> {
        match value {
            "B" | "black" => Ok(Self::B),
            "W" | "white" => Ok(Self::W),
            _ => bail!("color must be black or white"),
        }
    }
}

pub fn valid_rules(value: &str) -> bool {
    matches!(
        value,
        "japanese" | "chinese" | "korean" | "aga" | "new-zealand" | "tromp-taylor"
    )
}
pub fn rules_preset(value: &str) -> Option<String> {
    let normalized = value.trim().to_lowercase().replace(['_', ' '], "-");
    let name = match normalized.as_str() {
        "japan" | "japanese-rules" => "japanese",
        "china" => "chinese",
        "nz" | "newzealand" => "new-zealand",
        other => other,
    };
    valid_rules(name).then(|| name.to_owned())
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct Point {
    pub x: usize,
    pub y: usize,
}
impl Point {
    pub fn from_gtp(value: &str, width: usize, height: usize) -> Result<Self> {
        let text = value.trim().to_ascii_uppercase();
        let bytes = text.as_bytes();
        ensure!(
            bytes.len() >= 2 && bytes[1..].iter().all(u8::is_ascii_digit),
            "invalid GTP vertex: {value}"
        );
        let x = COLUMNS
            .find(bytes[0] as char)
            .ok_or_else(|| anyhow::anyhow!("invalid GTP column: {value}"))?;
        let row: usize = text[1..].parse()?;
        ensure!(
            x < width && row >= 1 && row <= height,
            "GTP vertex out of board: {value}"
        );
        Ok(Self { x, y: height - row })
    }
    pub fn to_gtp(self, width: usize, height: usize) -> Result<String> {
        ensure!(
            self.x < width.min(25) && self.y < height,
            "point out of board"
        );
        Ok(format!(
            "{}{}",
            COLUMNS.as_bytes()[self.x] as char,
            height - self.y
        ))
    }
    pub fn from_sgf(value: &str, width: usize, height: usize) -> Result<Self> {
        let bytes = value.as_bytes();
        ensure!(
            bytes.len() == 2 && bytes[0] >= b'a' && bytes[1] >= b'a',
            "invalid SGF vertex: {value}"
        );
        let p = Self {
            x: (bytes[0] - b'a') as usize,
            y: (bytes[1] - b'a') as usize,
        };
        ensure!(
            p.x < width && p.y < height,
            "SGF vertex out of board: {value}"
        );
        Ok(p)
    }
    pub fn to_sgf(self) -> String {
        format!(
            "{}{}",
            (b'a' + self.x as u8) as char,
            (b'a' + self.y as u8) as char
        )
    }
}
pub type Vertex = Option<Point>;
pub fn from_gtp(value: &str, width: usize, height: usize) -> Result<Vertex> {
    if value.trim().eq_ignore_ascii_case("pass") {
        Ok(None)
    } else {
        Point::from_gtp(value, width, height).map(Some)
    }
}
pub fn to_gtp(vertex: Vertex, width: usize, height: usize) -> Result<String> {
    vertex
        .map(|p| p.to_gtp(width, height))
        .unwrap_or_else(|| Ok("pass".into()))
}
pub fn from_sgf(value: &str, width: usize, height: usize) -> Result<Vertex> {
    if value.is_empty() || (value == "tt" && width.max(height) <= 19) {
        Ok(None)
    } else {
        Point::from_sgf(value, width, height).map(Some)
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct AppSettings {
    pub katago_path: String,
    #[serde(default)]
    pub opencl_path: String,
    #[serde(default)]
    pub cuda_path: String,
    pub model_path: String,
    pub gtp_config_path: String,
    pub analysis_config_path: String,
    pub ruleset: String,
    pub komi: f64,
    pub visits: u64,
    pub threads: u32,
    pub use_gpu: bool,
    #[serde(default)]
    pub gpu_backend: String,
    #[serde(default)]
    pub gpu_device_index: u32,
    #[serde(default)]
    pub gpu_name: String,
    pub cache_policy: String,
}
impl AppSettings {
    pub fn at(root: &Path) -> Self {
        let asset = |parts: &[&str]| {
            parts
                .iter()
                .fold(root.to_path_buf(), |path, part| path.join(part))
                .to_string_lossy()
                .into_owned()
        };
        Self {
            katago_path: asset(&["vendor", "katago", "katago.exe"]),
            opencl_path: asset(&["vendor", "katago-opencl", "katago.exe"]),
            cuda_path: asset(&["vendor", "katago-cuda", "katago.exe"]),
            model_path: asset(&["vendor", "models", "b10c384h6nbttflrs.bin.gz"]),
            gtp_config_path: asset(&["vendor", "config", "default_gtp.cfg"]),
            analysis_config_path: asset(&["vendor", "config", "analysis_example.cfg"]),
            ruleset: "japanese".into(),
            komi: 6.5,
            visits: 800,
            threads: 4,
            use_gpu: false,
            gpu_backend: String::new(),
            gpu_device_index: 0,
            gpu_name: String::new(),
            cache_policy: "reuse".into(),
        }
    }
    pub fn validate(&self) -> Result<()> {
        ensure!(
            valid_rules(&self.ruleset)
                && self.komi.is_finite()
                && self.visits > 0
                && self.threads > 0
                && matches!(self.gpu_backend.as_str(), "" | "opencl" | "cuda")
                && matches!(self.cache_policy.as_str(), "reuse" | "disabled"),
            "invalid engine settings"
        );
        Ok(())
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct GameMetadata {
    pub board_size: usize,
    pub board_height: Option<usize>,
    pub komi: f64,
    pub ruleset: String,
    pub black_name: String,
    pub white_name: String,
    pub file_name: Option<String>,
    pub handicap: usize,
    pub result: String,
    pub game_name: String,
    pub date: String,
    pub event: String,
    pub round: String,
    pub place: String,
    pub black_rank: String,
    pub white_rank: String,
    pub rules_description: Option<String>,
}
impl Default for GameMetadata {
    fn default() -> Self {
        Self {
            board_size: 19,
            board_height: None,
            komi: 6.5,
            ruleset: "japanese".into(),
            black_name: "Black".into(),
            white_name: "White".into(),
            file_name: None,
            handicap: 0,
            result: String::new(),
            game_name: String::new(),
            date: String::new(),
            event: String::new(),
            round: String::new(),
            place: String::new(),
            black_rank: String::new(),
            white_rank: String::new(),
            rules_description: None,
        }
    }
}
impl GameMetadata {
    pub fn height(&self) -> usize {
        self.board_height.unwrap_or(self.board_size)
    }
}

pub type Properties = BTreeMap<String, Vec<String>>;
#[derive(Clone, Debug, Default)]
pub struct SgfNode {
    pub properties: Properties,
    pub children: Vec<usize>,
    pub raw: BTreeMap<String, (Vec<String>, Vec<String>)>,
}
#[derive(Clone, Debug, Default)]
pub struct SgfTree {
    pub nodes: Vec<SgfNode>,
}
impl SgfTree {
    pub fn at(&self, path: &[usize]) -> Result<usize> {
        ensure!(!self.nodes.is_empty(), "empty SGF tree");
        let mut node = 0;
        for &index in path {
            node = *self.nodes[node]
                .children
                .get(index)
                .ok_or_else(|| anyhow::anyhow!("invalid SGF node path"))?;
        }
        Ok(node)
    }
    pub fn line(&self, path: &[usize]) -> Result<Vec<usize>> {
        let mut result = vec![0];
        for &index in path {
            let child = *self.nodes[*result.last().unwrap()]
                .children
                .get(index)
                .ok_or_else(|| anyhow::anyhow!("invalid SGF node path"))?;
            result.push(child);
        }
        Ok(result)
    }
}
#[derive(Clone, Debug)]
pub struct MoveRecord {
    pub move_number: usize,
    pub color: Color,
    pub vertex: Vertex,
    pub captures: Vec<Point>,
    pub comment: Option<String>,
}
#[derive(Clone, Debug)]
pub struct Game {
    pub metadata: GameMetadata,
    pub tree: SgfTree,
    pub current_path: Vec<usize>,
    pub initial_player: Color,
    pub next_player: Color,
    pub moves: Vec<MoveRecord>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct CandidateMove {
    pub vertex: Vertex,
    pub winrate: f64,
    pub score_lead: f64,
    pub visits: u64,
    pub pv: Vec<Vertex>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AnalysisResult {
    pub query_id: String,
    pub winrate: f64,
    pub score_lead: f64,
    pub visits: u64,
    pub candidate_moves: Vec<CandidateMove>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Segment {
    pub initial_stones: Vec<(Color, String)>,
    pub initial_player: Color,
    pub moves: Vec<(Color, String)>,
    pub move_offset: usize,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Position {
    pub board_x_size: usize,
    pub board_y_size: usize,
    pub komi: f64,
    pub rules: String,
    pub next_player: Color,
    #[serde(default)]
    pub handicap: usize,
    pub segments: Vec<Segment>,
}
impl Position {
    pub fn validate(&self) -> Result<()> {
        ensure!(
            (1..=25).contains(&self.board_x_size) && (1..=25).contains(&self.board_y_size),
            "invalid board dimensions"
        );
        ensure!(
            self.komi.is_finite() && valid_rules(&self.rules),
            "invalid komi or rules"
        );
        ensure!(
            !self.segments.is_empty(),
            "position requires engine segments"
        );
        let mut offset = 0;
        for segment in &self.segments {
            ensure!(segment.move_offset == offset, "invalid segment offset");
            let mut occupied = std::collections::BTreeSet::new();
            for (_, value) in &segment.initial_stones {
                let point = from_gtp(value, self.board_x_size, self.board_y_size)?
                    .ok_or_else(|| anyhow::anyhow!("invalid initial stone"))?;
                ensure!(occupied.insert(point), "duplicate initial stone");
            }
            for (_, value) in &segment.moves {
                from_gtp(value, self.board_x_size, self.board_y_size)?;
            }
            offset += segment.moves.len();
        }
        Ok(())
    }
}
