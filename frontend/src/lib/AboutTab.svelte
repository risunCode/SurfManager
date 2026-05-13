<script>
  import { onMount } from 'svelte';
  import { Github, Heart, ExternalLink, Star, GitFork } from 'lucide-svelte';
  import { GetPlatformInfo } from './api.js';
  import { APP_VERSION } from './version.js';

  let platform = {};

  onMount(async () => {
    try {
      platform = await GetPlatformInfo();
    } catch (e) {
      console.error(e);
    }
  });

  function openGithub() {
    window.open('https://github.com/risunCode/SurfManager', '_blank');
  }

  function openSponsor() {
    window.open('https://github.com/sponsors/risunCode', '_blank');
  }
</script>

<div class="h-full flex flex-col items-center justify-center animate-fadeIn p-6">
  <div class="flex gap-8 lg:gap-12 max-w-4xl w-full items-center">
    
    <!-- Left: Branding -->
    <div class="flex-1 text-center lg:text-left">
      <h1 class="text-4xl lg:text-5xl font-bold text-[var(--text-primary)] tracking-tight">
        <span class="text-[var(--primary-light)]">SURF</span>MANAGER
      </h1>
      
      <p class="text-[var(--text-muted)] mt-3 text-sm">
        Session & Data Management Tool
      </p>

      <p class="text-[var(--text-secondary)] mt-4 text-sm leading-relaxed max-w-md">
        Advanced session management for VSCode-based editors. 
        Backup, restore, and switch between multiple accounts seamlessly.
      </p>
    </div>

    <!-- Divider -->
    <div class="hidden lg:block w-px h-64 bg-gradient-to-b from-transparent via-[var(--border)] to-transparent"></div>

    <!-- Right: Details -->
    <div class="flex-1">
      <div class="space-y-5">
        <!-- Version -->
        <div>
          <span class="text-[var(--primary-light)] font-bold text-2xl">v{APP_VERSION}</span>
          <span class="text-[var(--text-muted)] text-sm ml-2">Rust + Tauri + Svelte</span>
        </div>

        <!-- Info Grid -->
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-[var(--bg-card)] rounded-lg p-3 border border-[var(--border)]">
            <span class="text-[var(--text-muted)] text-xs block">Author</span>
            <p class="text-[var(--text-primary)] font-semibold">risunCode</p>
          </div>
          <div class="bg-[var(--bg-card)] rounded-lg p-3 border border-[var(--border)]">
            <span class="text-[var(--text-muted)] text-xs block">License</span>
            <p class="text-[var(--text-primary)] font-semibold">MIT</p>
          </div>
          <div class="bg-[var(--bg-card)] rounded-lg p-3 border border-[var(--border)]">
            <span class="text-[var(--text-muted)] text-xs block">Platform</span>
            <p class="text-[var(--text-primary)] font-semibold capitalize">{platform.platform || '...'}</p>
          </div>
          <div class="bg-[var(--bg-card)] rounded-lg p-3 border border-[var(--border)]">
            <span class="text-[var(--text-muted)] text-xs block">Arch</span>
            <p class="text-[var(--text-primary)] font-semibold">{platform.arch || '...'}</p>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-3">
          <button
            class="flex-1 px-4 py-2.5 rounded-lg font-medium bg-[var(--primary)] hover:bg-[var(--primary-light)] hover:text-black text-white transition-all flex items-center justify-center gap-2"
            on:click={openGithub}
          >
            <Github size={18} />
            GitHub
            <ExternalLink size={14} />
          </button>
          <button
            class="flex-1 px-4 py-2.5 rounded-lg font-medium bg-[var(--danger)]/20 hover:bg-[var(--danger)]/30 text-[var(--danger)] border border-[var(--danger)]/30 transition-all flex items-center justify-center gap-2"
            on:click={openSponsor}
          >
            <Heart size={18} />
            Sponsor
          </button>
        </div>

        <!-- Support Message -->
        <div class="p-4 bg-[var(--bg-elevated)] rounded-lg border border-[var(--border)] text-center">
          <p class="text-sm text-[var(--text-secondary)] mb-3">
            If this app helps you, please support by:
          </p>
          <div class="flex gap-3 justify-center">
            <button
              class="px-4 py-2 rounded-lg text-sm font-medium bg-[var(--warning)]/20 hover:bg-[var(--warning)]/30 text-[var(--warning)] border border-[var(--warning)]/30 transition-all flex items-center gap-2"
              on:click={openGithub}
            >
              <Star size={16} />
              Star
            </button>
            <button
              class="px-4 py-2 rounded-lg text-sm font-medium bg-[var(--info)]/20 hover:bg-[var(--info)]/30 text-[var(--info)] border border-[var(--info)]/30 transition-all flex items-center gap-2"
              on:click={openGithub}
            >
              <GitFork size={16} />
              Fork
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Built with love - inside content area -->
  <div class="mt-8 text-center">
    <p class="text-[var(--text-muted)] text-xs">
      Built with <span class="text-[var(--danger)]">❤</span> using Rust, Tauri, and Svelte
    </p>
  </div>
</div>
