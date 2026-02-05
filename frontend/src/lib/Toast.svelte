<script context="module">
  import { writable } from 'svelte/store';

  // Toast store
  const toasts = writable([]);
  let toastId = 0;

  // Settings-aware controls
  import { settings } from './stores/settings.js';
  import { get as getStore } from 'svelte/store';
  let currentSettings = getStore(settings);
  settings.subscribe(v => currentSettings = v);

  function playBeep() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.value = 880;
      gain.gain.value = 0.05;
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.12);
    } catch (e) {
      // ignore
    }
  }

  // Export toast function for use anywhere
  export function toast(message, type = 'info', duration = 3000) {
    const cfg = currentSettings || {};
    if (cfg.muteToasts && type !== 'error') {
      return ++toastId; // still increment id to avoid clashes
    }
    const id = ++toastId;
    toasts.update(t => [...t, { id, message, type, duration }]);

    // Optional beep for completes
    if (type === 'success' && cfg.beepOnComplete && cfg.toastSound) {
      playBeep();
    }
    
    if (duration > 0) {
      setTimeout(() => {
        toasts.update(t => t.filter(toast => toast.id !== id));
      }, duration);
    }
    
    return id;
  }

  // Convenience methods
  toast.success = (msg, duration) => toast(msg, 'success', duration);
  toast.error = (msg, duration) => toast(msg, 'error', duration);
  toast.warning = (msg, duration) => toast(msg, 'warning', duration);
  toast.info = (msg, duration) => toast(msg, 'info', duration);

  export function dismissToast(id) {
    toasts.update(t => t.filter(toast => toast.id !== id));
  }
</script>

<script>
  import { fly } from 'svelte/transition';
  import { X, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-svelte';

  let toastList = [];
  toasts.subscribe(value => toastList = value);

  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info
  };

  const colors = {
    success: 'bg-[var(--success)]/20 border-[var(--success)]/50 text-[var(--success)]',
    error: 'bg-[var(--danger)]/20 border-[var(--danger)]/50 text-[var(--danger)]',
    warning: 'bg-[var(--warning)]/20 border-[var(--warning)]/50 text-[var(--warning)]',
    info: 'bg-[var(--info)]/20 border-[var(--info)]/50 text-[var(--info)]'
  };

  const iconColors = {
    success: 'text-[var(--success)]',
    error: 'text-[var(--danger)]',
    warning: 'text-[var(--warning)]',
    info: 'text-[var(--info)]'
  };
</script>

<div class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
  {#each toastList as t (t.id)}
    <div
      class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-sm shadow-lg min-w-[280px] max-w-[400px] toast-slide-in {colors[t.type]}"
      in:fly={{ x: 100, duration: 300 }}
      out:fly={{ x: 100, duration: 200 }}
    >
      <svelte:component this={icons[t.type]} size={20} class={iconColors[t.type]} />
      <span class="flex-1 text-sm text-[var(--text-primary)]">{t.message}</span>
      <button
        class="p-1 rounded hover:bg-white/10 transition-colors text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
        on:click={() => dismissToast(t.id)}
      >
        <X size={14} />
      </button>
    </div>
  {/each}
</div>
