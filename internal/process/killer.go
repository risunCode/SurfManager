// Package process provides process management utilities including
// graceful termination, force kill, and smart close with retry logic.
package process

import (
	"errors"
	"fmt"
	"os"
	"runtime"
	"strings"
	"sync"
	"time"

	"github.com/shirou/gopsutil/v3/process"
)

// Default timeouts and retry settings
const (
	DefaultGracefulTimeout = 3 * time.Second
	DefaultForceTimeout    = 2 * time.Second
	DefaultFileReleaseWait = 1 * time.Second
	DefaultMaxRetries      = 2
	DefaultRetryDelay      = 750 * time.Millisecond
	CacheDuration          = 2 * time.Second
)

// ProcessInfo holds information about a running process
type ProcessInfo struct {
	PID     int32
	Name    string
	Process *process.Process
}

// Killer handles process termination with graceful shutdown and force kill capabilities
type Killer struct {
	logFunc      func(string)
	cache        map[string][]ProcessInfo
	cacheExpiry  time.Time
	cacheMutex   sync.RWMutex
}

// NewKiller creates a new Killer instance with optional log callback
func NewKiller(logFunc func(string)) *Killer {
	if logFunc == nil {
		logFunc = func(msg string) {
			fmt.Println(msg)
		}
	}
	return &Killer{
		logFunc: logFunc,
		cache:   make(map[string][]ProcessInfo),
	}
}

// log writes a message using the configured log function
func (k *Killer) log(format string, args ...interface{}) {
	k.logFunc(fmt.Sprintf(format, args...))
}

// getCacheKey generates a cache key from process names
func getCacheKey(processNames []string) string {
	sorted := make([]string, len(processNames))
	copy(sorted, processNames)
	// Simple sort for cache key consistency
	for i := 0; i < len(sorted)-1; i++ {
		for j := i + 1; j < len(sorted); j++ {
			if sorted[i] > sorted[j] {
				sorted[i], sorted[j] = sorted[j], sorted[i]
			}
		}
	}
	return strings.Join(sorted, "|")
}

// GetRunningProcesses returns all running processes matching the given names
func (k *Killer) GetRunningProcesses(processNames []string) ([]ProcessInfo, error) {
	cacheKey := getCacheKey(processNames)
	now := time.Now()

	// Check cache first
	k.cacheMutex.RLock()
	if now.Before(k.cacheExpiry) {
		if cached, ok := k.cache[cacheKey]; ok {
			// Validate cached processes are still running
			valid := make([]ProcessInfo, 0, len(cached))
			for _, p := range cached {
				running, err := p.Process.IsRunning()
				if err == nil && running {
					valid = append(valid, p)
				}
			}
			if len(valid) > 0 {
				k.cacheMutex.RUnlock()
				return valid, nil
			}
		}
	}
	k.cacheMutex.RUnlock()

	// Get fresh process list
	running := make([]ProcessInfo, 0)
	procs, err := process.Processes()
	if err != nil {
		return nil, fmt.Errorf("failed to get process list: %w", err)
	}

	for _, proc := range procs {
		name, err := proc.Name()
		if err != nil {
			continue
		}

		// Check if process name matches any target
		nameLower := strings.ToLower(name)
		for _, target := range processNames {
			if strings.Contains(nameLower, strings.ToLower(target)) {
				running = append(running, ProcessInfo{
					PID:     proc.Pid,
					Name:    name,
					Process: proc,
				})
				break
			}
		}
	}

	// Update cache
	if len(running) > 0 {
		k.cacheMutex.Lock()
		k.cache[cacheKey] = running
		k.cacheExpiry = now.Add(CacheDuration)
		k.cacheMutex.Unlock()
	}

	return running, nil
}

// IsRunning checks if any process matching the given names is currently running
func (k *Killer) IsRunning(processNames []string) bool {
	procs, err := k.GetRunningProcesses(processNames)
	if err != nil {
		k.log("[ERROR] Failed to check running processes: %v", err)
		return false
	}
	return len(procs) > 0
}

