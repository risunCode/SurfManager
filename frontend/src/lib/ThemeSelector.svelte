<script>
  import { theme } from './stores/theme.js';
  import { Sun, Moon, Palette } from 'lucide-svelte';

  const themes = [
    { id: 'dark', label: 'Dark', icon: Moon },
    { id: 'solarized', label: 'Solarized Dark', icon: Palette },
    { id: 'solarized-light', label: 'Solarized Light', icon: Sun },
  ];
</script>

<div class="flex gap-1 p-1 bg-[var(--bg-card)] rounded-lg border border-[var(--border)]">
  {#each themes as t}
    <button
      class="p-2 rounded-md transition-all {$theme === t.id 
        ? 'bg-[var(--primary)] text-white' 
        : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}"
      on:click={() => theme.set(t.id)}
      title={t.label}
    >
      <svelte:component this={t.icon} size={16} />
    </button>
  {/each}
</div>
