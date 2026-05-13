use crate::models::{AppError, AppResult, BackupMetadata, BackupSizeInfo, Session};
use crate::services::{apps::AppsService, config::ConfigService};
use chrono::Utc;
use sha2::{Digest, Sha256};
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

#[derive(Debug)]
pub struct BackupService {
    config: ConfigService,
}

impl BackupService {
    pub fn new(config: ConfigService) -> Self {
        Self { config }
    }

    fn manual_root(&self, app: &str) -> PathBuf {
        self.config.backup_root().join(app.to_lowercase())
    }

    fn auto_root(&self, app: &str) -> PathBuf {
        self.config.auto_backup_root().join(app.to_lowercase())
    }

    fn active_file(&self, app: &str) -> PathBuf {
        self.manual_root(app).join(".active_session")
    }

    pub fn get_sessions(&self, app: &str, include_auto: bool) -> AppResult<Vec<Session>> {
        let mut out = scan_root(self.manual_root(app), app, false, &self.get_active_session(app))?;
        if include_auto {
            out.extend(scan_root(self.auto_root(app), app, true, "")?);
        }
        out.sort_by(|a, b| b.created.cmp(&a.created));
        Ok(out)
    }

    pub fn get_all_sessions(&self, apps: &AppsService, include_auto: bool) -> AppResult<Vec<Session>> {
        let mut all = Vec::new();
        for app in apps.get_active_apps() {
            all.extend(self.get_sessions(&app.app_name, include_auto)?);
        }
        all.sort_by(|a, b| b.created.cmp(&a.created));
        Ok(all)
    }

    pub fn create_backup(&self, apps: &AppsService, app: &str, session: &str, addon_only: bool) -> AppResult<()> {
        let cfg = apps.get_app(app).ok_or_else(|| AppError::NotFound(format!("app not found: {}", app)))?;
        let data = apps.get_app_data_path(app);
        if data.is_empty() {
            return Err(AppError::NotFound("data path not found".to_string()));
        }
        let dst = self.manual_root(app).join(session);
        if dst.exists() {
            return Err(AppError::Operation("session already exists".to_string()));
        }
        fs::create_dir_all(&dst)?;

        if !addon_only {
            for item in &cfg.backup_items {
                let src = Path::new(&data).join(&item.path);
                if src.exists() {
                    copy_any(&src, &dst.join(&item.path))?;
                } else if !item.optional {
                    return Err(AppError::NotFound(format!("required path missing: {}", item.path)));
                }
            }
        }

        for addon in &cfg.addon_backup_paths {
            let src = PathBuf::from(addon);
            if src.exists() {
                let name = src.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_else(|| "addon".to_string());
                copy_any(&src, &dst.join("_addons").join(name))?;
            }
        }

        self.write_meta(&dst, app, session)?;
        Ok(())
    }

    pub fn replace_session_data(&self, apps: &AppsService, app: &str, session: &str, addon_only: bool) -> AppResult<()> {
        let dst = self.manual_root(app).join(session);
        if dst.exists() {
            fs::remove_dir_all(&dst)?;
        }
        self.create_backup(apps, app, session, addon_only)
    }

    pub fn restore_backup(&self, apps: &AppsService, app: &str, session: &str) -> AppResult<()> {
        let cfg = apps.get_app(app).ok_or_else(|| AppError::NotFound(format!("app not found: {}", app)))?;
        let src_root = self.manual_root(app).join(session);
        let data = apps.get_app_data_path(app);
        if !src_root.exists() || data.is_empty() {
            return Err(AppError::NotFound("session/data path not found".to_string()));
        }
        for item in &cfg.backup_items {
            let dst = Path::new(&data).join(&item.path);
            if dst.exists() {
                remove_any(&dst)?;
            }
            let src = src_root.join(&item.path);
            if src.exists() {
                copy_any(&src, &dst)?;
            }
        }
        self.set_active_session(app, session)
    }