// KillProcess terminates a process by PID with graceful shutdown first, then force kill
func (k *Killer) KillProcess(pid int) error {
	proc, err := process.NewProcess(int32(pid))
	if err != nil {
		return fmt.Errorf("process not found: %w", err)
	}

	name, _ := proc.Name()
	if name == "" {
		name = fmt.Sprintf("PID %d", pid)
	}

	return k.killProcessInternal(ProcessInfo{
		PID:     int32(pid),
		Name:    name,
		Process: proc,
	}, DefaultGracefulTimeout)
}

// killProcessInternal handles the actual process termination logic
func (k *Killer) killProcessInternal(procInfo ProcessInfo, timeout time.Duration) error {
	proc := procInfo.Process
	pid := procInfo.PID
	name := procInfo.Name

	// Check if already terminated
	running, err := proc.IsRunning()
	if err != nil || !running {
		k.log("[OK] %s (PID %d) already terminated", name, pid)
		return nil
	}

	// Graceful terminate
	k.log("[KILL] Terminating %s (PID %d)...", name, pid)
	if err := k.terminateProcess(proc); err != nil {
		k.log("[WARNING] Graceful terminate failed: %v", err)
	}

	// Wait for graceful termination
	terminated := k.waitForExit(proc, timeout)
	if terminated {
		k.log("[OK] %s terminated gracefully", name)
		return nil
	}

	// Force kill
	k.log("[FORCE] Force killing %s (PID %d)...", name, pid)
	if err := k.forceKillProcess(proc); err != nil {
		return fmt.Errorf("force kill failed: %w", err)
	}

	// Wait for force kill
	if k.waitForExit(proc, DefaultForceTimeout) {
		k.log("[OK] %s force killed", name)
		return nil
	}

	return fmt.Errorf("failed to kill %s (PID %d)", name, pid)
}

// terminateProcess sends a graceful termination signal
func (k *Killer) terminateProcess(proc *process.Process) error {
	if runtime.GOOS == "windows" {
		// On Windows, use Terminate which sends WM_CLOSE
		return proc.Terminate()
	}
	// On Unix, send SIGTERM
	return proc.Terminate()
}

// forceKillProcess forcefully kills a process
func (k *Killer) forceKillProcess(proc *process.Process) error {
	if runtime.GOOS == "windows" {
		// On Windows, use Kill which calls TerminateProcess
		return proc.Kill()
	}
	// On Unix, send SIGKILL
	return proc.Kill()
}

// waitForExit waits for a process to exit within the given timeout
func (k *Killer) waitForExit(proc *process.Process, timeout time.Duration) bool {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		running, err := proc.IsRunning()
		if err != nil || !running {
			return true
		}
		time.Sleep(100 * time.Millisecond)
	}
	return false
}

// KillAll terminates all processes matching the given names
// Returns the number of processes killed and any error encountered
func (k *Killer) KillAll(processNames []string) (killed int, err error) {
	running, err := k.GetRunningProcesses(processNames)
	if err != nil {
		return 0, fmt.Errorf("failed to get running processes: %w", err)
	}

	if len(running) == 0 {
		return 0, nil
	}

	k.log("[KILL] Found %d process(es) to kill", len(running))

	var killErrors []string
	for _, proc := range running {
		if err := k.killProcessInternal(proc, DefaultGracefulTimeout); err != nil {
			killErrors = append(killErrors, fmt.Sprintf("%s: %v", proc.Name, err))
		} else {
			killed++
		}
	}

	// Double check for remaining processes
	time.Sleep(500 * time.Millisecond)
	remaining, _ := k.GetRunningProcesses(processNames)

	if len(remaining) > 0 {
		k.log("[RETRY] %d still running, force killing...", len(remaining))
		for _, proc := range remaining {
			if err := k.forceKillProcess(proc.Process); err == nil {
				if k.waitForExit(proc.Process, DefaultForceTimeout) {
					killed++
				}
			}
		}

		// Final check
		time.Sleep(500 * time.Millisecond)
		final, _ := k.GetRunningProcesses(processNames)
		if len(final) > 0 {
			return killed, fmt.Errorf("failed to kill %d process(es)", len(final))
		}
	}

	if len(killErrors) > 0 {
		return killed, errors.New(strings.Join(killErrors, "; "))
	}

	return killed, nil
}

