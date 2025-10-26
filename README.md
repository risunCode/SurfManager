# SurfManager v2.0.0 - Minimal Build Edition

🚀 **Advanced session and data management tool for (Windsurf, Cursor and Claude App windows)**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/risunCode/SurfManager)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/risunCode/SurfManager)
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/)
[![Size](https://img.shields.io/badge/size-~60--70MB-green.svg)](https://github.com/risunCode/SurfManager)

---

## 📖 Apa itu SurfManager?

**SurfManager** adalah aplikasi manajemen sesi dan data untuk development tools seperti Windsurf, Cursor, VS Code, dan Claude. Aplikasi ini memungkinkan Anda untuk:

- 🔄 **Reset data aplikasi** dengan aman
- 💾 **Backup & restore** sesi/akun berbeda
- 🆔 **Generate device ID baru** untuk reset identitas
- 🗑️ **Cleanup cache** dan file temporary
- 📁 **Quick access** ke folder aplikasi
- 🔊 **Audio feedback** untuk setiap aksi

---

## ✨ Fitur Utama

### 🔄 Reset Data Tab
Kelola data aplikasi development Anda dengan mudah:

- **Detect Installed Apps** - Auto-detect Windsurf, Cursor, Claude, VS Code
- **Reset Application Data** - Hapus data aplikasi dengan backup otomatis
- **Generate New Device ID** - Buat device ID baru untuk reset identitas
- **Cleanup Cache** - Bersihkan __pycache__ dan file temporary
- **Open Folder** - Quick access ke folder data aplikasi
- **Clear Log** - Bersihkan log output
- **Audio Toggle** - Enable/disable sound effects

### 👤 Account Manager Tab
Manajemen multi-sesi untuk berbagai akun:

- **Create Session Backup** - Backup sesi aktif dengan nama custom
- **Restore Session** - Load backup sesi sebelumnya
- **Update Backup** - Update backup dengan data terbaru
- **Session Management** - Rename, delete, set active session
- **Multi-App Support** - Kelola sesi Cursor, Windsurf, dan Claude
- **Search & Filter** - Cari sesi dengan mudah
- **Size Tracking** - Lihat ukuran setiap backup

 
## 🔊 Audio System

SurfManager dilengkapi dengan audio feedback untuk setiap aksi:

### Sound Configuration
Setiap button punya sound sendiri dengan mode **first-then-random**:

- **First Play**: Sound khusus untuk pertama kali
- **Subsequent Plays**: Random sound (exclude startup)

### Supported Actions
- Reset Windsurf/Cursor/Claude
- Clear Data
- Cleanup Cache
- Generate New ID
- Open Folder
- Startup Sound

### Audio Config Location
`app/audio/audio_config.json` - Edit untuk customize sounds

---

## 📦 Instalasi

### Requirements
- **OS**: Windows 10/11
- **Python**: 3.8+ (untuk build dari source)
- **Disk Space**: ~100 MB

### Download Pre-built
1. Download `SurfManager.exe` dari [Releases](https://github.com/risunCode/SurfManager/releases)
2. Jalankan langsung, no installation needed!

### Build dari Source
```cmd
# Clone repository
git clone https://github.com/risunCode/SurfManager.git
cd SurfManager

# Setup virtual environment
setup.bat

# Build executable
python scripts/build_installer.py --type stable
```

---

## 🚀 Cara Pakai

### 1. Reset Data
1. Buka tab **Reset Data**
2. Pilih aplikasi yang ingin direset
3. Klik tombol reset (akan ada konfirmasi backup)
4. Tunggu proses selesai

### 2. Backup Session
1. Buka tab **Account Manager**
2. Klik **Backup Cursor/Windsurf/Claude**
3. Masukkan nama session (misal: "Project-A")
4. Backup akan disimpan di `Documents/SurfManager/`

### 3. Restore Session
1. Buka tab **Account Manager**
2. Right-click pada session yang ingin direstore
3. Pilih **Load Backup**
4. Aplikasi akan otomatis close dan restore data

### 4. Generate New Device ID
1. Buka tab **Reset Data**
2. Klik **Generate New ID**
3. Pilih aplikasi (Windsurf/Cursor)
4. Device ID baru akan digenerate

---

## ⚙️ Configuration

### Config Files
- `app/config/config.json` - Main configuration
- `app/audio/audio_config.json` - Audio settings
- `Documents/SurfManager/sessions.json` - Session data

### Storage Locations
- **Session Backups**: `Documents/SurfManager/`
- **App Data**: System default paths (AppData)

---

## 🏗️ Build System

### Build Options
```cmd
# Stable build (no console, optimized)
python scripts/build_installer.py --type stable

# Debug build (with console)
python scripts/build_installer.py --type debug

# Build both versions
python scripts/build_installer.py --type both

# Clean build directories
python scripts/build_installer.py --clean-only
```

### Build Features
- ✅ Minimal dependencies (4 packages only)
- ✅ Aggressive module exclusion (20+ modules)
- ✅ Binary stripping for smaller size
- ✅ Expected size: ~60-70 MB

---

## 📊 Dependencies

### Core (Minimal)
```txt
PyQt6==6.7.0          # Modern GUI framework
pygame==2.6.1         # Multi-format audio support
psutil==5.9.8         # Process management
pyinstaller==6.3.0    # Build tool
```

### Size Comparison
- **v1.0.0**: ~100 MB
- **v1.5.0**: ~80 MB  
- **v2.0.0**: ~60-70 MB (30-40% reduction!)

---

## 🎨 Customization

### Audio Customization
Edit `app/audio/audio_config.json`:
```json
{
  "audio_enabled": true,
  "sounds": {
    "reset_windsurf": {
      "enabled": true,
      "first_play": "your-sound.mp3",
      "subsequent_play": "random",
      "volume": 0.8
    }
  }
}
```

### Theme
Dark theme by default. Edit `app/gui/styles.py` untuk customize.

---

## 🐛 Troubleshooting

### Audio tidak bunyi?
- Cek `audio_enabled: true` di config
- Pastikan file audio ada di `app/audio/sound/`
- Format supported: MP3, OGG, WAV

### Aplikasi tidak terdeteksi?
- Pastikan aplikasi terinstall di lokasi default
- Check `app/config/config.json` untuk path detection

### Build gagal?
- Jalankan `setup.bat` terlebih dahulu
- Pastikan Python 3.8+ terinstall
- Check dependencies: `pip install -r requirements.txt`

---

## 📝 Tips & Best Practices

### Session Backups
- ✅ Gunakan nama deskriptif (misal: "Project-Client-A")
- ✅ Backup sebelum update major
- ✅ Test restore dengan session non-critical dulu
- ✅ Cleanup backup lama secara berkala

### Performance
- ✅ Close aplikasi sebelum backup/restore
- ✅ Disable audio jika mengganggu
- ✅ Gunakan debug mode hanya untuk troubleshooting

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

---

## 📜 License

Distributed under the MIT License.

---

## 👨‍💻 Author

**risunCode**

- GitHub: [@risunCode](https://github.com/risunCode)

---

## 🙏 Acknowledgments

- PyQt6 for excellent GUI framework
- pygame for audio support
- Community contributors and testers

---

**Made with ❤️ by risunCode**

*Minimal build, maximum functionality*
