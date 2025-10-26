"""Build script untuk SurfManager menggunakan PyInstaller.

Supports:
- Stable build (no console, windowed)
- Debug build (with console for debugging)
- Standalone executable
"""
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Change to project root directory
PROJECT_ROOT = Path(__file__).parents[1]
os.chdir(PROJECT_ROOT)

# Import version dari app
sys.path.insert(0, str(PROJECT_ROOT))
from app import __version__

APP_VERSION = __version__
APP_NAME = "SurfManager"


class InstallerBuilder:
    """Builder untuk membuat installer SurfManager."""
    
    def __init__(self, build_type='stable'):
        self.project_root = PROJECT_ROOT
        self.build_type = build_type.lower()
        
        # Set output directory based on build type
        self.output_dir = self.project_root / 'output' / self.build_type
            
        self.build_dir = self.project_root / 'build'
        self.dist_dir = self.project_root / 'dist'
        
        # Build configuration
        self.is_debug = self.build_type == 'debug'
        self.exe_name = f'{APP_NAME}_Debug' if self.is_debug else APP_NAME
        
    def clean_build_dirs(self):
        """Clean previous build directories."""
        print("🧹 Membersihkan direktori build...")
        dirs_to_clean = [self.build_dir, self.dist_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  ✓ Cleaned: {dir_path.name}")
        print()
    
    def build_exe(self):
        """Build executable menggunakan PyInstaller."""
        build_mode = 'DEBUG' if self.is_debug else 'STABLE'
        print("=" * 70)
        print(f"  🔨 Building {APP_NAME} v{APP_VERSION} - {build_mode} Mode")
        print("=" * 70)
        print()
        
        # Base PyInstaller options
        pyinstaller_options = [
            'app/main.py',
            f'--name={self.exe_name}',
            '--onefile',
            '--icon=app/icons/surfmanager.ico',
            '--add-data=app/config;app/config',
            '--add-data=app/icons;app/icons',
            '--add-data=app/audio;app/audio',
            '--add-data=README.md;.',
            # Required imports
            '--hidden-import=PyQt6',
            '--hidden-import=PyQt6.QtCore',
            '--hidden-import=PyQt6.QtGui',
            '--hidden-import=PyQt6.QtWidgets',
            '--hidden-import=pygame',
            '--hidden-import=psutil',
            '--clean',
            '--noconfirm',
        ]
        
        # Exclude unnecessary modules for stable build (size optimization)
        if not self.is_debug:
            exclude_modules = [
                # Scientific/data libraries
                'matplotlib',
                'numpy',
                'pandas',
                'scipy',
                'PIL',
                'Pillow',
                # GUI libraries
                'tkinter',
                'wx',
                'gtk',
                # Testing/dev tools
                'unittest',
                'test',
                'pytest',
                'pydoc',
                'doctest',
                # Build tools
                'setuptools',
                'pip',
                'wheel',
                'distutils',
                'pkg_resources',
                # Other heavy modules
                'IPython',
                'jupyter',
                'notebook',
                'sqlite3',  # If not using database
                'xml.etree',  # If not using XML
                'email',  # If not using email
                'http.server',
                'xmlrpc',
            ]
            for module in exclude_modules:
                pyinstaller_options.append(f'--exclude-module={module}')
            
            # Additional size optimizations
            pyinstaller_options.extend([
                '--strip',  # Strip debug symbols
                '--noupx',  # Disable UPX (can cause issues, manual UPX is better)
            ])
            
            print("  📦 Optimizing: Excluding unnecessary modules for smaller size")
            print("  🗜️  Strip: Removing debug symbols")
        
        # Add debug or stable specific options
        if self.is_debug:
            pyinstaller_options.append('--console')  # Show console for debug
            pyinstaller_options.append('--debug=all')
            pyinstaller_options.append('--log-level=DEBUG')  # Verbose logging
            os.environ['SURFMANAGER_BUILD_TYPE'] = 'DEBUG'
            os.environ['SURFMANAGER_SHOW_TERMINAL'] = 'YES'
            print("  🐛 Debug mode: Console window enabled")
            print("  📝 Verbose logging: ENABLED")
        else:
            pyinstaller_options.append('--windowed')  # No console for stable
            pyinstaller_options.append('--log-level=WARN')  # Minimal logging for size
            os.environ['SURFMANAGER_BUILD_TYPE'] = 'STABLE'
            os.environ['SURFMANAGER_SHOW_TERMINAL'] = 'NO'
            print("  🚀 Stable mode: No console window")
            print("  📝 Logging: Minimal (WARN level)")
        
        print("\n📦 Menjalankan PyInstaller...")
        print("=" * 70)
        
        try:
            # Run PyInstaller with real-time output (no capture)
            result = subprocess.run(
                ['pyinstaller'] + pyinstaller_options,
                text=True,
                encoding='utf-8'
            )
            
            print("=" * 70)
            if result.returncode == 0:
                print("\n  ✓ Build executable berhasil!")
                return True
            else:
                print("\n  ✗ Build executable gagal!")
                print(f"  Exit code: {result.returncode}")
                return False
                
        except FileNotFoundError:
            print("  ✗ PyInstaller tidak ditemukan!")
            print("  Install dengan: pip install pyinstaller")
            return False
        except Exception as e:
            print(f"  ✗ Build error: {e}")
            return False
    
    def prepare_installer_files(self):
        """Prepare files untuk installer."""
        print("\n📁 Menyiapkan file...")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy executable
        exe_src = self.dist_dir / f'{self.exe_name}.exe'
        exe_dst = self.output_dir / f'{self.exe_name}.exe'
        
        if exe_src.exists():
            shutil.copy2(exe_src, exe_dst)
            print(f"  ✓ Copied: {self.exe_name}.exe")
            
            # Show file size
            size_mb = exe_dst.stat().st_size / (1024 * 1024)
            print(f"  📏 Size: {size_mb:.2f} MB")
        else:
            print(f"  ✗ Executable tidak ditemukan: {exe_src}")
            return False
        
        # Copy additional files
        files_to_copy = [
            'README.md',
            'CHANGELOG.md',
            'requirements.txt'
        ]
        
        for file_name in files_to_copy:
            src = self.project_root / file_name
            if src.exists():
                shutil.copy2(src, self.output_dir / file_name)
                print(f"  ✓ Copied: {file_name}")
        
        # Show build summary
        self._show_build_summary(exe_dst)
        
        print()
        return True
    
    def _show_build_summary(self, exe_path):
        """Show detailed build summary."""
        print("\n" + "=" * 70)
        print("  📊 BUILD SUMMARY")
        print("=" * 70)
        
        # File info
        size_bytes = exe_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        print(f"\n  📦 Executable: {exe_path.name}")
        print(f"  📏 Size: {size_mb:.2f} MB ({size_bytes:,} bytes)")
        
        # Build info
        build_mode = 'DEBUG' if self.is_debug else 'STABLE'
        print(f"\n  🔧 Build Type: {build_mode}")
        print(f"  📁 Output: {self.output_dir}")
        
        # Packed modules info
        print(f"\n  📚 Included Modules:")
        included_modules = [
            'PyQt6 (GUI Framework)',
            'pygame (Audio)',
            'psutil (Process Management)',
        ]
        for module in included_modules:
            print(f"     • {module}")
        
        if not self.is_debug:
            print(f"\n  🚫 Excluded Modules (for size optimization):")
            excluded = ['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'tkinter', 'unittest', 'sqlite3', 'email']
            for module in excluded:
                print(f"     • {module}")
        
        # Data files
        print(f"\n  📂 Bundled Data:")
        data_items = [
            'app/config (Configuration files)',
            'app/icons (Application icons)',
            'app/audio (Sound effects)',
            'README.md (Documentation)',
        ]
        for item in data_items:
            print(f"     • {item}")
        
        print("=" * 70)
    
    def build_all(self):
        """Build complete package."""
        build_mode = 'DEBUG' if self.is_debug else 'STABLE'
        print("\n" + "=" * 70)
        print(f"  🚀 {APP_NAME} v{APP_VERSION} - Build System")
        print(f"  Mode: {build_mode}")
        print(f"  Target: Standalone Executable")
        print("=" * 70)
        print()
        
        # Step 1: Clean
        self.clean_build_dirs()
        
        # Step 2: Build EXE
        if not self.build_exe():
            print("\n❌ Build executable gagal!")
            return False
        
        # Step 3: Prepare files
        if not self.prepare_installer_files():
            print("\n❌ Gagal menyiapkan file!")
            return False
        
        print("\n" + "=" * 70)
        print("  ✅ BUILD SELESAI!")
        print("=" * 70)
        print(f"\n  📁 Output: {self.output_dir}")
        print(f"  📦 File: {self.exe_name}.exe")
        print()
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='SurfManager Build System - Build executable',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build stable executable (default)
  python scripts/build_installer.py
  
  # Build debug executable with console
  python scripts/build_installer.py --type debug
  
  # Build both stable and debug
  python scripts/build_installer.py --type both
        """
    )
    
    parser.add_argument(
        '--type',
        choices=['stable', 'debug', 'both'],
        default='stable',
        help='Build type: stable (no console), debug (with console), or both'
    )
    
    parser.add_argument(
        '--clean-only',
        action='store_true',
        help='Only clean build directories without building'
    )
    
    args = parser.parse_args()
    
    try:
        # Clean only mode
        if args.clean_only:
            print("🧹 Cleaning build directories...")
            builder = InstallerBuilder()
            builder.clean_build_dirs()
            print("✅ Clean completed!")
            sys.exit(0)
        
        # Build both stable and debug
        if args.type == 'both':
            print("\n" + "=" * 70)
            print("  Building BOTH Stable and Debug versions")
            print("=" * 70)
            
            # Build stable
            print("\n[1/2] Building STABLE version...")
            builder_stable = InstallerBuilder(build_type='stable')
            success_stable = builder_stable.build_all()
            
            # Build debug
            print("\n[2/2] Building DEBUG version...")
            builder_debug = InstallerBuilder(build_type='debug')
            success_debug = builder_debug.build_all()
            
            # Summary
            print("\n" + "=" * 70)
            print("  📊 BUILD SUMMARY")
            print("=" * 70)
            print(f"  Stable: {'✅ Success' if success_stable else '❌ Failed'}")
            print(f"  Debug:  {'✅ Success' if success_debug else '❌ Failed'}")
            print()
            
            sys.exit(0 if (success_stable and success_debug) else 1)
        
        # Build single type
        else:
            builder = InstallerBuilder(build_type=args.type)
            success = builder.build_all()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Build dibatalkan oleh user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
