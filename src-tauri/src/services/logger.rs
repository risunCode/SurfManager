use crate::models::AppResult;
use chrono::Utc;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;

#[derive(Debug, Clone)]
pub struct LoggerService {
    log_path: PathBuf,
}

impl LoggerService {
    pub fn new(log_path: PathBuf) -> AppResult<Self> {
        if let Some(parent) = log_path.parent() {
            fs::create_dir_all(parent)?;
        }
        let _ = OpenOptions::new().create(true).append(true).open(&log_path)?;
        Ok(Self { log_path })
    }

    pub fn log(&self, msg: &str) -> AppResult<()> {
        println!("{}", msg);
        let mut f = OpenOptions::new().create(true).append(true).open(&self.log_path)?;
        writeln!(f, "{} {}", Utc::now().to_rfc3339(), msg)?;
        Ok(())
    }

    pub fn get_logs(&self) -> AppResult<String> {
        Ok(fs::read_to_string(&self.log_path).unwrap_or_default())
    }
}
