"""Windows Multi-user Manager for SurfManager."""
import os
import subprocess
import getpass
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    import winreg
except ImportError:
    # Fallback for non-Windows systems
    winreg = None

try:
    from app.core.core_utils import debug_print
except ImportError:
    def debug_print(msg):
        print(f"[DEBUG] {msg}")


@dataclass
class WindowsUser:
    """Represents a Windows user account."""
    username: str
    display_name: str
    profile_path: str
    is_active: bool
    is_current: bool
    sid: str
    last_logon: Optional[str] = None


class UserManager:
    """Manages Windows multi-user functionality."""
    
    def __init__(self):
        self.current_user = getpass.getuser()
        self._users_cache = None
        self._selected_user = self.current_user
    
    def get_windows_users(self, refresh_cache: bool = False) -> List[WindowsUser]:
        """Get all Windows user accounts."""
        if self._users_cache is None or refresh_cache:
            self._users_cache = self._detect_users()
        return self._users_cache
    
    def _detect_users(self) -> List[WindowsUser]:
        """Detect Windows user accounts from registry and active sessions."""
        users = []
        current_user = self.current_user.lower()
        
        try:
            # Get users from registry
            registry_users = self._get_registry_users()
            
            # Get active/logged in users
            active_users = self._get_active_users()
            
            # Combine information
            for reg_user in registry_users:
                username = reg_user['username'].lower()
                is_active = username in [u.lower() for u in active_users]
                is_current = username == current_user
                
                user = WindowsUser(
                    username=reg_user['username'],
                    display_name=reg_user.get('display_name', reg_user['username']),
                    profile_path=reg_user['profile_path'],
                    is_active=is_active,
                    is_current=is_current,
                    sid=reg_user['sid'],
                    last_logon=reg_user.get('last_logon')
                )
                users.append(user)
            
            # Sort users: current first, then active, then alphabetical
            users.sort(key=lambda u: (not u.is_current, not u.is_active, u.username.lower()))
            
        except Exception as e:
            debug_print(f"Error detecting users: {e}")
            # Fallback: at least add current user
            users.append(WindowsUser(
                username=self.current_user,
                display_name=self.current_user,
                profile_path=str(Path.home()),
                is_active=True,
                is_current=True,
                sid="",
            ))
        
        return users
    
    def _get_registry_users(self) -> List[Dict]:
        """Get user accounts from Windows registry."""
        users = []
        
        if winreg is None or os.name != 'nt':
            debug_print("Windows registry not available on this system")
            return users
        
        try:
            # Open ProfileList registry key
            profiles_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
            )
            
            i = 0
            while True:
                try:
                    # Enumerate subkeys (SIDs)
                    sid = winreg.EnumKey(profiles_key, i)
                    
                    # Skip system accounts (S-1-5-18, S-1-5-19, S-1-5-20)
                    if sid.startswith('S-1-5-') and not sid.startswith('S-1-5-21-'):
                        i += 1
                        continue
                    
                    # Open user profile key
                    user_key = winreg.OpenKey(profiles_key, sid)
                    
                    try:
                        # Get profile path
                        profile_path = winreg.QueryValueEx(user_key, "ProfileImagePath")[0]
                        
                        # Extract username from profile path
                        username = os.path.basename(profile_path)
                        
                        # Skip system accounts
                        if username.lower() in ['systemprofile', 'localservice', 'networkservice']:
                            i += 1
                            continue
                        
                        # Try to get display name
                        display_name = username
                        try:
                            # Try to get full name from user account
                            result = subprocess.run([
                                'net', 'user', username
                            ], capture_output=True, text=True, timeout=5)
                            
                            if result.returncode == 0:
                                for line in result.stdout.split('\n'):
                                    if 'Full Name' in line:
                                        full_name = line.split('Full Name')[1].strip()
                                        if full_name and full_name != username:
                                            display_name = full_name
                                        break
                        except (OSError, PermissionError):
                            pass  # Cannot access registry for this user
                        
                        users.append({
                            'username': username,
                            'display_name': display_name,
                            'profile_path': profile_path,
                            'sid': sid
                        })
                        
                    except FileNotFoundError:
                        pass
                    finally:
                        winreg.CloseKey(user_key)
                    
                    i += 1
                    
                except OSError:
                    break
                    
            winreg.CloseKey(profiles_key)
            
        except Exception as e:
            debug_print(f"Error reading registry users: {e}")
        
        return users
    
    def _get_active_users(self) -> List[str]:
        """Get currently active/logged in users."""
        active_users = []
        
        try:
            # Use 'query user' command to get active sessions
            result = subprocess.run([
                'query', 'user'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        # Parse query user output
                        parts = line.split()
                        if len(parts) >= 1:
                            username = parts[0].strip()
                            if username and username != 'USERNAME':
                                active_users.append(username)
        except Exception as e:
            debug_print(f"Error getting active users: {e}")
        
        # Fallback: at least include current user
        if self.current_user not in active_users:
            active_users.append(self.current_user)
        
        return active_users
    
    def get_selected_user(self) -> str:
        """Get currently selected user."""
        return self._selected_user
    
    def set_selected_user(self, username: str) -> bool:
        """Set the selected user for operations."""
        users = self.get_windows_users()
        user_names = [u.username.lower() for u in users]
        
        if username.lower() in user_names:
            self._selected_user = username
            debug_print(f"Selected user changed to: {username}")
            return True
        
        return False
    
    def get_user_profile_path(self, username: Optional[str] = None) -> str:
        """Get profile path for specified user (or selected user)."""
        if username is None:
            username = self._selected_user
        
        users = self.get_windows_users()
        for user in users:
            if user.username.lower() == username.lower():
                return user.profile_path
        
        # Fallback to standard Windows path
        return f"C:\\Users\\{username}"
    
    def get_user_app_data_path(self, username: Optional[str] = None, local: bool = False) -> str:
        """Get AppData path for specified user."""
        profile_path = self.get_user_profile_path(username)
        
        if local:
            return os.path.join(profile_path, "AppData", "Local")
        else:
            return os.path.join(profile_path, "AppData", "Roaming")
    
    def can_access_user_profile(self, username: str) -> bool:
        """Check if we can access another user's profile."""
        if username.lower() == self.current_user.lower():
            return True
        
        try:
            profile_path = self.get_user_profile_path(username)
            return os.path.exists(profile_path) and os.access(profile_path, os.R_OK)
        except (OSError, PermissionError):
            return False  # Cannot check user profile accessibility
    
    def get_user_applications_data(self, username: str, app_configs: Dict) -> Dict:
        """Get application data paths for a specific user."""
        user_apps = {}
        profile_path = self.get_user_profile_path(username)
        appdata_roaming = os.path.join(profile_path, "AppData", "Roaming")
        appdata_local = os.path.join(profile_path, "AppData", "Local")
        
        for app_name, app_config in app_configs.items():
            user_app = {
                'display_name': app_config.get('display_name', app_name.title()),
                'installed': False,
                'path': None,
                'exe_path': None
            }
            
            # Check data paths
            for data_path_template in app_config.get('data_paths', []):
                # Replace environment variables with user-specific paths
                data_path = data_path_template.replace('%APPDATA%', appdata_roaming)
                data_path = data_path.replace('%LOCALAPPDATA%', appdata_local)
                
                if os.path.exists(data_path):
                    user_app['installed'] = True
                    user_app['path'] = data_path
                    break
            
            # Check executable paths
            for exe_path_template in app_config.get('exe_paths', []):
                # Replace environment variables
                exe_path = exe_path_template.replace('%APPDATA%', appdata_roaming)
                exe_path = exe_path.replace('%LOCALAPPDATA%', appdata_local)
                
                if os.path.exists(exe_path):
                    user_app['exe_path'] = exe_path
                    break
            
            user_apps[app_name] = user_app
        
        return user_apps
    
    def refresh_users(self):
        """Refresh the users cache."""
        self._users_cache = None
        return self.get_windows_users(refresh_cache=True)
    
    def get_user_info(self, username: str) -> Optional[WindowsUser]:
        """Get detailed information for a specific user."""
        users = self.get_windows_users()
        for user in users:
            if user.username.lower() == username.lower():
                return user
        return None
