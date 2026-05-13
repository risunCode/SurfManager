use crate::models::{AppError, AppResult};
use serde::Serialize;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize)]
pub struct PlatformInfo {
    pub platform: String,
    pub arch: String,
    pub user: String,
}

#[derive(Debug, Clone)]
pub struct ConfigService {
    home_dir: PathBuf,
    user: String,
}

impl ConfigService {
    pub fn new() -> AppResult<Self> {
        let home_dir = dirs::home_dir().ok_or_else(|| AppError::Operation("unable to resolve home directory".to_string()))?;
        let user = std::env::var("USERNAME")
            .or_else(|_| std::env::var("USER"))
            .unwrap_or_else(|_| "user".to_string());
        Ok(Self { home_dir, user })
    }

    pub fn platform_info(&self) -> PlatformInfo {
        PlatformInfo {
            platform: std::env::consts::OS.to_string(),
            arch: std::env::consts::ARCH.to_string(),
            user: self.user.clone(),
        }
    }

    pub fn current_user(&self) -> String {
        self.user.clone()
    }

    pub fn documents_dir(&self) -> PathBuf {
        dirs::document_dir().unwrap_or_else(|| self.home_dir.join("Documents"))
    }

    pub fn config_root(&self) -> PathBuf {
        self.home_dir.join(".surfmanager").join("AppConfigs")
    }

    pub fn backup_root(&self) -> PathBuf {
        self.documents_dir().join("SurfManager").join("backup")
    }

    pub fn auto_backup_root(&self) -> PathBuf {
        self.documents_dir().join("SurfManager").join("auto-backups")
    }

    pub fn notes_root(&self) -> PathBuf {
        self.documents_dir().join("SurfManager").join("notes")
    }

    pub fn logs_root(&self) -> PathBuf {
        self.documents_dir().join("SurfManager").join("logs")
    }

    pub fn ensure_dirs(&self) -> AppResult<()> {
        std::fs::create_dir_all(self.config_root())?;
        std::fs::create_dir_all(self.backup_root())?;
        std::fs::create_dir_all(self.auto_backup_root())?;
        std::fs::create_dir_all(self.notes_root())?;
        std::fs::create_dir_all(self.logs_root())?;
        Ok(())
    }
}