// SmartClose intelligently closes an application with retry logic
// It attempts graceful termination first, then force kill, with configurable retries
func (k *Killer) SmartClose(appName string, processNames []string) error {
	return k.SmartCloseWithOptions(appName, processNames, DefaultGracefulTimeout, DefaultMaxRetries)
}

// SmartCloseWithOptions provides full control over the smart close behavior
func (k *Killer) SmartCloseWithOptions(appName string, processNames []string, timeout time.Duration, maxRetries int) error {
	k.log("[SMART CLOSE] %s", appName)

	for attempt := 1; attempt <= maxRetries; attempt++ {
		// Check if already not running
		if !k.IsRunning(processNames) {
			k.log("[OK] %s is not running", appName)
			// Wait for file handles to be released
			k.waitForFileHandles()
			return nil
		}

		k.log("[ATTEMPT] %d/%d", attempt, maxRetries)

		killed, err := k.KillAll(processNames)
		if err == nil && killed >= 0 {
			k.log("[OK] %s closed - waiting for file release...", appName)
			// Wait for file handles to be released
			k.waitForFileHandles()
			return nil
		}

		if attempt < maxRetries {
			k.log("[RETRY] Waiting...")
			time.Sleep(DefaultRetryDelay)
		}
	}

	// Final check
	remaining, _ := k.GetRunningProcesses(processNames)
	if len(remaining) > 0 {
		return fmt.Errorf("failed to close %s after %d attempts", appName, maxRetries)
	}

	// Wait for file release even if no processes found
	k.waitForFileHandles()
	return nil
}

// waitForFileHandles waits for file handles to be released after process termination
func (k *Killer) waitForFileHandles() {
	time.Sleep(DefaultFileReleaseWait)
}

// WaitForExit waits for all matching processes to exit within the given timeout
func (k *Killer) WaitForExit(processNames []string, timeout time.Duration) bool {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if !k.IsRunning(processNames) {
			return true
		}
		time.Sleep(500 * time.Millisecond)
	}
	return false
}

// ClearCache clears the process cache
func (k *Killer) ClearCache() {
	k.cacheMutex.Lock()
	defer k.cacheMutex.Unlock()
	k.cache = make(map[string][]ProcessInfo)
	k.cacheExpiry = time.Time{}
}

// KillByName is a convenience function to kill a process by its executable name
func (k *Killer) KillByName(processName string) error {
	procs, err := k.GetRunningProcesses([]string{processName})
	if err != nil {
		return err
	}

	if len(procs) == 0 {
		return nil
	}

	var lastErr error
	for _, proc := range procs {
		if err := k.killProcessInternal(proc, DefaultGracefulTimeout); err != nil {
			lastErr = err
		}
	}
	return lastErr
}

// FindProcessByPID returns process info for a given PID
func (k *Killer) FindProcessByPID(pid int) (*ProcessInfo, error) {
	proc, err := process.NewProcess(int32(pid))
	if err != nil {
		return nil, fmt.Errorf("process not found: %w", err)
	}

	name, err := proc.Name()
	if err != nil {
		name = fmt.Sprintf("PID %d", pid)
	}

	return &ProcessInfo{
		PID:     int32(pid),
		Name:    name,
		Process: proc,
	}, nil
}

// IsProcessRunning checks if a specific PID is still running
func (k *Killer) IsProcessRunning(pid int) bool {
	proc, err := process.NewProcess(int32(pid))
	if err != nil {
		return false
	}
	running, err := proc.IsRunning()
	return err == nil && running
}

// GetPIDsByName returns all PIDs for processes matching the given name
func (k *Killer) GetPIDsByName(processName string) ([]int, error) {
	procs, err := k.GetRunningProcesses([]string{processName})
	if err != nil {
		return nil, err
	}

	pids := make([]int, len(procs))
	for i, p := range procs {
		pids[i] = int(p.PID)
	}
	return pids, nil
}

// TerminateWithSignal sends a specific signal to a process (Unix only)
// On Windows, this falls back to regular termination
func (k *Killer) TerminateWithSignal(pid int, sig os.Signal) error {
	proc, err := os.FindProcess(pid)
	if err != nil {
		return fmt.Errorf("process not found: %w", err)
	}
	return proc.Signal(sig)
}
