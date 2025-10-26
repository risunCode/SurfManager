"""Audio Manager for MinimalSurfGUI - handles audio playback configuration."""
import os
import json
import threading
import random
from .debug_utils import debug_print

class AudioManager:
    """Manages audio playback for the application."""
    
    def __init__(self):
        """Initialize audio manager."""
        # Determine paths
        base_path = os.path.dirname(os.path.dirname(__file__))
        self.config_path = os.path.join(base_path, 'audio', 'audio_config.json')
        self.audio_directory = os.path.join(base_path, 'audio', 'sound')
        
        self.audio_config = self.load_config()
        self.current_sound = None
        self.sound_start_time = None
        self.initialized = False
        
        # Track first play for each action
        self._action_play_count = {}
        
        # Initialize pygame in a separate thread to avoid blocking UI
        self._init_thread = threading.Thread(target=self._initialize_pygame)
        self._init_thread.daemon = True
        self._init_thread.start()
    
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
    
    def _initialize_pygame(self):
        """Initialize pygame mixer for audio playback."""
        try:
            debug_print("[AudioManager] Initializing pygame mixer...")
            import pygame
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            debug_print("[AudioManager] Pygame mixer initialized")
            self.initialized = True
        except Exception as e:
            debug_print(f"[AudioManager] Failed to initialize pygame mixer: {e}")
            self.initialized = False
    
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
        """Get full path to a sound file."""
        sound_config = self.get_sound_config(sound_name)
        filename = sound_config.get('filename')
        
        if filename:
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
        
        sound_config = self.get_sound_config(sound_name)
        volume = sound_config.get('volume', 1.0)
        
        return self.play_audio_file(sound_path, volume, blocking)
    
    def play_random_sound(self, exclude_sounds=None, blocking=False):
        """Play a random sound from available audio files, excluding specified sounds."""
        if not self.is_audio_enabled():
            return False
        
        if exclude_sounds is None:
            exclude_sounds = ['startup']  # Default exclude startup
        
        # Get all audio files from directory
        if not os.path.exists(self.audio_directory):
            return False
        
        audio_extensions = ('.mp3', '.ogg', '.wav', '.flac', '.m4a')
        audio_files = []
        
        for file in os.listdir(self.audio_directory):
            if file.lower().endswith(audio_extensions):
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
        return self.play_audio_file(random_path, 0.8, blocking)  # Default volume 0.8 for random sounds
    
    
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
        
        volume = action_config.get('volume', 0.8)
        
        # Initialize play count for this action
        if action_name not in self._action_play_count:
            self._action_play_count[action_name] = 0
        
        # First time play
        if self._action_play_count[action_name] == 0:
            first_play_file = action_config.get('first_play')
            
            if first_play_file:
                sound_path = os.path.join(self.audio_directory, first_play_file)
                if os.path.exists(sound_path):
                    debug_print(f"[AudioManager] Playing first {action_name} sound: {first_play_file}")
                    self._action_play_count[action_name] += 1
                    return self.play_audio_file(sound_path, volume, blocking)
        
        # Subsequent plays - random mode
        subsequent_mode = action_config.get('subsequent_play')
        if subsequent_mode == 'random':
            exclude_list = action_config.get('exclude', ['startup.ogg'])
            debug_print(f"[AudioManager] Playing random {action_name} sound (excluding: {exclude_list})")
            self._action_play_count[action_name] += 1
            return self.play_random_sound(exclude_list, blocking)
        
        return False
    
    def play_audio_file(self, audio_path, volume=1.0, blocking=False):
        """Play an audio file using pygame."""
        try:
            import pygame
            import time
            
            # Wait for initialization if needed (max 2 seconds)
            wait_count = 0
            while not self.initialized and wait_count < 20:
                time.sleep(0.1)
                wait_count += 1
            
            if not pygame.mixer.get_init():
                debug_print("[AudioManager] Mixer not initialized, skipping sound")
                return False
            
            debug_print(f"[AudioManager] Playing audio: {audio_path}")
            
            # Load and play sound
            sound = pygame.mixer.Sound(audio_path)
            sound.set_volume(volume)
            
            # Track current sound and start time
            self.current_sound = sound
            self.sound_start_time = time.time()
            
            if blocking:
                channel = sound.play()
                if channel is None:
                    raise Exception("Failed to get audio channel")
                # Wait for sound to finish
                while pygame.mixer.get_busy():
                    pygame.time.wait(100)
                # Clear tracking when done
                self.current_sound = None
                self.sound_start_time = None
            else:
                channel = sound.play()
                if channel is None:
                    raise Exception("Failed to get audio channel")
            
            debug_print(f"[AudioManager] Audio playback successful")
            return True
        except Exception as e:
            debug_print(f"[AudioManager] Error playing audio: {e}")
            return False
    
    def is_audio_playing(self):
        """Check if audio is currently playing."""
        try:
            import pygame
            if pygame.mixer.get_init() and pygame.mixer.get_busy():
                return True
        except:
            pass
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
