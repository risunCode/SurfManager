use crate::models::Note;
use crate::state::AppState;
use tauri::State;

#[tauri::command]
pub async fn get_notes(state: State<'_, AppState>) -> Result<Vec<Note>, String> {
    state.notes.lock().await.get_notes().map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_note(state: State<'_, AppState>, id: String) -> Result<Note, String> {
    state.notes.lock().await.get_note(&id).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn save_note(state: State<'_, AppState>, note: Note) -> Result<Note, String> {
    state.notes.lock().await.save_note(note).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn delete_note(state: State<'_, AppState>, id: String) -> Result<(), String> {
    state.notes.lock().await.delete_note(&id).map_err(|e| e.to_string())
}
