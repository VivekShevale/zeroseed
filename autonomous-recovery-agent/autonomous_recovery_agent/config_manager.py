"""
Configuration management with hot reload
"""
import json
import yaml
import threading
import time
import logging
import hashlib
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


@dataclass
class ConfigChange:
    """Configuration change event"""
    timestamp: datetime
    file_path: str
    change_type: str  # 'added', 'modified', 'deleted'
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class ConfigFileHandler(FileSystemEventHandler):
    """Watch for config file changes"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def on_modified(self, event):
        if not event.is_directory:
            self.config_manager.handle_config_change(event.src_path, 'modified')
    
    def on_created(self, event):
        if not event.is_directory:
            self.config_manager.handle_config_change(event.src_path, 'added')
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.config_manager.handle_config_change(event.src_path, 'deleted')


class ConfigurationManager:
    """Manage configuration files with hot reload"""
    
    def __init__(
        self,
        config_dirs: List[str] = None,
        watch_files: List[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.config_dirs = config_dirs or [".", "config", "conf"]
        self.watch_files = watch_files or []
        self.logger = logger or logging.getLogger(__name__)
        
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._config_hashes: Dict[str, str] = {}
        self._change_history: List[ConfigChange] = []
        self._callbacks: Dict[str, List[Callable]] = {}
        
        self._observer = None
        self._running = False
        
        # Default config files to watch
        if not self.watch_files:
            self.watch_files = [
                "config.yaml", "config.yml", "config.json",
                "settings.yaml", "settings.yml", "settings.json",
                ".env", "environment.yaml", "environment.yml"
            ]
    
    def start_watching(self):
        """Start watching for config file changes"""
        if self._running:
            return
        
        self._observer = Observer()
        event_handler = ConfigFileHandler(self)
        
        # Watch all config directories
        for config_dir in self.config_dirs:
            if Path(config_dir).exists():
                self._observer.schedule(event_handler, config_dir, recursive=False)
                self.logger.info(f"👀 Watching config directory: {config_dir}")
        
        self._observer.start()
        self._running = True
        
        # Load initial configs
        self.load_all_configs()
        
        self.logger.info("Configuration manager started watching for changes")
    
    def stop_watching(self):
        """Stop watching for config file changes"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
        self._running = False
        self.logger.info("Configuration manager stopped")
    
    def load_all_configs(self):
        """Load all configuration files"""
        for config_dir in self.config_dirs:
            config_path = Path(config_dir)
            if not config_path.exists():
                continue
            
            for config_file in self.watch_files:
                file_path = config_path / config_file
                if file_path.exists():
                    self.load_config(str(file_path))
    
    def load_config(self, file_path: str) -> bool:
        """Load a single configuration file"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            # Calculate file hash
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # Skip if unchanged
            if file_path in self._config_hashes and self._config_hashes[file_path] == file_hash:
                return True
            
            # Load based on file extension
            if file_path.endswith(('.yaml', '.yml')):
                with open(file_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    config = json.load(f) or {}
            elif file_path.endswith('.env'):
                config = self._parse_env_file(file_path)
            else:
                # Try to parse as text key-value
                config = self._parse_text_config(file_path)
            
            old_hash = self._config_hashes.get(file_path)
            
            # Store config
            self._configs[file_path] = config
            self._config_hashes[file_path] = file_hash
            
            # Record change
            change = ConfigChange(
                timestamp=datetime.now(),
                file_path=file_path,
                change_type='modified' if old_hash else 'added',
                old_hash=old_hash,
                new_hash=file_hash,
                success=True
            )
            self._change_history.append(change)
            
            # Trigger callbacks
            self._trigger_callbacks(file_path, config, change)
            
            self.logger.info(f"📝 Loaded config: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading config {file_path}: {e}")
            
            change = ConfigChange(
                timestamp=datetime.now(),
                file_path=file_path,
                change_type='error',
                success=False,
                error=str(e)
            )
            self._change_history.append(change)
            
            return False
    
    def handle_config_change(self, file_path: str, change_type: str):
        """Handle configuration file change"""
        if change_type == 'deleted':
            # Config file was deleted
            if file_path in self._configs:
                old_hash = self._config_hashes.get(file_path)
                del self._configs[file_path]
                del self._config_hashes[file_path]
                
                change = ConfigChange(
                    timestamp=datetime.now(),
                    file_path=file_path,
                    change_type='deleted',
                    old_hash=old_hash,
                    success=True
                )
                self._change_history.append(change)
                
                # Trigger deletion callbacks
                self._trigger_callbacks(file_path, None, change)
                
                self.logger.warning(f"🗑️ Config file deleted: {file_path}")
        
        else:
            # Config file was added or modified
            self.load_config(file_path)
            self.logger.info(f"🔄 Config file {change_type}: {file_path}")
    
    def register_callback(self, config_key: str, callback: Callable):
        """Register callback for config changes"""
        if config_key not in self._callbacks:
            self._callbacks[config_key] = []
        self._callbacks[config_key].append(callback)
        self.logger.debug(f"Registered callback for {config_key}")
    
    def _trigger_callbacks(self, file_path: str, new_config: Optional[Dict[str, Any]], change: ConfigChange):
        """Trigger registered callbacks"""
        config_key = Path(file_path).name
        
        if config_key in self._callbacks:
            for callback in self._callbacks[config_key]:
                try:
                    callback(new_config, change)
                except Exception as e:
                    self.logger.error(f"Error in config callback: {e}")
    
    def get_config(self, file_path: str = None) -> Dict[str, Any]:
        """Get configuration"""
        if file_path:
            return self._configs.get(file_path, {}).copy()
        
        # Merge all configs (later files override earlier ones)
        merged_config = {}
        for config in self._configs.values():
            merged_config.update(config)
        return merged_config
    
    def update_config(self, file_path: str, updates: Dict[str, Any], save: bool = True) -> bool:
        """Update configuration programmatically"""
        try:
            if file_path not in self._configs:
                self._configs[file_path] = {}
            
            # Update config
            self._configs[file_path].update(updates)
            
            if save:
                # Save to file
                self._save_config(file_path)
            
            # Calculate new hash
            config_str = json.dumps(self._configs[file_path], sort_keys=True)
            new_hash = hashlib.md5(config_str.encode()).hexdigest()
            old_hash = self._config_hashes.get(file_path)
            
            self._config_hashes[file_path] = new_hash
            
            # Record change
            change = ConfigChange(
                timestamp=datetime.now(),
                file_path=file_path,
                change_type='updated',
                old_hash=old_hash,
                new_hash=new_hash,
                success=True
            )
            self._change_history.append(change)
            
            # Trigger callbacks
            self._trigger_callbacks(file_path, self._configs[file_path], change)
            
            self.logger.info(f"Updated config: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating config: {e}")
            return False
    
    def _save_config(self, file_path: str):
        """Save configuration to file"""
        try:
            config = self._configs[file_path]
            
            if file_path.endswith(('.yaml', '.yml')):
                with open(file_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
            elif file_path.endswith('.json'):
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
            else:
                # Save as text key-value
                with open(file_path, 'w') as f:
                    for key, value in config.items():
                        f.write(f"{key}={value}\n")
            
        except Exception as e:
            self.logger.error(f"Error saving config {file_path}: {e}")
            raise
    
    def _parse_env_file(self, file_path: str) -> Dict[str, Any]:
        """Parse .env file"""
        config = {}
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        return config
    
    def _parse_text_config(self, file_path: str) -> Dict[str, Any]:
        """Parse text config file"""
        config = {}
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
                    elif ':' in line:
                        key, value = line.split(':', 1)
                        config[key.strip()] = value.strip()
        return config
    
    def get_change_history(self, limit: int = 20) -> List[ConfigChange]:
        """Get configuration change history"""
        return self._change_history[-limit:]
    
    def rollback(self, file_path: str, steps: int = 1) -> bool:
        """Rollback configuration changes"""
        # This would require storing previous versions
        # For now, just log the intention
        self.logger.info(f"Rollback requested for {file_path} ({steps} steps)")
        return False