    pub fn restore_account_only(&self, apps: &AppsService, app: &str, session: &str) -> AppResult<()> {
        let src_root = self.manual_root(app).join(session);
        let data = apps.get_app_data_path(app);
        if !src_root.exists() || data.is_empty() {
            return Err(AppError::NotFound("session/data path not found".to_string()));
        }
        for p in ["User", "Network"] {
            let src = src_root.join(p);
            let dst = Path::new(&data).join(p);
            if dst.exists() {
                remove_any(&dst)?;
            }
            if src.exists() {
                copy_any(&src, &dst)?;
            }
        }
        self.set_active_session(app, session)
    }

    pub fn reset_app(&self, apps: &AppsService, app: &str, auto_backup: bool) -> AppResult<()> {
        if auto_backup {
            let auto_name = format!("auto-{}", Utc::now().format("%Y%m%d-%H%M%S"));
            let _ = self.create_backup(apps, app, &auto_name, false);
        }
        let cfg = apps.get_app(app).ok_or_else(|| AppError::NotFound(format!("app not found: {}", app)))?;
        let data = apps.get_app_data_path(app);
        if data.is_empty() {
            return Err(AppError::NotFound("data path not found".to_string()));
        }
        for item in &cfg.backup_items {
            let target = Path::new(&data).join(&item.path);
            if target.exists() {
                remove_any(&target)?;
            }
        }
        Ok(())
    }

    pub fn reset_account_only(&self, apps: &AppsService, app: &str) -> AppResult<()> {
        let data = apps.get_app_data_path(app);
        if data.is_empty() {
            return Err(AppError::NotFound("data path not found".to_string()));
        }
        for p in ["User", "Network"] {
            let target = Path::new(&data).join(p);
            if target.exists() {
                remove_any(&target)?;
            }
        }
        Ok(())
    }

    pub fn reset_addon_data(&self, apps: &AppsService, app: &str) -> AppResult<()> {
        let cfg = apps.get_app(app).ok_or_else(|| AppError::NotFound(format!("app not found: {}", app)))?;
        for addon in &cfg.addon_backup_paths {
            let target = PathBuf::from(addon);
            if target.exists() {
                remove_any(&target)?;
            }
        }
        Ok(())
    }

    pub fn delete_session(&self, app: &str, session: &str) -> AppResult<()> {
        let path = self.manual_root(app).join(session);
        if path.exists() {
            fs::remove_dir_all(path)?;
        }
        Ok(())
    }

    pub fn rename_session(&self, app: &str, old: &str, new: &str) -> AppResult<()> {
        let old_path = self.manual_root(app).join(old);
        let new_path = self.manual_root(app).join(new);
        if !old_path.exists() {
            return Err(AppError::NotFound("session not found".to_string()));
        }
        fs::rename(old_path, new_path)?;
        Ok(())
    }

    pub fn set_active_session(&self, app: &str, session: &str) -> AppResult<()> {
        fs::create_dir_all(self.manual_root(app))?;
        fs::write(self.active_file(app), session)?;
        Ok(())
    }

    pub fn get_active_session(&self, app: &str) -> String {
        fs::read_to_string(self.active_file(app)).unwrap_or_default().trim().to_string()
    }

    pub fn restore_addon_only(&self, apps: &AppsService, app: &str, session: &str) -> AppResult<()> {
        let cfg = apps.get_app(app).ok_or_else(|| AppError::NotFound(format!("app not found: {}", app)))?;
        let src_root = self.manual_root(app).join(session).join("_addons");
        if !src_root.exists() {
            return Ok(());
        }
        for addon in &cfg.addon_backup_paths {
            let dst = PathBuf::from(addon);
            let name = dst.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_else(|| "addon".to_string());
            let src = src_root.join(name);
            if src.exists() {
                if dst.exists() {
                    remove_any(&dst)?;
                }
                copy_any(&src, &dst)?;
            }
        }
        Ok(())
    }

    pub fn check_session_has_addons(&self, app: &str, session: &str) -> bool {
        self.manual_root(app).join(session).join("_addons").exists()
    }

    pub fn open_session_folder(&self, app: &str, session: &str) -> AppResult<()> {
        let path = self.manual_root(app).join(session);
        if !path.exists() {
            return Err(AppError::NotFound("session folder not found".to_string()));
        }
        open::that(path)?;
        Ok(())
    }

