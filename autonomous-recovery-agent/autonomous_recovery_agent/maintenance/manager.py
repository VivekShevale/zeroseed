"""
Maintenance mode management
"""
import json
import time
import threading
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class MaintenanceLevel(Enum):
    NORMAL = "normal"
    DEGRADED = "degraded"  # Read-only mode
    MAINTENANCE = "maintenance"  # Limited functionality
    OFFLINE = "offline"  # Completely offline


@dataclass
class MaintenanceSchedule:
    """Maintenance schedule"""
    start_time: datetime
    end_time: datetime
    level: MaintenanceLevel
    reason: str
    affected_services: list = field(default_factory=list)
    notifications_sent: bool = False


class MaintenanceManager:
    """Manage maintenance modes and schedules"""
    
    def __init__(
        self,
        status_file: str = "maintenance_status.json",
        logger: Optional[logging.Logger] = None
    ):
        self.status_file = status_file
        self.logger = logger or logging.getLogger(__name__)
        
        self._current_level: MaintenanceLevel = MaintenanceLevel.NORMAL
        self._schedules: Dict[str, MaintenanceSchedule] = {}
        self._callbacks: Dict[MaintenanceLevel, List[Callable]] = {}
        self._maintenance_page_html: Optional[str] = None
        self._lock = threading.RLock()
        
        # Load saved status
        self._load_status()
        
        # Start schedule monitoring
        self._monitor_thread = threading.Thread(
            target=self._monitor_schedules,
            daemon=True,
            name="MaintenanceMonitor"
        )
        self._monitor_thread.start()
    
    def enable_maintenance(
        self,
        level: MaintenanceLevel,
        reason: str,
        duration_minutes: int = 60,
        affected_services: list = None
    ) -> str:
        """Enable maintenance mode"""
        schedule_id = f"maintenance_{int(time.time())}"
        
        schedule = MaintenanceSchedule(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=duration_minutes),
            level=level,
            reason=reason,
            affected_services=affected_services or []
        )
        
        with self._lock:
            self._schedules[schedule_id] = schedule
            self._current_level = level
        
        # Save status
        self._save_status()
        
        # Trigger callbacks
        self._trigger_callbacks(level, schedule)
        
        self.logger.info(
            f"🔧 Maintenance enabled: {level.value} "
            f"(Reason: {reason}, Duration: {duration_minutes}min)"
        )
        
        return schedule_id
    
    def disable_maintenance(self, schedule_id: str = None):
        """Disable maintenance mode"""
        with self._lock:
            if schedule_id and schedule_id in self._schedules:
                # Disable specific schedule
                del self._schedules[schedule_id]
            elif not schedule_id:
                # Disable all schedules
                self._schedules.clear()
            
            # Determine new level
            self._current_level = self._determine_current_level()
        
        # Save status
        self._save_status()
        
        # Trigger callbacks
        self._trigger_callbacks(self._current_level, None)
        
        self.logger.info(f"✅ Maintenance disabled, returning to {self._current_level.value}")
    
    def _determine_current_level(self) -> MaintenanceLevel:
        """Determine current maintenance level based on active schedules"""
        now = datetime.now()
        highest_level = MaintenanceLevel.NORMAL
        
        for schedule in self._schedules.values():
            if schedule.start_time <= now <= schedule.end_time:
                # Map levels to priority
                level_priority = {
                    MaintenanceLevel.NORMAL: 0,
                    MaintenanceLevel.DEGRADED: 1,
                    MaintenanceLevel.MAINTENANCE: 2,
                    MaintenanceLevel.OFFLINE: 3
                }
                
                if level_priority[schedule.level] > level_priority[highest_level]:
                    highest_level = schedule.level
        
        return highest_level
    
    def register_callback(self, level: MaintenanceLevel, callback: Callable):
        """Register callback for maintenance level changes"""
        with self._lock:
            if level not in self._callbacks:
                self._callbacks[level] = []
            self._callbacks[level].append(callback)
    
    def _trigger_callbacks(self, level: MaintenanceLevel, schedule: Optional[MaintenanceSchedule]):
        """Trigger registered callbacks"""
        if level in self._callbacks:
            for callback in self._callbacks[level]:
                try:
                    callback(level, schedule)
                except Exception as e:
                    self.logger.error(f"Error in maintenance callback: {e}")
    
    def set_maintenance_page(self, html_content: str):
        """Set custom maintenance page HTML"""
        self._maintenance_page_html = html_content
        self.logger.info("Custom maintenance page set")
    
    def get_maintenance_page(self) -> str:
        """Get maintenance page HTML"""
        if self._maintenance_page_html:
            return self._maintenance_page_html
        
        # Default maintenance page
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Maintenance Mode</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                }
                .container { 
                    max-width: 600px; 
                    margin: 0 auto; 
                    background: rgba(255, 255, 255, 0.1);
                    padding: 40px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                h1 { font-size: 3em; margin-bottom: 20px; }
                .status { font-size: 1.5em; margin: 20px 0; padding: 10px; border-radius: 5px; }
                .normal { background: #4CAF50; }
                .degraded { background: #FFC107; }
                .maintenance { background: #FF9800; }
                .offline { background: #F44336; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛠️ Maintenance Mode</h1>
                <div class="status {{ level }}">
                    Status: {{ level|upper }}
                </div>
                <p>{{ reason }}</p>
                {% if estimated_end %}
                <p>Estimated completion: {{ estimated_end }}</p>
                {% endif %}
                <p>We apologize for the inconvenience. Please try again later.</p>
            </div>
        </body>
        </html>
        """
    
    def is_maintenance_active(self) -> bool:
        """Check if maintenance is active"""
        return self._current_level != MaintenanceLevel.NORMAL
    
    def get_current_level(self) -> MaintenanceLevel:
        """Get current maintenance level"""
        return self._current_level
    
    def get_schedules(self) -> Dict[str, MaintenanceSchedule]:
        """Get all maintenance schedules"""
        return self._schedules.copy()
    
    def _monitor_schedules(self):
        """Monitor maintenance schedules"""
        while True:
            try:
                with self._lock:
                    now = datetime.now()
                    schedules_to_remove = []
                    
                    for schedule_id, schedule in self._schedules.items():
                        # Check if schedule has ended
                        if now > schedule.end_time:
                            schedules_to_remove.append(schedule_id)
                    
                    # Remove ended schedules
                    for schedule_id in schedules_to_remove:
                        del self._schedules[schedule_id]
                    
                    # Update current level
                    new_level = self._determine_current_level()
                    if new_level != self._current_level:
                        old_level = self._current_level
                        self._current_level = new_level
                        self._save_status()
                        
                        # Trigger callbacks for level change
                        self._trigger_callbacks(new_level, None)
                        
                        self.logger.info(
                            f"🔄 Maintenance level changed: {old_level.value} -> {new_level.value}"
                        )
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in maintenance monitor: {e}")
                time.sleep(10)
    
    def _save_status(self):
        """Save maintenance status to file"""
        try:
            status = {
                "current_level": self._current_level.value,
                "schedules": {
                    schedule_id: {
                        "start_time": schedule.start_time.isoformat(),
                        "end_time": schedule.end_time.isoformat(),
                        "level": schedule.level.value,
                        "reason": schedule.reason,
                        "affected_services": schedule.affected_services
                    }
                    for schedule_id, schedule in self._schedules.items()
                },
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving maintenance status: {e}")
    
    def _load_status(self):
        """Load maintenance status from file"""
        try:
            with open(self.status_file, 'r') as f:
                status = json.load(f)
            
            self._current_level = MaintenanceLevel(status.get("current_level", "normal"))
            
            # Load schedules
            schedules_data = status.get("schedules", {})
            for schedule_id, data in schedules_data.items():
                schedule = MaintenanceSchedule(
                    start_time=datetime.fromisoformat(data["start_time"]),
                    end_time=datetime.fromisoformat(data["end_time"]),
                    level=MaintenanceLevel(data["level"]),
                    reason=data["reason"],
                    affected_services=data.get("affected_services", [])
                )
                self._schedules[schedule_id] = schedule
            
            self.logger.info(f"Loaded maintenance status: {self._current_level.value}")
            
        except FileNotFoundError:
            self.logger.info("No previous maintenance status found")
        except Exception as e:
            self.logger.error(f"Error loading maintenance status: {e}")