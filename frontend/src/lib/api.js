import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

export const EventsOn = async (eventName, callback) => {
  const unlisten = await listen(eventName, (event) => callback(event.payload));
  return unlisten;
};

// Apps
export const GetApps = () => invoke('get_apps');
export const GetActiveApps = () => invoke('get_active_apps');
export const GetApp = (appKey) => invoke('get_app', { appKey });
export const SaveApp = (config) => invoke('save_app', { config });
export const DeleteApp = (appKey) => invoke('delete_app', { appKey });
export const ToggleApp = (appKey) => invoke('toggle_app', { appKey });
export const ReloadApps = () => invoke('reload_apps');
export const CheckAppInstalled = (appKey) => invoke('check_app_installed', { appKey });
export const GetAppDataPath = (appKey) => invoke('get_app_data_path', { appKey });
export const OpenConfigFolder = () => invoke('open_config_folder');

// Backup / sessions
export const GetSessions = (appKey, includeAuto) => invoke('get_sessions', { appKey, includeAuto });
export const GetAllSessions = (includeAuto) => invoke('get_all_sessions', { includeAuto });
export const CreateBackup = (appKey, sessionName, addonOnly) =>
  invoke('create_backup', { appKey, sessionName, addonOnly });
export const ReplaceSessionData = (appKey, sessionName, addonOnly) =>
  invoke('replace_session_data', { appKey, sessionName, addonOnly });
export const RestoreBackup = (appKey, sessionName, skipClose) =>
  invoke('restore_backup', { appKey, sessionName, skipClose });
export const RestoreAccountOnly = (appKey, sessionName, skipClose) =>
  invoke('restore_account_only', { appKey, sessionName, skipClose });
export const RestoreAddonOnly = (appKey, sessionName, skipClose) =>
  invoke('restore_addon_only', { appKey, sessionName, skipClose });
export const ResetApp = (appKey, autoBackup, skipClose) => invoke('reset_app', { appKey, autoBackup, skipClose });
export const ResetAccountOnly = (appKey) => invoke('reset_account_only', { appKey });
export const ResetAddonData = (appKey, skipClose) => invoke('reset_addon_data', { appKey, skipClose });
export const DeleteSession = (appKey, sessionName) => invoke('delete_session', { appKey, sessionName });
export const RenameSession = (appKey, oldName, newName) => invoke('rename_session', { appKey, oldName, newName });
export const SetActiveSession = (appKey, sessionName) => invoke('set_active_session', { appKey, sessionName });
export const GetActiveSession = (appKey) => invoke('get_active_session', { appKey });
export const OpenSessionFolder = (appKey, sessionName) => invoke('open_session_folder', { appKey, sessionName });
export const CountAutoBackups = () => invoke('count_auto_backups');
export const ClearAllSessions = () => invoke('clear_all_sessions');
export const BackupAllSessions = () => invoke('backup_all_sessions');
export const CheckSessionHasAddons = (appKey, sessionName) =>
  invoke('check_session_has_addons', { appKey, sessionName });
export const VerifySessionIntegrity = (appKey, sessionName) =>
  invoke('verify_session_integrity', { appKey, sessionName });
export const OpenBackupFolder = () => invoke('open_backup_folder');
export const CalculateBackupSize = (appKey, includeData) =>
  invoke('calculate_backup_size', { appKey, includeData });

// Notes
export const GetNotes = () => invoke('get_notes');
export const GetNote = (id) => invoke('get_note', { id });
export const SaveNote = (note) => invoke('save_note', { note });
export const DeleteNote = (id) => invoke('delete_note', { id });

// System
export const GetPlatformInfo = () => invoke('get_platform_info');
export const GetCurrentUser = () => invoke('get_current_user');
export const IsAppRunning = (appKey) => invoke('is_app_running', { appKey });
export const KillApp = (appKey) => invoke('kill_app', { appKey });
export const LaunchApp = (appKey) => invoke('launch_app', { appKey });
export const OpenFolder = (path) => invoke('open_folder', { path });
export const OpenAppFolder = (appKey) => invoke('open_app_folder', { appKey });
export const OpenURL = (url) => invoke('open_url', { url });
export const LogMessage = (message) => invoke('log_message', { message });
export const GetLogs = () => invoke('get_logs');
export const GenerateNewID = (appKey) => invoke('generate_new_id', { appKey });
export const FormatSize = (bytes) => invoke('format_size', { bytes });

// File dialogs
export const SelectFile = (title, filters = []) => invoke('select_file', { title, filters });
export const SelectFolder = (title) => invoke('select_folder', { title });
export const SelectFolderFromHome = (title) => invoke('select_folder_from_home', { title });
export const SelectFolderFromRoaming = (title) => invoke('select_folder_from_roaming', { title });
export const SelectFolderFromLocalPrograms = (title) =>
  invoke('select_folder_from_local_programs', { title });
export const SelectExeFromLocalPrograms = (title) =>
  invoke('select_exe_from_local_programs', { title });
