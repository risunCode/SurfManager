use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupItem {
    #[serde(default)]
    pub r#type: String,
    pub path: String,
    #[serde(default)]
    pub description: String,
    #[serde(default)]
    pub optional: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppPaths {
    #[serde(default)]
    pub data_paths: Vec<String>,
    #[serde(default)]
    pub exe_paths: Vec<String>,
    #[serde(default)]
    pub reset_folder: String,
    #[serde(default)]
    pub process_names: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub app_name: String,
    pub display_name: String,
    #[serde(default)]
    pub version: String,
    #[serde(default = "default_active")]
    pub active: bool,
    #[serde(default)]
    pub description: String,
    pub paths: AppPaths,
    #[serde(default)]
    pub backup_items: Vec<BackupItem>,
    #[serde(default)]
    pub addon_backup_paths: Vec<String>,
    #[serde(default)]
    pub app_type: String,
}

fn default_active() -> bool {
    true
}
