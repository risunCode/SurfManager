use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub name: String,
    pub app: String,
    pub size: i64,
    pub created: String,
    pub modified: String,
    pub is_active: bool,
    pub is_auto: bool,
    #[serde(default)]
    pub corrupted: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupMetadata {
    pub app: String,
    pub session: String,
    pub created: String,
    pub hash: String,
    #[serde(default)]
    pub hash_version: i32,
    #[serde(default)]
    pub size: i64,
    #[serde(default)]
    pub file_count: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupProgress {
    pub percent: i32,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupSizeInfo {
    pub data_size: i64,
    pub addon_size: i64,
    pub total_size: i64,
    pub data_size_formatted: String,
    pub addon_size_formatted: String,
    pub total_size_formatted: String,
}
