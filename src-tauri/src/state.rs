use crate::models::AppResult;
use crate::services::{
    apps::AppsService, backup::BackupService, config::ConfigService, logger::LoggerService, notes::NotesService,
    process::ProcessService,
};
use tokio::sync::Mutex;

pub struct AppState {
    pub config: ConfigService,
    pub apps: Mutex<AppsService>,
    pub backup: Mutex<BackupService>,
    pub notes: Mutex<NotesService>,
    pub process: Mutex<ProcessService>,
    pub logger: Mutex<LoggerService>,
}

impl AppState {
    pub fn new() -> AppResult<Self> {
        let config = ConfigService::new()?;
        config.ensure_dirs()?;
        let apps = AppsService::new(config.clone())?;
        let backup = BackupService::new(config.clone());
        let notes = NotesService::new(config.clone());
        let logger = LoggerService::new(config.logs_root().join("app.log"))?;

        Ok(Self {
            config,
            apps: Mutex::new(apps),
            backup: Mutex::new(backup),
            notes: Mutex::new(notes),
            process: Mutex::new(ProcessService::default()),
            logger: Mutex::new(logger),
        })
    }
}
