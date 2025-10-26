# Audio Configuration

This folder contains audio configuration for MinimalSurfGUI sound effects.

## Configuration

Edit `audio_config.json` to customize sound effects:

```json
{
    "audio_enabled": true,
    "volume": 0.5,
    "sounds": {
        "startup": {
            "frequency": 880,
            "duration": 0.3,
            "type": "beep"
        },
        "success": {
            "frequency": 1000,
            "duration": 0.15,
            "type": "beep"
        }
    }
}
```

### Parameters

- **audio_enabled**: Enable/disable all audio (true/false)
- **volume**: Master volume (0.0 to 1.0)
- **frequency**: Tone frequency in Hz (higher = higher pitch)
- **duration**: Sound duration in seconds
- **type**: Currently only "beep" is supported

### Adding Custom Sounds

You can add more sound effects by adding entries to the "sounds" object:

```json
"my_custom_sound": {
    "frequency": 750,
    "duration": 0.25,
    "type": "beep"
}
```

Then call it in code:
```python
self.audio_manager.play_sound('my_custom_sound')
```
