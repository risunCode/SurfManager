pub mod commands;
pub mod models;
pub mod services;
pub mod state;

use state::AppState;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let state = AppState::new().expect("failed to initialize app state");

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(state)
        .invoke_handler(tauri::generate_handler![
            commands::apps::get_apps,
            commands::apps::get_active_apps,
            commands::apps::get_app,
            commands::apps::save_app,
            commands::apps::delete_app,
            commands::apps::toggle_app,
            commands::apps::reload_apps,
            commands::apps::check_app_installed,
            commands::apps::get_app_data_path,
            commands::apps::open_config_folder,
            commands::backup::get_sessions,
            commands::backup::get_all_sessions,
            commands::backup::create_backup,
            commands::backup::replace_session_data,
            commands::backup::restore_backup,
            commands::backup::restore_account_only,
            commands::backup::restore_addon_only,
            commands::backup::reset_app,
            commands::backup::reset_account_only,
            commands::backup::reset_addon_data,
            commands::backup::delete_session,
            commands::backup::rename_session,
            commands::backup::set_active_session,
            commands::backup::get_active_session,
            commands::backup::open_session_folder,
            commands::backup::count_auto_backups,
            commands::backup::clear_all_sessions,
            commands::backup::backup_all_sessions,
            commands::backup::check_session_has_addons,
            commands::backup::verify_session_integrity,
            commands::backup::open_backup_folder,
            commands::backup::calculate_backup_size,
            commands::notes::get_notes,
            commands::notes::get_note,
            commands::notes::save_note,
            commands::notes::delete_note,
            commands::system::get_platform_info,
            commands::system::get_current_user,
            commands::system::is_app_running,
            commands::system::kill_app,
            commands::system::launch_app,
            commands::system::open_folder,
            commands::system::open_app_folder,
            commands::system::log_message,
            commands::system::get_logs,
            commands::system::generate_new_id,
            commands::system::open_url,
            commands::system::select_file,
            commands::system::select_folder,
            commands::system::select_folder_from_home,
            commands::system::select_folder_from_roaming,
            commands::system::select_folder_from_local_programs,
            commands::system::select_exe_from_local_programs,
            commands::system::format_size
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
