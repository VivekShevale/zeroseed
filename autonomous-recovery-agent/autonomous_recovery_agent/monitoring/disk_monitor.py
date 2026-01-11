"""
Disk monitoring and automatic cleanup
"""
import os
import shutil
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta


class DiskMonitor:
    """Monitor disk usage and perform automatic cleanup"""
    
    def __init__(
        self,
        log_dirs: List[str] = None,
        temp_dirs: List[str] = None,
        cleanup_threshold: float = 0.85,  # 85% disk usage
        critical_threshold: float = 0.95,  # 95% disk usage
        max_log_age_days: int = 30,
        max_temp_age_hours: int = 24,
        check_interval: int = 300,  # 5 minutes
        logger: Optional[logging.Logger] = None
    ):
        self.log_dirs = log_dirs or []
        self.temp_dirs = temp_dirs or []
        self.cleanup_threshold = cleanup_threshold
        self.critical_threshold = critical_threshold
        self.max_log_age_days = max_log_age_days
        self.max_temp_age_hours = max_temp_age_hours
        self.check_interval = check_interval
        self.logger = logger or logging.getLogger(__name__)
        
        self._running = False
        self._thread = None
        self._cleanup_history = []
        
        # Default directories if none provided
        if not self.log_dirs:
            self.log_dirs = [
                "logs",
                "app/logs",
                "var/log",
                "/var/log",
                "/tmp/logs"
            ]
        
        if not self.temp_dirs:
            self.temp_dirs = [
                "tmp",
                "temp",
                "/tmp",
                "/var/tmp"
            ]
    
    def start(self):
        """Start disk monitoring"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="DiskMonitor"
        )
        self._thread.start()
        self.logger.info("💾 Disk monitoring started")
    
    def stop(self):
        """Stop disk monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Disk monitoring stopped")
    
    def check_disk_usage(self, path: str = "/") -> Dict[str, Any]:
        """Check disk usage for a path"""
        try:
            stat = shutil.disk_usage(path)
            
            total_gb = stat.total / (1024**3)
            used_gb = stat.used / (1024**3)
            free_gb = stat.free / (1024**3)
            usage_percent = (stat.used / stat.total) * 100
            
            status = "normal"
            if usage_percent > self.critical_threshold * 100:
                status = "critical"
            elif usage_percent > self.cleanup_threshold * 100:
                status = "warning"
            
            return {
                "path": path,
                "status": status,
                "usage_percent": round(usage_percent, 2),
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking disk usage: {e}")
            return {
                "path": path,
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def perform_cleanup(self, disk_info: Dict[str, Any]) -> Dict[str, Any]:
        """Perform automatic cleanup based on disk usage"""
        result = {
            "success": True,
            "actions": [],
            "freed_gb": 0.0,
            "errors": []
        }
        
        if disk_info.get("status") not in ["warning", "critical"]:
            return result
        
        # Cleanup based on severity
        if disk_info["status"] == "critical":
            # Aggressive cleanup
            result["actions"].append("Critical cleanup initiated")
            self._cleanup_old_logs(result, aggressive=True)
            self._cleanup_temp_files(result, aggressive=True)
            self._cleanup_cache_files(result)
            
        elif disk_info["status"] == "warning":
            # Conservative cleanup
            result["actions"].append("Warning cleanup initiated")
            self._cleanup_old_logs(result, aggressive=False)
            self._cleanup_temp_files(result, aggressive=False)
        
        # Log cleanup action
        self._cleanup_history.append({
            "timestamp": time.time(),
            "disk_info": disk_info,
            "result": result
        })
        
        return result
    
    def _cleanup_old_logs(self, result: Dict[str, Any], aggressive: bool = False):
        """Cleanup old log files"""
        cutoff_date = datetime.now() - timedelta(
            days=self.max_log_age_days if not aggressive else self.max_log_age_days // 2
        )
        
        for log_dir in self.log_dirs:
            if not os.path.exists(log_dir):
                continue
            
            try:
                freed_bytes = 0
                files_deleted = 0
                
                for root, _, files in os.walk(log_dir):
                    for file in files:
                        if file.endswith(('.log', '.txt', '.out', '.err')):
                            filepath = os.path.join(root, file)
                            try:
                                stat = os.stat(filepath)
                                file_time = datetime.fromtimestamp(stat.st_mtime)
                                
                                if file_time < cutoff_date:
                                    freed_bytes += stat.st_size
                                    os.remove(filepath)
                                    files_deleted += 1
                                    self.logger.debug(f"Deleted old log: {filepath}")
                                    
                            except Exception as e:
                                result["errors"].append(f"Error deleting {filepath}: {e}")
                
                if files_deleted > 0:
                    freed_gb = freed_bytes / (1024**3)
                    result["freed_gb"] += freed_gb
                    result["actions"].append(
                        f"Cleaned {files_deleted} log files from {log_dir}, freed {freed_gb:.2f}GB"
                    )
                    
            except Exception as e:
                result["errors"].append(f"Error cleaning log dir {log_dir}: {e}")
    
    def _cleanup_temp_files(self, result: Dict[str, Any], aggressive: bool = False):
        """Cleanup temporary files"""
        cutoff_hours = self.max_temp_age_hours if not aggressive else self.max_temp_age_hours // 2
        cutoff_date = datetime.now() - timedelta(hours=cutoff_hours)
        
        for temp_dir in self.temp_dirs:
            if not os.path.exists(temp_dir):
                continue
            
            try:
                freed_bytes = 0
                files_deleted = 0
                
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        filepath = os.path.join(root, file)
                        try:
                            # Skip important files
                            if file in ['.gitkeep', '.keep', 'README.md']:
                                continue
                            
                            stat = os.stat(filepath)
                            file_time = datetime.fromtimestamp(stat.st_mtime)
                            
                            if file_time < cutoff_date:
                                freed_bytes += stat.st_size
                                os.remove(filepath)
                                files_deleted += 1
                                self.logger.debug(f"Deleted temp file: {filepath}")
                                
                        except Exception as e:
                            result["errors"].append(f"Error deleting {filepath}: {e}")
                
                if files_deleted > 0:
                    freed_gb = freed_bytes / (1024**3)
                    result["freed_gb"] += freed_gb
                    result["actions"].append(
                        f"Cleaned {files_deleted} temp files from {temp_dir}, freed {freed_gb:.2f}GB"
                    )
                    
            except Exception as e:
                result["errors"].append(f"Error cleaning temp dir {temp_dir}: {e}")
    
    def _cleanup_cache_files(self, result: Dict[str, Any]):
        """Cleanup cache files"""
        cache_dirs = [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "node_modules",
            ".npm",
            ".cache"
        ]
        
        for cache_pattern in cache_dirs:
            for root, dirs, _ in os.walk(".", topdown=False):
                if cache_pattern in root:
                    try:
                        freed_bytes = 0
                        # Calculate size before deletion
                        for dirpath, _, files in os.walk(root):
                            for file in files:
                                try:
                                    freed_bytes += os.path.getsize(os.path.join(dirpath, file))
                                except:
                                    pass
                        
                        # Delete the directory
                        shutil.rmtree(root, ignore_errors=True)
                        
                        freed_gb = freed_bytes / (1024**3)
                        result["freed_gb"] += freed_gb
                        result["actions"].append(
                            f"Cleaned cache: {root}, freed {freed_gb:.2f}GB"
                        )
                        
                    except Exception as e:
                        result["errors"].append(f"Error cleaning cache {root}: {e}")
    
    def rotate_logs(self, log_dir: str, max_size_mb: int = 100, backup_count: int = 5) -> Dict[str, Any]:
        """Rotate log files when they get too large"""
        result = {
            "success": True,
            "rotated": [],
            "errors": []
        }
        
        if not os.path.exists(log_dir):
            return result
        
        try:
            for file in os.listdir(log_dir):
                if file.endswith('.log'):
                    filepath = os.path.join(log_dir, file)
                    stat = os.stat(filepath)
                    
                    # Check if file needs rotation (size > max_size_mb)
                    if stat.st_size > max_size_mb * 1024 * 1024:
                        # Rotate existing backups
                        for i in range(backup_count - 1, 0, -1):
                            old_file = f"{filepath}.{i}"
                            new_file = f"{filepath}.{i + 1}"
                            if os.path.exists(old_file):
                                os.rename(old_file, new_file)
                        
                        # Create new backup
                        backup_file = f"{filepath}.1"
                        os.rename(filepath, backup_file)
                        
                        # Create new empty log file
                        open(filepath, 'w').close()
                        
                        result["rotated"].append(file)
                        self.logger.info(f"Rotated log file: {file} -> {backup_file}")
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            self.logger.error(f"Error rotating logs: {e}")
        
        return result
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                # Check disk usage
                disk_info = self.check_disk_usage()
                
                # Perform cleanup if needed
                if disk_info["status"] in ["warning", "critical"]:
                    self.logger.warning(
                        f"💾 Disk {disk_info['status']}: {disk_info['usage_percent']}% used "
                        f"(Free: {disk_info['free_gb']:.1f}GB)"
                    )
                    
                    cleanup_result = self.perform_cleanup(disk_info)
                    
                    if cleanup_result["freed_gb"] > 0:
                        self.logger.info(
                            f"🧹 Cleanup freed {cleanup_result['freed_gb']:.2f}GB. "
                            f"Actions: {', '.join(cleanup_result['actions'][:3])}"
                        )
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in disk monitoring loop: {e}")
                time.sleep(60)
    
    def get_cleanup_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get cleanup history"""
        return self._cleanup_history[-limit:]
    
    def force_cleanup(self) -> Dict[str, Any]:
        """Force cleanup regardless of disk usage"""
        disk_info = self.check_disk_usage()
        return self.perform_cleanup(disk_info)