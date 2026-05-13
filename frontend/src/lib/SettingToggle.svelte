<script>
  import { createEventDispatcher } from 'svelte';
  
  export let label = '';
  export let description = '';
  export let checked = false;

  const dispatch = createEventDispatcher();

  function handleChange() {
    dispatch('change', !checked);
  }
</script>

<div 
  class="flex items-center justify-between p-4 bg-[var(--bg-card)] rounded-lg cursor-pointer hover:bg-[var(--bg-hover)] transition-colors border border-[var(--border)]"
  on:click={handleChange}
  on:keydown={(e) => e.key === 'Enter' && handleChange()}
  role="button"
  tabindex="0"
>
  <div class="flex-1 pr-4">
    <p class="font-medium text-[var(--text-primary)]">{label}</p>
    {#if description}
      <p class="text-sm text-[var(--text-secondary)]">{description}</p>
    {/if}
  </div>
  
  <div 
    class="relative w-11 h-6 rounded-full flex-shrink-0 transition-colors
           {checked ? 'bg-[var(--primary)]' : 'bg-[var(--bg-elevated)] border border-[var(--border)]'}"
  >
    <div 
      class="absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-all duration-200"
      style="left: {checked ? '22px' : '4px'}"
    ></div>
  </div>
</div>
