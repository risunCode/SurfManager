use crate::models::{BackupSizeInfo, Session};
use crate::state::AppState;
use tauri::State;

#[tauri::command]
pub async fn get_sessions(state: State<'_, AppState>, app_key: String, include_auto: bool) -> Result<Vec<Session>, String> {
    state.backup.lock().await.get_sessions(&app_key, include_auto).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_all_sessions(state: State<'_, AppState>, include_auto: bool) -> Result<Vec<Session>, String> {
    let apps_guard = state.apps.lock().await;
    state.backup.lock().await.get_all_sessions(&apps_guard, include_auto).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn create_backup(state: State<'_, AppState>, app_key: String, session_name: String, addon_only: bool) -> Result<(), String> {
    if !addon_only {
        let app_opt = state.apps.lock().await.get_app(&app_key);
        if let Some(app) = app_opt {
            let _ = state.process.lock().await.smart_close(&app.display_name, &app.paths.process_names);
        }
    }
    let apps_guard = state.apps.lock().await;
    state
        .backup
        .lock()
        .await
        .create_backup(&apps_guard, &app_key, &session_name, addon_only)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn replace_session_data(
    state: State<'_, AppState>,
    app_key: String,
    session_name: String,
    addon_only: bool,
) -> Result<(), String> {
    let apps_guard = state.apps.lock().await;
    state
        .backup
        .lock()
        .await
        .replace_session_data(&apps_guard, &app_key, &session_name, addon_only)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn restore_backup(state: State<'_, AppState>, app_key: String, session_name: String, _skip_close: bool) -> Result<(), String> {
    let app_opt = state.apps.lock().await.get_app(&app_key);
    if let Some(app) = app_opt {
        let _ = state.process.lock().await.smart_close(&app.display_name, &app.paths.process_names);
    }
    let apps_guard = state.apps.lock().await;
    state
        .backup
        .lock()
        .await
        .restore_backup(&apps_guard, &app_key, &session_name)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn restore_account_only(
    state: State<'_, AppState>,
    app_key: String,
    session_name: String,
    _skip_close: bool,
) -> Result<(), String> {
    let app_opt = state.apps.lock().await.get_app(&app_key);
    if let Some(app) = app_opt {
        let _ = state.process.lock().await.smart_close(&app.display_name, &app.paths.process_names);
    }
    let apps_guard = state.apps.lock().await;
    state
        .backup
        .lock()
        .await
        .restore_account_only(&apps_guard, &app_key, &session_name)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn restore_addon_only(
    state: State<'_, AppState>,
    app_key: String,
    session_name: String,
    _skip_close: bool,
) -> Result<(), String> {
    let apps_guard = state.apps.lock().await;
    state
        .backup
        .lock()
        .await
        .restore_addon_only(&apps_guard, &app_key, &session_name)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn reset_app(state: State<'_, AppState>, app_key: String, auto_backup: bool, _skip_close: bool) -> Result<(), String> {
    let app_opt = state.apps.lock().await.get_app(&app_key);
    if let Some(app) = app_opt {
        let _ = state.process.lock().await.smart_close(&app.display_name, &app.paths.process_names);
    }
    let apps_guard = state.apps.lock().await;
    state
        .backup
        .lock()
        .await
        .reset_app(&apps_guard, &app_key, auto_backup)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn reset_account_only(state: State<'_, AppState>, app_key: String) -> Result<(), String> {
    let apps_guard = state.apps.lock().await;
    state
        .backup
        .lock()
        .await
        .reset_account_only(&apps_guard, &app_key)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn reset_addon_data(state: State<'_, AppState>, app_key: String, _skip_close: bool) -> Result<(), String> {
    let apps_guard = state.apps.lock().await;
    state
        .backup
        .lock()
        .await
        .reset_addon_data(&apps_guard, &app_key)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn delete_session(state: State<'_, AppState>, app_key: String, session_name: String) -> Result<(), String> {
    state
        .backup
        .lock()
        .await
        .delete_session(&app_key, &session_name)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn rename_session(state: State<'_, AppState>, app_key: String, old_name: String, new_name: String) -> Result<(), String> {
    state
        .backup
        .lock()
        .await
        .rename_session(&app_key, &old_name, &new_name)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn set_active_session(state: State<'_, AppState>, app_key: String, session_name: String) -> Result<(), String> {
    state
        .backup
        .lock()
        .await
        .set_active_session(&app_key, &session_name)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_active_session(state: State<'_, AppState>, app_key: String) -> Result<String, String> {
    Ok(state.backup.lock().await.get_active_session(&app_key))
}

#[tauri::command]
pub async fn open_session_folder(state: State<'_, AppState>, app_key: String, session_name: String) -> Result<(), String> {
    state
        .backup
        .lock()
        .await
        .open_session_folder(&app_key, &session_name)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn count_auto_backups(state: State<'_, AppState>) -> Result<i32, String> {
    Ok(state.backup.lock().await.count_auto_backups())
}

#[tauri::command]
pub async fn clear_all_sessions(state: State<'_, AppState>) -> Result<i32, String> {
    state.backup.lock().await.clear_all_sessions().map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn backup_all_sessions(state: State<'_, AppState>) -> Result<String, String> {
    state
        .backup
        .lock()
        .await
        .backup_all_sessions_zip()
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn check_session_has_addons(state: State<'_, AppState>, app_key: String, session_name: String) -> Result<bool, String> {
    Ok(state.backup.lock().await.check_session_has_addons(&app_key, &session_name))
}

#[tauri::command]
pub async fn verify_session_integrity(state: State<'_, AppState>, app_key: String, session_name: String) -> Result<bool, String> {
    state
        .backup
        .lock()
        .await
        .verify_session_integrity(&app_key, &session_name)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn open_backup_folder(state: State<'_, AppState>) -> Result<(), String> {
    state.backup.lock().await.open_backup_folder().map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn calculate_backup_size(
    state: State<'_, AppState>,
    app_key: String,
    include_data: bool,
) -> Result<BackupSizeInfo, String> {
    let apps_guard = state.apps.lock().await;
    state
        .backup
        .lock()
        .await
        .calculate_backup_size(&apps_guard, &app_key, include_data)
        .map_err(|e| e.to_string())
}