    pub fn count_auto_backups(&self) -> i32 {
        let mut count = 0;
        if let Ok(app_dirs) = fs::read_dir(self.config.auto_backup_root()) {
            for app_dir in app_dirs.flatten() {
                if let Ok(entries) = fs::read_dir(app_dir.path()) {
                    for e in entries.flatten() {
                        if e.path().is_dir() {
                            count += 1;
                        }
                    }
                }
            }
        }
        count
    }

    pub fn clear_all_sessions(&self) -> AppResult<i32> {
        let mut removed = 0;
        for root in [self.config.backup_root(), self.config.auto_backup_root()] {
            if !root.exists() {
                continue;
            }
            for app in fs::read_dir(root)? {
                let app = app?;
                for entry in fs::read_dir(app.path())? {
                    let entry = entry?;
                    if entry.path().is_dir() {
                        fs::remove_dir_all(entry.path())?;
                        removed += 1;
                    }
                }
            }
        }
        Ok(removed)
    }

    pub fn backup_all_sessions_zip(&self) -> AppResult<String> {
        let out = self.config.documents_dir().join(format!(
            "SurfManager_all_sessions_{}.zip",
            Utc::now().format("%Y%m%d_%H%M%S")
        ));
        let file = fs::File::create(&out)?;
        let mut zip = zip::ZipWriter::new(file);
        let options = zip::write::FileOptions::default().compression_method(zip::CompressionMethod::Deflated);
        for (root, root_name) in [
            (self.config.backup_root(), "backup"),
            (self.config.auto_backup_root(), "auto-backups"),
        ] {
            if !root.exists() {
                continue;
            }
            for entry in WalkDir::new(&root).into_iter().filter_map(|e| e.ok()) {
                let path = entry.path();
                if !path.is_file() {
                    continue;
                }
                let rel = path.strip_prefix(&root).unwrap_or(path).to_string_lossy().replace('\\', "/");
                zip.start_file(format!("{}/{}", root_name, rel), options)?;
                zip.write_all(&fs::read(path)?)?;
            }
        }
        zip.finish()?;
        Ok(out.to_string_lossy().to_string())
    }

    pub fn open_backup_folder(&self) -> AppResult<()> {
        open::that(self.config.backup_root())?;
        Ok(())
    }

    pub fn verify_session_integrity(&self, app: &str, session: &str) -> AppResult<bool> {
        let dir = self.manual_root(app).join(session);
        let meta_path = dir.join(".backup_meta.json");
        if !dir.exists() || !meta_path.exists() {
            return Ok(false);
        }
        let meta: BackupMetadata = serde_json::from_str(&fs::read_to_string(meta_path)?)?;
        Ok(hash_dir(&dir)? == meta.hash)
    }

    pub fn calculate_backup_size(&self, apps: &AppsService, app: &str, include_data: bool) -> AppResult<BackupSizeInfo> {
        let cfg = apps.get_app(app).ok_or_else(|| AppError::NotFound(format!("app not found: {}", app)))?;
        let mut data_size = 0_i64;
        let data = apps.get_app_data_path(app);
        if include_data && !data.is_empty() {
            for item in &cfg.backup_items {
                data_size += dir_size(&Path::new(&data).join(&item.path))?;
            }
        }
        let mut addon_size = 0_i64;
        for addon in &cfg.addon_backup_paths {
            addon_size += dir_size(Path::new(addon))?;
        }
        let total_size = data_size + addon_size;
        Ok(BackupSizeInfo {
            data_size,
            addon_size,
            total_size,
            data_size_formatted: format_size(data_size),
            addon_size_formatted: format_size(addon_size),
            total_size_formatted: format_size(total_size),
        })
    }

    fn write_meta(&self, dst: &Path, app: &str, session: &str) -> AppResult<()> {
        let meta = BackupMetadata {
            app: app.to_string(),
            session: session.to_string(),
            created: Utc::now().to_rfc3339(),
            hash: hash_dir(dst)?,
            hash_version: 2,
            size: dir_size(dst)?,
            file_count: count_files(dst)? as i32,
        };
        fs::write(dst.join(".backup_meta.json"), serde_json::to_string_pretty(&meta)?)?;
        Ok(())
    }
}

