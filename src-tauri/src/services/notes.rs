use crate::models::{AppError, AppResult, Note};
use crate::services::config::ConfigService;
use chrono::Utc;

#[derive(Debug)]
pub struct NotesService {
    config: ConfigService,
}

impl NotesService {
    pub fn new(config: ConfigService) -> Self {
        Self { config }
    }

    fn note_path(&self, id: &str) -> std::path::PathBuf {
        self.config.notes_root().join(format!("{}.json", id))
    }

    pub fn get_notes(&self) -> AppResult<Vec<Note>> {
        let dir = self.config.notes_root();
        std::fs::create_dir_all(&dir)?;
        let mut notes = Vec::new();
        for entry in std::fs::read_dir(dir)? {
            let entry = entry?;
            let path = entry.path();
            if !path.is_file() || path.extension().and_then(|s| s.to_str()) != Some("json") {
                continue;
            }
            let data = std::fs::read_to_string(path)?;
            if let Ok(note) = serde_json::from_str::<Note>(&data) {
                notes.push(note);
            }
        }
        notes.sort_by(|a, b| b.updated_at.cmp(&a.updated_at));
        Ok(notes)
    }

    pub fn get_note(&self, id: &str) -> AppResult<Note> {
        let path = self.note_path(id);
        if !path.exists() {
            return Err(AppError::NotFound(format!("note not found: {}", id)));
        }
        let data = std::fs::read_to_string(path)?;
        Ok(serde_json::from_str(&data)?)
    }

    pub fn save_note(&self, mut note: Note) -> AppResult<Note> {
        let now = Utc::now().to_rfc3339();
        if note.id.trim().is_empty() {
            note.id = uuid::Uuid::new_v4().to_string();
            note.created_at = now.clone();
        }
        note.updated_at = now;
        let data = serde_json::to_string_pretty(&note)?;
        std::fs::write(self.note_path(&note.id), data)?;
        Ok(note)
    }

    pub fn delete_note(&self, id: &str) -> AppResult<()> {
        let path = self.note_path(id);
        if path.exists() {
            std::fs::remove_file(path)?;
        }
        Ok(())
    }
}
