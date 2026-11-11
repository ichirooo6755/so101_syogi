//! GPU detection is invoked only after an explicit GPU opt-in. Device indices
//! come from the compute APIs, never from Windows display-adapter ordering.
use crate::{
    domain::AppSettings,
    protocol::{Cancellation, EngineProcess},
};
use anyhow::{bail, ensure, Context, Result};
use std::{path::Path, sync::Arc};

#[cfg(windows)]
mod windows;

#[derive(Clone, Debug)]
pub struct GpuDevice {
    pub backend: String,
    pub index: u32,
    pub name: String,
    pub score: u64,
}

pub fn executable(settings: &AppSettings) -> Result<&str> {
    if !settings.use_gpu {
        return Ok(&settings.katago_path);
    }
    match settings.gpu_backend.as_str() {
        "cuda" => Ok(&settings.cuda_path),
        "opencl" => Ok(&settings.opencl_path),
        _ => bail!("GPUが未確認です。AI詳細設定で「GPUを用いる」を選び直してください。"),
    }
}

pub fn device_overrides(settings: &AppSettings) -> Result<String> {
    if !settings.use_gpu {
        return Ok(String::new());
    }
    let key = match settings.gpu_backend.as_str() {
        "cuda" => "cudaDeviceToUse",
        "opencl" => "openclDeviceToUse",
        _ => bail!("GPUの実行方式が未確認です。"),
    };
    Ok(format!(
        ",numNNServerThreadsPerModel=1,{key}={0},{key}Thread0={0}",
        settings.gpu_device_index
    ))
}

pub fn reset_to_cpu(settings: &mut AppSettings) {
    settings.use_gpu = false;
    settings.gpu_backend.clear();
    settings.gpu_name.clear();
    settings.gpu_device_index = 0;
}

pub fn configure(settings: &mut AppSettings, cancellation: Arc<Cancellation>) -> Result<()> {
    if !settings.use_gpu {
        reset_to_cpu(settings);
        return Ok(());
    }
    cancellation.check()?;
    #[cfg(windows)]
    let devices = windows::detect(&settings.cuda_path)?;
    #[cfg(not(windows))]
    let devices: Vec<GpuDevice> = Vec::new();
    configure_with_devices(settings, devices, cancellation)
}

/// Also used by protocol integration tests with real fixture child processes.
pub fn configure_with_devices(
    settings: &mut AppSettings,
    mut devices: Vec<GpuDevice>,
    cancellation: Arc<Cancellation>,
) -> Result<()> {
    ensure!(
        !devices.is_empty(),
        "利用可能なGPUを検出できませんでした。GPUドライバーを確認するか、CPUを使用してください。"
    );
    // Prefer usable CUDA, then the ranked OpenCL GPU candidates.
    devices.sort_by_key(|device| std::cmp::Reverse(device.score));
    let mut failures = Vec::new();
    for device in devices {
        cancellation.check()?;
        let mut candidate = settings.clone();
        candidate.use_gpu = true;
        candidate.gpu_backend = device.backend.clone();
        candidate.gpu_device_index = device.index;
        candidate.gpu_name = device.name.clone();
        let attempt = (|| -> Result<()> {
            let path = executable(&candidate)?;
            ensure!(
                Path::new(path).is_file(),
                "同梱エンジンが見つかりません: {path}"
            );
            // A small real inference verifies the model, runtime DLLs and GPU,
            // rather than accepting the mere presence of a vendor driver.
            let mut probe = candidate.clone();
            probe.threads = 1;
            probe.visits = 1;
            let mut process = EngineProcess::probe(&probe, cancellation.clone())?;
            process.command("boardsize 9")?;
            process.command("clear_board")?;
            process
                .analyze(
                    &crate::domain::Position {
                        board_x_size: 9,
                        board_y_size: 9,
                        komi: 6.5,
                        rules: "japanese".into(),
                        next_player: crate::domain::Color::B,
                        handicap: 0,
                        segments: vec![crate::domain::Segment {
                            initial_stones: vec![],
                            initial_player: crate::domain::Color::B,
                            moves: vec![],
                            move_offset: 0,
                        }],
                    },
                    1,
                )
                .context("GPUでの試験評価に失敗しました")?;
            Ok(())
        })();
        match attempt {
            Ok(()) => {
                cancellation.check()?;
                *settings = candidate;
                return Ok(());
            }
            Err(error) => failures.push(format!(
                "{} / {}: {error:#}",
                device.backend.to_uppercase(),
                device.name
            )),
        }
    }
    cancellation.check()?;
    bail!(
        "GPUを使用できませんでした。設定は変更していません。\n{}",
        failures.join("\n\n")
    )
}
