<script context="module">
  import { writable } from 'svelte/store';

  const modalState = writable(null);
  let resolvePromise = null;

  // Export confirm function that returns a Promise
  export function confirm(options) {
    return new Promise((resolve) => {
      resolvePromise = resolve;
      modalState.set({
        title: options.title || 'Confirm',
        message: options.message || 'Are you sure?',
        confirmText: options.confirmText || 'Confirm',
        cancelText: options.cancelText || 'Cancel',
        danger: options.danger || false
      });
    });
  }

  // Convenience method for danger confirmations
  confirm.danger = (options) => confirm({ ...options, danger: true });

  // Quick helpers for common actions
  confirm.delete = (itemName) => confirm({
    title: 'Delete Confirmation',
    message: `Are you sure you want to delete "${itemName}"?\n\nThis action cannot be undone.`,
    confirmText: 'Delete',
    danger: true
  });

  confirm.reset = (appName, hasAutoBackup = true) => confirm({
    title: 'Reset Confirmation', 
    message: `Reset all data for ${appName}?\n\nThis will delete all app data.${hasAutoBackup ? '\n\nAuto-backup will be created first.' : ''}`,
    confirmText: 'Reset',
    danger: true
  });

  confirm.restore = (sessionName) => confirm({
    title: 'Restore Session',
    message: `Restore "${sessionName}"?\n\nCurrent data will be replaced with this backup.`,
    confirmText: 'Restore'
  });

  confirm.discard = () => confirm({
    title: 'Unsaved Changes',
    message: 'You have unsaved changes.\n\nDiscard them and continue?',
    confirmText: 'Discard',
    danger: true
  });

  confirm.bulkDelete = (count) => confirm({
    title: 'Delete Multiple Items',
    message: `Delete ${count} selected item(s)?\n\nThis action cannot be undone.`,
    confirmText: 'Delete All',
    danger: true
  });
</script>

<script>
  import { fade, scale } from 'svelte/transition';
  import { AlertTriangle } from 'lucide-svelte';

  let state = null;
  modalState.subscribe(value => state = value);

  function handleConfirm() {
    if (resolvePromise) resolvePromise(true);
    modalState.set(null);
  }

  function handleCancel() {
    if (resolvePromise) resolvePromise(false);
    modalState.set(null);
  }

  function handleKeydown(e) {
    if (!state) return;
    if (e.key === 'Escape') handleCancel();
    if (e.key === 'Enter') handleConfirm();
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if state}
  <div 
    class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[200]"
    transition:fade={{ duration: 150 }}
    tabindex="0"
    on:click|self={handleCancel}
    on:keydown={(e) => { if (e.key === 'Escape') handleCancel(); if (e.key === 'Enter') handleConfirm(); }}
  >
    <div 
      class="bg-[var(--bg-card)] rounded-xl border border-[var(--border)] w-full max-w-md p-6 shadow-2xl"
      transition:scale={{ duration: 200, start: 0.95 }}
    >
      <!-- Header -->
      <div class="flex items-start gap-4 mb-4">
        {#if state.danger}
          <div class="p-2 rounded-full bg-[var(--danger)]/20">
            <AlertTriangle size={24} class="text-[var(--danger)]" />
          </div>
        {/if}
        <div class="flex-1">
          <h3 class="text-lg font-semibold text-[var(--text-primary)]">{state.title}</h3>
          <p class="text-[var(--text-secondary)] mt-2 text-sm leading-relaxed whitespace-pre-line">{state.message}</p>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex justify-end gap-3 mt-6">
        <button 
          class="px-4 py-2 rounded-lg font-medium bg-[var(--bg-hover)] hover:bg-[var(--border)] border border-[var(--border)] text-[var(--text-secondary)] transition-all"
          on:click={handleCancel}
        >
          {state.cancelText}
        </button>
        <button 
          class="px-4 py-2 rounded-lg font-medium transition-all
                 {state.danger 
                   ? 'bg-[var(--danger)] hover:bg-[var(--danger)]/80 text-white' 
                   : 'bg-[var(--primary)] hover:bg-[var(--primary-light)] hover:text-black text-white'}"
          on:click={handleConfirm}
        >
          {state.confirmText}
        </button>
      </div>
    </div>
  </div>
{/if}
