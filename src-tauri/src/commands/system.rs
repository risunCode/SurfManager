use crate::state::AppState;
use tauri::State;

#[tauri::command]
pub async fn get_platform_info(state: State<'_, AppState>) -> Result<serde_json::Value, String> {
    serde_json::to_value(state.config.platform_info()).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_current_user(state: State<'_, AppState>) -> Result<String, String> {
    Ok(state.config.current_user())
}

#[tauri::command]
pub async fn is_app_running(state: State<'_, AppState>, app_key: String) -> Result<bool, String> {
    let apps = state.apps.lock().await;
    let app = apps.get_app(&app_key).ok_or_else(|| format!("app not found: {}", app_key))?;
    Ok(state.process.lock().await.is_running(&app.paths.process_names))
}

#[tauri::command]
pub async fn kill_app(state: State<'_, AppState>, app_key: String) -> Result<(), String> {
    let apps = state.apps.lock().await;
    let app = apps.get_app(&app_key).ok_or_else(|| format!("app not found: {}", app_key))?;
    state.process.lock().await.kill_app(&app.paths.process_names).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn launch_app(state: State<'_, AppState>, app_key: String) -> Result<(), String> {
    let apps = state.apps.lock().await;
    let app = apps.get_app(&app_key).ok_or_else(|| format!("app not found: {}", app_key))?;
    state.process.lock().await.launch_app(&app.paths.exe_paths).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn open_folder(_state: State<'_, AppState>, path: String) -> Result<(), String> {
    open::that(path).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn select_file(_state: State<'_, AppState>, title: String, _filters: Vec<String>) -> Result<String, String> {
    let picked = rfd::FileDialog::new().set_title(&title).pick_file();
    Ok(picked.map(|p| p.to_string_lossy().to_string()).unwrap_or_default())
}

#[tauri::command]
pub async fn select_folder(_state: State<'_, AppState>, title: String) -> Result<String, String> {
    let picked = rfd::FileDialog::new().set_title(&title).pick_folder();
    Ok(picked.map(|p| p.to_string_lossy().to_string()).unwrap_or_default())
}

#[tauri::command]
pub async fn select_folder_from_home(state: State<'_, AppState>, title: String) -> Result<String, String> {
    let start = dirs::home_dir().unwrap_or_else(|| state.config.documents_dir());
    let picked = rfd::FileDialog::new().set_title(&title).set_directory(start).pick_folder();
    Ok(picked.map(|p| p.to_string_lossy().to_string()).unwrap_or_default())
}

#[tauri::command]
pub async fn select_folder_from_roaming(state: State<'_, AppState>, title: String) -> Result<String, String> {
    let start = state.config.documents_dir();
    let picked = rfd::FileDialog::new().set_title(&title).set_directory(start).pick_folder();
    Ok(picked.map(|p| p.to_string_lossy().to_string()).unwrap_or_default())
}

#[tauri::command]
pub async fn select_folder_from_local_programs(_state: State<'_, AppState>, title: String) -> Result<String, String> {
    let start = std::env::var("LOCALAPPDATA").unwrap_or_default();
    let picked = if start.is_empty() {
        rfd::FileDialog::new().set_title(&title).pick_folder()
    } else {
        rfd::FileDialog::new().set_title(&title).set_directory(start).pick_folder()
    };
    Ok(picked.map(|p| p.to_string_lossy().to_string()).unwrap_or_default())
}

#[tauri::command]
pub async fn select_exe_from_local_programs(state: State<'_, AppState>, title: String) -> Result<String, String> {
    let base = std::env::var("LOCALAPPDATA").unwrap_or_else(|_| state.config.documents_dir().to_string_lossy().to_string());
    let picked = rfd::FileDialog::new()
        .set_title(&title)
        .set_directory(base)
        .add_filter("Executable", &["exe"])
        .pick_file();
    Ok(picked.map(|p| p.to_string_lossy().to_string()).unwrap_or_default())
}

#[tauri::command]
pub async fn open_app_folder(state: State<'_, AppState>, app_key: String) -> Result<(), String> {
    let apps = state.apps.lock().await;
    let path = apps.get_app_data_path(&app_key);
    if path.is_empty() {
        return Err("data path not found".to_string());
    }
    open::that(path).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn log_message(state: State<'_, AppState>, message: String) -> Result<(), String> {
    state.logger.lock().await.log(&message).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_logs(state: State<'_, AppState>) -> Result<String, String> {
    state.logger.lock().await.get_logs().map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn generate_new_id(_state: State<'_, AppState>, _app_key: String) -> Result<i32, String> {
    Ok((chrono::Utc::now().timestamp() & 0x7fff_ffff) as i32)
}

#[tauri::command]
pub async fn open_url(_state: State<'_, AppState>, url: String) -> Result<(), String> {
    open::that(url).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn format_size(_state: State<'_, AppState>, bytes: i64) -> Result<String, String> {
    Ok(crate::services::backup::format_size(bytes))
}
