"""Smart process killer with realtime detection."""
import time
from typing import Dict, List, Tuple, Optional, Callable

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class ProcessKiller:
    """Smart process killer with realtime detection and advanced termination."""
    
    def __init__(self, log_callback: Optional[Callable] = None):
        """Initialize ProcessKiller.
        
        Args:
            log_callback: Optional callback for logging messages
        """
        self._log_callback = log_callback or print
        self._process_cache = {}
        self._cache_expiry = 0
        self._cache_duration = 2.0
    
    def _log(self, message: str):
        """Log message."""
        if self._log_callback:
            self._log_callback(message)
    
    def get_running_processes(self, process_names: List[str]) -> List[Dict]:
        """Get ALL running processes matching names.
        
        Args:
            process_names: List of process executable names to search for
        
        Returns:
            List of process info dictionaries with pid, name, process_obj
        """
        if not PSUTIL_AVAILABLE:
            self._log("[WARNING] psutil not available - skipping process check")
            return []
        
        current_time = time.time()
        cache_key = tuple(sorted(process_names))
        
        # Check cache first
        if current_time < self._cache_expiry and cache_key in self._process_cache:
            cached = self._process_cache[cache_key]
            valid = []
            for p in cached:
                try:
                    if p['process_obj'].is_running():
                        valid.append(p)
                except:
                    pass
            if valid:
                return valid
        
        running = []
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name']
                    if any(target.lower() in proc_name.lower() for target in process_names):
                        running.append({
                            'pid': proc.info['pid'],
                            'name': proc_name,
                            'process_obj': proc
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            self._log(f"[ERROR] Failed to get processes: {e}")
        
        if running:
            self._process_cache[cache_key] = running
            self._cache_expiry = current_time + self._cache_duration
        
        return running
    
    def is_running(self, process_names: List[str]) -> bool:
        """Check if any matching process is running."""
        return len(self.get_running_processes(process_names)) > 0
    
    def kill_process(self, proc_info: Dict, timeout: int = 5) -> bool:
        """Kill a process gracefully first, then forcefully.
        
        Args:
            proc_info: Process info dict with 'process_obj', 'pid', 'name'
            timeout: Timeout for graceful termination
        
        Returns:
            True if killed successfully
        """
        if not PSUTIL_AVAILABLE:
            return False
            
        proc = proc_info['process_obj']
        pid = proc_info['pid']
        name = proc_info['name']
        
        try:
            if not proc.is_running():
                self._log(f"[OK] {name} (PID {pid}) already terminated")
                return True
            
            # Graceful terminate
            self._log(f"[KILL] Terminating {name} (PID {pid})...")
            proc.terminate()
            
            try:
                proc.wait(timeout=timeout)
                self._log(f"[OK] {name} terminated gracefully")
                return True
            except psutil.TimeoutExpired:
                # Force kill
                self._log(f"[FORCE] Force killing {name} (PID {pid})...")
                proc.kill()
                try:
                    proc.wait(timeout=2)
                    self._log(f"[OK] {name} force killed")
                    return True
                except psutil.TimeoutExpired:
                    self._log(f"[ERROR] Failed to kill {name}")
                    return False
                    
        except psutil.NoSuchProcess:
            self._log(f"[OK] {name} no longer exists")
            return True
        except psutil.AccessDenied:
            self._log(f"[ERROR] Access denied: {name}")
            return False
        except Exception as e:
            self._log(f"[ERROR] {name}: {e}")
            return False
    
    def kill_all(self, process_names: List[str], timeout: int = 5) -> Tuple[bool, str]:
        """Kill ALL matching processes.
        
        Args:
            process_names: List of process names to kill
            timeout: Timeout per process
        
        Returns:
            Tuple of (success, message)
        """
        running = self.get_running_processes(process_names)
        
        if not running:
            return True, "No processes running"
        
        self._log(f"[KILL] Found {len(running)} process(es) to kill")
        
        killed = 0
        for proc in running:
            if self.kill_process(proc, timeout):
                killed += 1
        
        # Double check
        time.sleep(0.5)
        remaining = self.get_running_processes(process_names)
        
        if remaining:
            # Force kill remaining
            self._log(f"[RETRY] {len(remaining)} still running, force killing...")
            for proc in remaining:
                try:
                    proc['process_obj'].kill()
                    proc['process_obj'].wait(timeout=2)
                    killed += 1
                except:
                    pass
            
            time.sleep(0.5)
            final = self.get_running_processes(process_names)
            if final:
                return False, f"Failed to kill {len(final)} process(es)"
        
        return True, f"Killed {killed} process(es)"
    
    def smart_close(self, app_name: str, process_names: List[str], 
                    timeout: int = 10, max_retries: int = 3) -> Tuple[bool, str]:
        """Smart app closer - main method for closing apps before operations.
        
        Args:
            app_name: Display name of the application
            process_names: List of process names to kill
            timeout: Timeout per process
            max_retries: Maximum retry attempts
        
        Returns:
            Tuple of (success, message)
        """
        if not PSUTIL_AVAILABLE:
            self._log(f"[WARNING] psutil not available - skipping close")
            return True, "psutil not available"
        
        self._log(f"[SMART CLOSE] {app_name}")
        
        for attempt in range(1, max_retries + 1):
            if not self.is_running(process_names):
                self._log(f"[OK] {app_name} is not running")
                # Wait extra time for file handles to be released
                time.sleep(2)
                return True, f"{app_name} is not running"
            
            self._log(f"[ATTEMPT] {attempt}/{max_retries}")
            
            success, message = self.kill_all(process_names, timeout)
            
            if success:
                self._log(f"[OK] {app_name} closed - waiting for file release...")
                # Wait longer for file handles to be released
                time.sleep(3)
                return True, f"{app_name} closed"
            
            if attempt < max_retries:
                self._log(f"[RETRY] Waiting...")
                time.sleep(2)
        
        # Failed
        remaining = self.get_running_processes(process_names)
        if remaining:
            msg = f"Failed to close {app_name} after {max_retries} attempts"
            self._log(f"[ERROR] {msg}")
            return False, msg
        
        # Wait extra for file release even if no processes found
        time.sleep(3)
        return True, f"{app_name} closed after retries"
    
    def wait_for_exit(self, process_names: List[str], timeout: int = 30) -> bool:
        """Wait for processes to exit.
        
        Args:
            process_names: List of process names to monitor
            timeout: Maximum time to wait (seconds)
        
        Returns:
            True if all exited, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            if not self.is_running(process_names):
                return True
            time.sleep(0.5)
        return False
