use crate::models::AppConfig;
use crate::state::AppState;
use tauri::State;

#[tauri::command]
pub async fn get_apps(state: State<'_, AppState>) -> Result<Vec<AppConfig>, String> {
    Ok(state.apps.lock().await.get_all_apps())
}

#[tauri::command]
pub async fn get_active_apps(state: State<'_, AppState>) -> Result<Vec<AppConfig>, String> {
    Ok(state.apps.lock().await.get_active_apps())
}

#[tauri::command]
pub async fn get_app(state: State<'_, AppState>, app_key: String) -> Result<Option<AppConfig>, String> {
    Ok(state.apps.lock().await.get_app(&app_key))
}

#[tauri::command]
pub async fn save_app(state: State<'_, AppState>, config: AppConfig) -> Result<(), String> {
    state.apps.lock().await.save_app(config).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn delete_app(state: State<'_, AppState>, app_key: String) -> Result<(), String> {
    state.apps.lock().await.delete_app(&app_key).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn toggle_app(state: State<'_, AppState>, app_key: String) -> Result<(), String> {
    state.apps.lock().await.toggle_app(&app_key).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn reload_apps(state: State<'_, AppState>) -> Result<(), String> {
    state.apps.lock().await.reload().map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn check_app_installed(state: State<'_, AppState>, app_key: String) -> Result<bool, String> {
    Ok(state.apps.lock().await.check_app_installed(&app_key))
}

#[tauri::command]
pub async fn get_app_data_path(state: State<'_, AppState>, app_key: String) -> Result<String, String> {
    Ok(state.apps.lock().await.get_app_data_path(&app_key))
}

#[tauri::command]
pub async fn open_config_folder(state: State<'_, AppState>) -> Result<(), String> {
    state.apps.lock().await.open_config_folder().map_err(|e| e.to_string())
}
