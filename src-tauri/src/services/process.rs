use crate::models::{AppError, AppResult};
use std::path::Path;
use std::process::Command;
use sysinfo::{Signal, System};

#[derive(Debug, Default)]
pub struct ProcessService;

impl ProcessService {
    pub fn is_running(&self, process_names: &[String]) -> bool {
        if process_names.is_empty() {
            return false;
        }
        let mut sys = System::new_all();
        sys.refresh_all();
        for process in sys.processes().values() {
            let n = process.name().to_lowercase();
            if process_names.iter().any(|p| n.contains(&p.to_lowercase())) {
                return true;
            }
        }
        false
    }

    pub fn kill_app(&self, process_names: &[String]) -> AppResult<()> {
        if process_names.is_empty() {
            return Ok(());
        }
        let mut sys = System::new_all();
        sys.refresh_all();
        for process in sys.processes().values() {
            let n = process.name().to_lowercase();
            if process_names.iter().any(|p| n.contains(&p.to_lowercase())) {
                let _ = process.kill_with(Signal::Term);
                let _ = process.kill();
            }
        }
        Ok(())
    }

    pub fn smart_close(&self, _display_name: &str, process_names: &[String]) -> AppResult<()> {
        self.kill_app(process_names)
    }

    pub fn launch_app(&self, exe_paths: &[String]) -> AppResult<()> {
        for exe in exe_paths {
            if Path::new(exe).exists() {
                Command::new(exe).spawn()?;
                return Ok(());
            }
        }
        Err(AppError::NotFound("executable not found".to_string()))
    }
}
