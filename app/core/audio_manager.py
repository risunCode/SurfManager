"""Audio Manager for SurfManager - Native Windows audio using winsound."""
import os
import sys
import json
import random
from .core_utils import debug_print

# Windows-only audio support
if sys.platform == 'win32':
    import winsound
else:
    winsound = None


class AudioManager:
    """Manages audio playback using native Windows winsound (WAV only)."""
    
    def __init__(self):
        """Initialize audio manager."""
        # Determine paths
        base_path = os.path.dirname(os.path.dirname(__file__))
        self.config_path = os.path.join(base_path, 'audio', 'audio_config.json')
        self.audio_directory = os.path.join(base_path, 'audio', 'sound')
        
        self.audio_config = self.load_config()
        self.initialized = (winsound is not None)
        
        # Track first play for each action
        self._action_play_count = {}
        
        if self.initialized:
            debug_print("[AudioManager] Initialized with winsound (native Windows)")
        else:
            debug_print("[AudioManager] winsound not available (non-Windows platform)")
    
    def load_config(self):
        """Load audio configuration from JSON."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    debug_print(f"[AudioManager] Loaded config from: {self.config_path}")
                    return config
        except Exception as e:
            debug_print(f"[AudioManager] Failed to load audio config: {e}")
        
        # Return default config if file doesn't exist
        return {
            'audio_enabled': True,
            'audio_directory': 'audio/sound',
            'random_sounds_enabled': True,
            'sounds': {
                'startup': {
                    'enabled': True,
                    'filename': 'startup.ogg',
                    'description': 'Plays when application starts',
                    'volume': 1.0
                }
            }
        }
    
    
    def is_audio_enabled(self):
        """Check if audio is enabled globally."""
        return self.audio_config.get('audio_enabled', True)
    
    def get_sound_config(self, sound_name):
        """Get configuration for a specific sound."""
        sounds = self.audio_config.get('sounds', {})
        return sounds.get(sound_name, {})
    
    def is_sound_enabled(self, sound_name):
        """Check if a specific sound is enabled."""
        if not self.is_audio_enabled():
            return False
        
        sound_config = self.get_sound_config(sound_name)
        return sound_config.get('enabled', False)
    
    def get_sound_path(self, sound_name):
        """Get full path to a sound file (WAV only)."""
        sound_config = self.get_sound_config(sound_name)
        filename = sound_config.get('filename')
        
        if filename:
            # Convert .mp3/.ogg to .wav extension
            filename = os.path.splitext(filename)[0] + '.wav'
            sound_path = os.path.join(self.audio_directory, filename)
            
            if os.path.exists(sound_path):
                return sound_path
            else:
                debug_print(f"[AudioManager] Sound file not found: {sound_path}")
        
        return None
    
    def play_sound(self, sound_name, blocking=False):
        """Play a sound by name."""
        if not self.is_sound_enabled(sound_name):
            return False
        
        sound_path = self.get_sound_path(sound_name)
        if not sound_path:
            debug_print(f"[AudioManager] Sound file not found: {sound_name}")
            return False
        
        # Note: winsound doesn't support volume control
        return self.play_audio_file(sound_path, blocking=blocking)
    
    def play_random_sound(self, exclude_sounds=None, blocking=False):
        """Play a random sound from available WAV files, excluding specified sounds."""
        if not self.is_audio_enabled():
            return False
        
        if exclude_sounds is None:
            exclude_sounds = ['startup']  # Default exclude startup
        
        # Get all WAV files from directory
        if not os.path.exists(self.audio_directory):
            return False
        
        audio_files = []
        for file in os.listdir(self.audio_directory):
            if file.lower().endswith('.wav'):
                # Check if file should be excluded
                file_base = os.path.splitext(file)[0].lower()
                if not any(exclude in file_base for exclude in exclude_sounds):
                    audio_files.append(file)
        
        if not audio_files:
            debug_print(f"[AudioManager] No random audio files found (excluding: {exclude_sounds})")
            return False
        
        # Pick random file
        random_file = random.choice(audio_files)
        random_path = os.path.join(self.audio_directory, random_file)
        
        debug_print(f"[AudioManager] Playing random sound: {random_file}")
        return self.play_audio_file(random_path, blocking=blocking)
    
    
    def play_action_sound(self, action_name, blocking=False):
        """Play action sound - first time specific, then random.
        
        Args:
            action_name: Name of the action (e.g., 'reset_windsurf', 'cleanup', etc.)
            blocking: Whether to block until sound finishes
        
        First play: Uses configured first_play sound
        Subsequent plays: Random sound excluding specified files
        """
        if not self.is_audio_enabled():
            return False
        
        action_config = self.get_sound_config(action_name)
        if not action_config or not action_config.get('enabled', False):
            return False
        
        # Initialize play count for this action
        if action_name not in self._action_play_count:
            self._action_play_count[action_name] = 0
        
        # First time play
        if self._action_play_count[action_name] == 0:
            first_play_file = action_config.get('first_play')
            
            if first_play_file:
                # Convert to .wav
                first_play_file = os.path.splitext(first_play_file)[0] + '.wav'
                sound_path = os.path.join(self.audio_directory, first_play_file)
                
                if os.path.exists(sound_path):
                    debug_print(f"[AudioManager] Playing first {action_name} sound: {first_play_file}")
                    self._action_play_count[action_name] += 1
                    return self.play_audio_file(sound_path, blocking=blocking)
        
        # Subsequent plays - random mode
        subsequent_mode = action_config.get('subsequent_play')
        if subsequent_mode == 'random':
            exclude_list = action_config.get('exclude', ['startup'])
            debug_print(f"[AudioManager] Playing random {action_name} sound (excluding: {exclude_list})")
            self._action_play_count[action_name] += 1
            return self.play_random_sound(exclude_list, blocking)
        
        return False
    
    def play_audio_file(self, audio_path, blocking=False):
        """Play a WAV audio file using native Windows winsound.
        
        Args:
            audio_path: Path to WAV file
            blocking: If True, wait for sound to finish (SND_SYNC), else async (SND_ASYNC)
        """
        if not self.initialized:
            debug_print("[AudioManager] winsound not available")
            return False
        
        if not os.path.exists(audio_path):
            debug_print(f"[AudioManager] Audio file not found: {audio_path}")
            return False
        
        try:
            debug_print(f"[AudioManager] Playing audio: {audio_path}")
            
            # Play sound with winsound
            flags = winsound.SND_FILENAME
            if blocking:
                flags |= winsound.SND_SYNC  # Wait for sound to finish
            else:
                flags |= winsound.SND_ASYNC  # Play asynchronously
            
            winsound.PlaySound(audio_path, flags)
            debug_print(f"[AudioManager] Audio playback successful")
            return True
            
        except Exception as e:
            debug_print(f"[AudioManager] Error playing audio: {e}")
            return False
    
    def is_audio_playing(self):
        """Check if audio is currently playing.
        
        Note: winsound doesn't provide a way to check playback status.
        Always returns False for async sounds.
        """
        return False
    
    def save_config(self):
        """Save current audio configuration to JSON."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.audio_config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            debug_print(f"[AudioManager] Failed to save audio config: {e}")
            return False
    
    def toggle_audio_enabled(self):
        """Toggle audio enabled state and save configuration."""
        current_state = self.audio_config.get('audio_enabled', True)
        self.audio_config['audio_enabled'] = not current_state
        self.save_config()
        return self.audio_config['audio_enabled']
