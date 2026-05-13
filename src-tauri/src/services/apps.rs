use crate::models::{AppConfig, AppError, AppResult};
use crate::services::config::ConfigService;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug)]
pub struct AppsService {
    config: ConfigService,
    apps: HashMap<String, AppConfig>,
}

impl AppsService {
    pub fn new(config: ConfigService) -> AppResult<Self> {
        let mut service = Self {
            config,
            apps: HashMap::new(),
        };
        service.reload()?;
        Ok(service)
    }

    pub fn reload(&mut self) -> AppResult<()> {
        self.apps.clear();
        let dir = self.config.config_root();
        std::fs::create_dir_all(&dir)?;

        for entry in std::fs::read_dir(&dir)? {
            let entry = entry?;
            let path = entry.path();
            if !path.is_file() || path.extension().and_then(|s| s.to_str()) != Some("json") {
                continue;
            }
            let data = std::fs::read_to_string(&path)?;
            let cfg: AppConfig = serde_json::from_str(&data)?;
            self.apps.insert(cfg.app_name.to_lowercase(), cfg);
        }
        Ok(())
    }

    pub fn get_all_apps(&self) -> Vec<AppConfig> {
        self.apps.values().cloned().collect()
    }

    pub fn get_active_apps(&self) -> Vec<AppConfig> {
        self.apps.values().filter(|a| a.active).cloned().collect()
    }

    pub fn get_app(&self, app_key: &str) -> Option<AppConfig> {
        self.apps.get(&app_key.to_lowercase()).cloned()
    }

    pub fn save_app(&mut self, app: AppConfig) -> AppResult<()> {
        if app.app_name.trim().is_empty() {
            return Err(AppError::InvalidInput("app_name is required".to_string()));
        }
        let key = app.app_name.to_lowercase();
        let path = self.config.config_root().join(format!("{}.json", key));
        let json = serde_json::to_string_pretty(&app)?;
        std::fs::write(path, json)?;
        self.apps.insert(key, app);
        Ok(())
    }

    pub fn delete_app(&mut self, app_key: &str) -> AppResult<()> {
        let key = app_key.to_lowercase();
        let path = self.config.config_root().join(format!("{}.json", key));
        if path.exists() {
            std::fs::remove_file(path)?;
        }
        self.apps.remove(&key);
        Ok(())
    }

    pub fn toggle_app(&mut self, app_key: &str) -> AppResult<()> {
        let key = app_key.to_lowercase();
        let mut app = self
            .apps
            .get(&key)
            .cloned()
            .ok_or_else(|| AppError::NotFound(format!("app not found: {}", app_key)))?;
        app.active = !app.active;
        self.save_app(app)
    }

    pub fn check_app_installed(&self, app_key: &str) -> bool {
        self.get_app(app_key)
            .map(|app| app.paths.exe_paths.iter().any(|p| Path::new(p).exists()))
            .unwrap_or(false)
    }

    pub fn get_app_data_path(&self, app_key: &str) -> String {
        if let Some(app) = self.get_app(app_key) {
            for p in app.paths.data_paths {
                if Path::new(&p).exists() {
                    return p;
                }
            }
        }
        String::new()
    }

    pub fn open_config_folder(&self) -> AppResult<()> {
        open::that(self.config.config_root())?;
        Ok(())
    }
}
