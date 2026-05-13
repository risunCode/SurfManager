<script>
  import { onMount } from 'svelte';
  import { Plus, Save, Trash2 } from 'lucide-svelte';
  import { GetNotes, GetNote, SaveNote, DeleteNote } from './api.js';
  import { confirm } from './ConfirmModal.svelte';
  import { settings } from './stores/settings.js';

  let notes = [];
  let currentNote = null;
  let title = '';
  let content = '';
  let unsaved = false;
  let loading = false;
  let autoSaveTimer = null;

  onMount(loadNotes);

  async function loadNotes() {
    loading = true;
    try {
      notes = (await GetNotes()) || [];
      notes.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
    } catch (e) {
      console.error('Error loading notes:', e);
    }
    loading = false;
  }

  async function selectNote(note) {
    if (unsaved) {
      const confirmed = await confirm.discard();
      if (!confirmed) return;
    }
    
    try {
      const fullNote = await GetNote(note.id);
      currentNote = fullNote;
      title = fullNote.title || '';
      content = fullNote.content || '';
      unsaved = false;
    } catch (e) {
      console.error('Error loading note:', e);
    }
  }

  async function newNote() {
    if (unsaved) {
      const confirmed = await confirm.discard();
      if (!confirmed) return;
    }
    
    currentNote = null;
    title = '';
    content = '';
    unsaved = false;
  }

  async function saveCurrentNote() {
    const note = {
      id: currentNote?.id || '',
      title: title || 'Untitled',
      content: content,
      created_at: currentNote?.created_at || '',
      updated_at: ''
    };

    try {
      await SaveNote(note);
      unsaved = false;
      await loadNotes();
      
      if (!currentNote) {
        const saved = notes.find(n => n.title === note.title);
        if (saved) {
          currentNote = saved;
        }
      }
    } catch (e) {
      console.error('Error saving note:', e);
    }
  }

  async function deleteCurrentNote() {
    if (!currentNote) return;
    
    const confirmed = await confirm.delete(title || 'Untitled');
    if (!confirmed) return;

    try {
      await DeleteNote(currentNote.id);
      currentNote = null;
      title = '';
      content = '';
      unsaved = false;
      await loadNotes();
    } catch (e) {
      console.error('Error deleting note:', e);
    }
  }

  function handleInput() {
    unsaved = true;
    
    // Auto-save if enabled
    if ($settings.autoSaveNotes) {
      if (autoSaveTimer) clearTimeout(autoSaveTimer);
      autoSaveTimer = setTimeout(() => {
        if (unsaved && (title || content)) {
          saveCurrentNote();
        }
      }, $settings.autoSaveDelay);
    }
  }
</script>

<div class="h-full flex gap-4 animate-fadeIn">
  <div class="w-64 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)] flex flex-col overflow-hidden">
    <div class="flex items-center gap-2 p-3 border-b border-[var(--border)]">
      <button 
        class="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors"
        on:click={newNote} 
        title="New Note"
      >
        <Plus size={18} />
      </button>
      <button 
        class="p-2 rounded-lg transition-colors {unsaved ? 'text-[var(--warning)]' : 'text-[var(--text-secondary)]'} hover:bg-[var(--bg-hover)]"
        on:click={saveCurrentNote} 
        title="Save"
        disabled={!unsaved}
      >
        <Save size={18} />
      </button>
      <button 
        class="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--danger)] hover:bg-[var(--bg-hover)] transition-colors"
        on:click={deleteCurrentNote} 
        title="Delete"
        disabled={!currentNote}
      >
        <Trash2 size={18} />
      </button>
    </div>

    <div class="flex-1 overflow-auto p-2 space-y-1">
      {#if notes.length === 0}
        <p class="text-center text-[var(--text-muted)] text-sm py-4">No notes yet</p>
      {/if}
      {#each notes as note}
        <button
          class="w-full text-left p-3 rounded-lg transition-colors
                 {currentNote?.id === note.id 
                   ? 'bg-[var(--primary-dim)] text-[var(--primary-light)]' 
                   : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}"
          on:click={() => selectNote(note)}
        >
          <p class="font-medium truncate">{note.title || 'Untitled'}</p>
          <p class="text-xs text-[var(--text-muted)] mt-1">{note.updated_at || ''}</p>
        </button>
      {/each}
    </div>

    <div class="p-3 border-t border-[var(--border)] text-xs text-[var(--text-muted)]">
      {notes.length} note(s)
    </div>
  </div>

  <div class="flex-1 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)] flex flex-col overflow-hidden">
    <input
      type="text"
      class="bg-transparent border-b border-[var(--border)] px-4 py-3 text-xl font-semibold text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--primary)]"
      placeholder="Note title..."
      bind:value={title}
      on:input={handleInput}
    />

    {#if currentNote}
      <div class="px-4 py-2 text-xs text-[var(--text-muted)]">
        Modified: {currentNote.updated_at || '-'}
      </div>
    {/if}

    <textarea
      class="flex-1 bg-transparent px-4 py-3 text-[var(--text-secondary)] placeholder-[var(--text-muted)] resize-none focus:outline-none font-mono text-sm"
      placeholder="Start writing..."
      bind:value={content}
      on:input={handleInput}
    ></textarea>

    <div class="px-4 py-2 border-t border-[var(--border)] flex items-center justify-between text-xs">
      <span class="text-[var(--text-muted)]">{content.length} characters</span>
      <div class="flex items-center gap-3">
        {#if $settings.autoSaveNotes}
          <span class="text-[var(--text-muted)]">Auto-save ON</span>
        {/if}
        {#if unsaved}
          <span class="text-[var(--warning)]">Unsaved changes</span>
        {/if}
      </div>
    </div>
  </div>
</div>