fn scan_root(root: PathBuf, app: &str, is_auto: bool, active: &str) -> AppResult<Vec<Session>> {
    if !root.exists() {
        return Ok(Vec::new());
    }
    let mut out = Vec::new();
    for entry in fs::read_dir(root)? {
        let entry = entry?;
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }
        let name = entry.file_name().to_string_lossy().to_string();
        if name.starts_with('.') {
            continue;
        }
        if is_auto && !name.starts_with("auto-") {
            continue;
        }
        if !is_auto && name.starts_with("auto-") {
            continue;
        }
        let modified = fs::metadata(&path)?.modified().ok().map(|t| chrono::DateTime::<Utc>::from(t).to_rfc3339()).unwrap_or_default();
        out.push(Session {
            name: name.clone(),
            app: app.to_lowercase(),
            size: dir_size(&path)?,
            created: modified.clone(),
            modified,
            is_active: !is_auto && active == name,
            is_auto,
            corrupted: false,
        });
    }
    Ok(out)
}

fn copy_any(src: &Path, dst: &Path) -> AppResult<()> {
    if src.is_file() {
        if let Some(parent) = dst.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::copy(src, dst)?;
        return Ok(());
    }
    for entry in WalkDir::new(src).into_iter().filter_map(|e| e.ok()) {
        let p = entry.path();
        let rel = p.strip_prefix(src).unwrap_or(p);
        let t = dst.join(rel);
        if p.is_dir() {
            fs::create_dir_all(&t)?;
        } else {
            if let Some(parent) = t.parent() {
                fs::create_dir_all(parent)?;
            }
            fs::copy(p, t)?;
        }
    }
    Ok(())
}

fn remove_any(path: &Path) -> AppResult<()> {
    if path.is_dir() {
        fs::remove_dir_all(path)?;
    } else {
        fs::remove_file(path)?;
    }
    Ok(())
}

fn dir_size(path: &Path) -> AppResult<i64> {
    if !path.exists() {
        return Ok(0);
    }
    if path.is_file() {
        return Ok(fs::metadata(path)?.len() as i64);
    }
    let mut n = 0_i64;
    for entry in WalkDir::new(path).into_iter().filter_map(|e| e.ok()) {
        if entry.path().is_file() {
            n += entry.path().metadata()?.len() as i64;
        }
    }
    Ok(n)
}

fn count_files(path: &Path) -> AppResult<usize> {
    if !path.exists() {
        return Ok(0);
    }
    let mut n = 0;
    for entry in WalkDir::new(path).into_iter().filter_map(|e| e.ok()) {
        if entry.path().is_file() {
            n += 1;
        }
    }
    Ok(n)
}

fn hash_dir(root: &Path) -> AppResult<String> {
    let mut hasher = Sha256::new();
    let mut files = Vec::new();
    for entry in WalkDir::new(root).into_iter().filter_map(|e| e.ok()) {
        if entry.path().is_file() && entry.file_name() != ".backup_meta.json" {
            files.push(entry.path().to_path_buf());
        }
    }
    files.sort();
    for file in files {
        let rel = file.strip_prefix(root).unwrap_or(&file).to_string_lossy().replace('\\', "/");
        hasher.update(rel.as_bytes());
        let mut f = fs::File::open(file)?;
        let mut buf = [0_u8; 65536];
        loop {
            let n = f.read(&mut buf)?;
            if n == 0 {
                break;
            }
            hasher.update(&buf[..n]);
        }
    }
    Ok(format!("{:x}", hasher.finalize()))
}

pub fn format_size(bytes: i64) -> String {
    let units = ["B", "KB", "MB", "GB", "TB"];
    let mut val = bytes as f64;
    let mut idx = 0;
    while val >= 1024.0 && idx < units.len() - 1 {
        val /= 1024.0;
        idx += 1;
    }
    if idx == 0 {
        format!("{} {}", bytes, units[idx])
    } else {
        format!("{:.2} {}", val, units[idx])
    }
}
