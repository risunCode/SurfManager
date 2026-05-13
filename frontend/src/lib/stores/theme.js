// Theme store with localStorage persistence
import { writable } from 'svelte/store';

const STORAGE_KEY = 'surfmanager-theme';
const DEFAULT_THEME = 'dark';

function createThemeStore() {
  // Get stored theme or default
  const stored = typeof localStorage !== 'undefined' 
    ? localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME 
    : DEFAULT_THEME;
  
  const { subscribe, set, update } = writable(stored);

  return {
    subscribe,
    set: (theme) => {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, theme);
      }
      document.documentElement.setAttribute('data-theme', theme);
      set(theme);
    },
    toggle: () => {
      update(current => {
        const themes = ['dark', 'solarized', 'solarized-light'];
        const next = themes[(themes.indexOf(current) + 1) % themes.length];
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem(STORAGE_KEY, next);
        }
        document.documentElement.setAttribute('data-theme', next);
        return next;
      });
    },
    init: () => {
      document.documentElement.setAttribute('data-theme', stored);
    }
  };
}

export const theme = createThemeStore();
