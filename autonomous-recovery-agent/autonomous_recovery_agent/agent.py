"""
Autonomous Recovery Agent - Main entry point
"""

import logging
import threading
import time
from flask import Flask, request, jsonify
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field

from .maintenance.manager import MaintenanceManager, MaintenanceLevel
from .traffic.throttler import TrafficThrottler, ThrottleLevel
from .config_manager import ConfigurationManager
from .monitoring.disk_monitor import DiskMonitor
from .monitoring.service_monitor import ServiceMonitor
from .monitoring.database_monitor import DatabaseMonitor
from .recovery.engine import RecoveryEngine
from .flask_integration import FlaskIntegration
from .mongodb_integration import patch_pymongo


@dataclass
class AgentConfig:
    """Configuration for the autonomous recovery agent"""

    # General settings
    enabled: bool = True
    log_level: str = "INFO"
    check_interval: int = 30

    # Service monitoring
    service_monitoring: bool = True
    max_service_memory_mb: float = 500
    max_service_cpu_percent: float = 80

    # Database monitoring
    database_monitoring: bool = True
    mongodb_url: Optional[str] = None
    max_db_connection_time_ms: float = 100
    max_db_query_time_ms: float = 500

    # Recovery settings
    auto_recovery: bool = True
    max_restart_attempts: int = 3
    restart_cooldown: int = 60

    # Disk monitoring
    disk_monitoring: bool = True
    disk_cleanup_threshold: float = 0.85
    disk_critical_threshold: float = 0.95
    max_log_age_days: int = 30
    max_temp_age_hours: int = 24
    log_rotation_size_mb: int = 100
    log_backup_count: int = 5

    # Configuration management
    config_management: bool = True
    config_dirs: List[str] = field(default_factory=lambda: [".", "config"])
    watch_config_files: bool = True

    # Maintenance mode
    maintenance_mode: bool = True
    maintenance_status_file: str = "maintenance_status.json"

    # Traffic throttling
    traffic_throttling: bool = True
    default_rps: int = 100
    overload_threshold: float = 0.8
    recovery_threshold: float = 0.5

    # Web UI
    enable_web_ui: bool = True
    web_ui_port: int = 8081
    web_ui_host: str = "0.0.0.0"

    # API endpoints
    enable_api: bool = True
    api_prefix: str = "/recovery"

    # Custom callbacks
    on_service_unhealthy: Optional[Callable] = None
    on_database_unhealthy: Optional[Callable] = None
    on_recovery_completed: Optional[Callable] = None

    # Disk cleanup directories
    log_dirs: List[str] = field(default_factory=lambda: ["logs", "app/logs"])
    temp_dirs: List[str] = field(default_factory=lambda: ["tmp", "temp"])


class AutonomousRecoveryAgent:
    """
    Autonomous Recovery Agent for Flask + MongoDB applications

    Usage:
        agent = AutonomousRecoveryAgent(
            flask_app=app,
            mongodb_url="mongodb://localhost:27017"
        )
        agent.start()
    """

    def __init__(
        self,
        flask_app=None,
        mongodb_url: Optional[str] = None,
        config: Optional[AgentConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.flask_app = flask_app
        self.mongodb_url = mongodb_url
        self.config = config or AgentConfig()
        self.logger = logger or logging.getLogger(__name__)

        # Initialize components
        self.service_monitor = None
        self.database_monitor = None
        self.recovery_engine = None
        self.flask_integration = None
        self.disk_monitor = None
        self.config_manager = None
        self.traffic_throttler = None
        self.maintenance_manager = None

        # Runtime state
        self._running = False
        self._monitor_thread = None
        self._web_ui_thread = None

        self._setup_logging()
        self._initialize_components()

    def _setup_logging(self):
        """Setup logging configuration"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(getattr(logging, self.config.log_level))

    def _initialize_components(self):
        """Initialize monitoring and recovery components"""

        # Initialize service monitor
        if self.config.service_monitoring:
            from .monitoring.service_monitor import ServiceMonitor

            self.service_monitor = ServiceMonitor(
                process_name="python",
                max_memory_mb=self.config.max_service_memory_mb,
                max_cpu_percent=self.config.max_service_cpu_percent,
                logger=self.logger,
            )

        # Initialize database monitor
        if self.config.database_monitoring and self.mongodb_url:
            from .monitoring.database_monitor import DatabaseMonitor

            self.database_monitor = DatabaseMonitor(
                mongodb_url=self.mongodb_url,
                max_connection_time_ms=self.config.max_db_connection_time_ms,
                max_query_time_ms=self.config.max_db_query_time_ms,
                logger=self.logger,
            )

        # Initialize disk monitor
        if self.config.disk_monitoring:
            from .monitoring.disk_monitor import DiskMonitor

            self.disk_monitor = DiskMonitor(
                log_dirs=self.config.log_dirs,
                temp_dirs=self.config.temp_dirs,
                cleanup_threshold=self.config.disk_cleanup_threshold,
                critical_threshold=self.config.disk_critical_threshold,
                max_log_age_days=self.config.max_log_age_days,
                max_temp_age_hours=self.config.max_temp_age_hours,
                logger=self.logger,
            )

        # Initialize traffic throttler
        if self.config.traffic_throttling and self.flask_app:
            from .traffic.throttler import TrafficThrottler

            self.traffic_throttler = TrafficThrottler(
                default_rps=self.config.default_rps,
                overload_threshold=self.config.overload_threshold,
                recovery_threshold=self.config.recovery_threshold,
                logger=self.logger,
            )

        if self.config.maintenance_mode:
            from .maintenance.manager import MaintenanceManager

            self.maintenance_manager = MaintenanceManager(
                status_file=self.config.maintenance_status_file, logger=self.logger
            )

        if self.config.config_management:
            from .config_manager import ConfigurationManager

            self.config_manager = ConfigurationManager(
                config_dirs=self.config.config_dirs, logger=self.logger
            )

        # Initialize recovery engine
        if self.config.auto_recovery:
            from .recovery.engine import RecoveryEngine

            self.recovery_engine = RecoveryEngine(
                max_attempts=self.config.max_restart_attempts,
                cooldown_seconds=self.config.restart_cooldown,
                logger=self.logger,
            )

        # Patch pymongo for automatic recovery
        try:
            from .mongodb_integration import patch_pymongo

            patch_pymongo()
            self.logger.info("pymongo patched for automatic recovery")
        except Exception as e:
            self.logger.warning(f"Failed to patch pymongo: {e}")

        # Integrate with Flask
        if self.flask_app:
            from .flask_integration import FlaskIntegration

            self.flask_integration = FlaskIntegration(
                flask_app=self.flask_app,
                agent=self,
                api_prefix=self.config.api_prefix,
                enable_api=self.config.enable_api,
                logger=self.logger,
            )
            self._integrate_throttler_with_flask()

    def start(self):
        """Start the autonomous recovery agent"""
        if self._running:
            self.logger.warning("Agent is already running")
            return

        self.logger.info("🚀 Starting Autonomous Recovery Agent...")

        try:
            # Start service monitoring
            if self.service_monitor:
                self.service_monitor.start()
                self.logger.info("✅ Service monitoring started")

            # Start database monitoring
            if self.database_monitor:
                self.database_monitor.start()
                self.logger.info("✅ Database monitoring started")

            if self.disk_monitor:
                self.disk_monitor.start()
                self.logger.info("💾 Disk monitoring started")

            if self.config_manager and self.config.watch_config_files:
                self.config_manager.start_watching()
                self._register_config_callbacks()
                self.logger.info("📝 Configuration manager started")

            # Start recovery engine
            if self.recovery_engine:
                self.recovery_engine.start()
                self.logger.info("✅ Recovery engine started")

            if self.maintenance_manager:
                self.logger.info("🔧 Maintenance mode management enabled")

            # Integrate with Flask
            if self.flask_integration:
                self.flask_integration.integrate()
                self.logger.info("✅ Flask integration completed")

            if self.traffic_throttler:
                self.logger.info("🚦 Traffic throttling enabled")

            self._register_maintenance_callbacks()
            self._integrate_maintenance_with_flask()

            # Start Web UI
            if self.config.enable_web_ui:
                self._start_web_ui()

            # Start main monitoring thread
            self._running = True
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True, name="RecoveryAgentMonitor"
            )
            self._monitor_thread.start()

            self.logger.info("🎉 Autonomous Recovery Agent started successfully!")
            self.logger.info(
                f"📊 Web Dashboard: http://{self.config.web_ui_host}:{self.config.web_ui_port}"
            )
            self.logger.info(f"🩺 Health endpoint: /health")
            self.logger.info(f"⚙️  Recovery API: {self.config.api_prefix}")

            # Register shutdown handler
            import atexit

            atexit.register(self.stop)

        except Exception as e:
            self.logger.error(f"❌ Failed to start agent: {e}")
            raise

    def _register_maintenance_callbacks(self):
        """Register callbacks for maintenance mode changes"""
        if not self.maintenance_manager:
            return

        # Register for all maintenance levels
        for level in MaintenanceLevel:
            self.maintenance_manager.register_callback(
                level, self._on_maintenance_change
            )

    def _on_maintenance_change(self, level: MaintenanceLevel, schedule):
        """Handle maintenance mode changes"""
        self.logger.info(f"🔄 Maintenance level changed to: {level.value}")

        # Take actions based on maintenance level
        if level == MaintenanceLevel.DEGRADED:
            # Enable read-only mode
            self._enable_readonly_mode()

        elif level == MaintenanceLevel.MAINTENANCE:
            # Disable non-essential features
            self._disable_non_essential_features()

        elif level == MaintenanceLevel.OFFLINE:
            # Prepare for complete shutdown
            self._prepare_for_shutdown()

        elif level == MaintenanceLevel.NORMAL:
            # Restore normal operations
            self._restore_normal_operations()

    def _enable_readonly_mode(self):
        """Enable read-only mode"""
        self.logger.info("Enabling read-only mode")
        # Implementation depends on your application

    def _disable_non_essential_features(self):
        """Disable non-essential features"""
        self.logger.info("Disabling non-essential features")
        # Implementation depends on your application

    def _prepare_for_shutdown(self):
        """Prepare for complete shutdown"""
        self.logger.info("Preparing for shutdown")
        # Implementation depends on your application

    def _restore_normal_operations(self):
        """Restore normal operations"""
        self.logger.info("Restoring normal operations")
        # Implementation depends on your application

    def _integrate_maintenance_with_flask(self):
        """Integrate maintenance manager with Flask app"""
        if not self.flask_app or not self.maintenance_manager:
            return

        @self.flask_app.before_request
        def check_maintenance():
            """Check if maintenance mode is active"""
            if not self.maintenance_manager:
                return

            level = self.maintenance_manager.get_current_level()

            if level != MaintenanceLevel.NORMAL:
                # Get maintenance page
                html = self.maintenance_manager.get_maintenance_page()

                # Render with context
                from flask import render_template_string

                return (
                    render_template_string(
                        html,
                        level=level.value,
                        reason="Scheduled maintenance",
                        estimated_end="Soon",
                    ),
                    503,
                )  # Service Unavailable

        # Add maintenance control endpoints
        @self.flask_app.route("/admin/maintenance/enable", methods=["POST"])
        def enable_maintenance():
            """Enable maintenance mode (admin only)"""
            # Add authentication check here
            data = request.get_json() or {}
            level = MaintenanceLevel(data.get("level", "maintenance"))
            reason = data.get("reason", "Scheduled maintenance")
            duration = data.get("duration", 60)

            schedule_id = self.maintenance_manager.enable_maintenance(
                level=level, reason=reason, duration_minutes=duration
            )

            return jsonify(
                {
                    "success": True,
                    "schedule_id": schedule_id,
                    "message": f"Maintenance mode enabled: {level.value}",
                }
            )

        @self.flask_app.route("/admin/maintenance/disable", methods=["POST"])
        def disable_maintenance():
            """Disable maintenance mode (admin only)"""
            # Add authentication check here
            data = request.get_json() or {}
            schedule_id = data.get("schedule_id")

            self.maintenance_manager.disable_maintenance(schedule_id)

            return jsonify({"success": True, "message": "Maintenance mode disabled"})

        @self.flask_app.route("/admin/maintenance/status", methods=["GET"])
        def maintenance_status():
            """Get maintenance status (admin only)"""
            # Add authentication check here
            level = self.maintenance_manager.get_current_level()
            schedules = self.maintenance_manager.get_schedules()

            return jsonify(
                {
                    "current_level": level.value,
                    "schedules": {
                        sid: {
                            "level": s.level.value,
                            "reason": s.reason,
                            "start_time": s.start_time.isoformat(),
                            "end_time": s.end_time.isoformat(),
                        }
                        for sid, s in schedules.items()
                    },
                }
            )

        self.logger.info("Maintenance manager integrated with Flask")

    def _integrate_throttler_with_flask(self):
        """Integrate traffic throttler with Flask app"""
        if not self.flask_app or not self.traffic_throttler:
            return

        @self.flask_app.before_request
        def check_throttle():
            """Check if request should be throttled"""
            if not self.traffic_throttler:
                return

            # Update system load from service monitor
            if self.service_monitor:
                try:
                    health = self.service_monitor.check_health()
                    if health and isinstance(health, dict):
                        cpu_percent = health.get("metrics", {}).get("cpu_percent", 0)
                        memory_mb = health.get("metrics", {}).get("memory_mb", 0)

                        # Convert memory to percentage (assuming 1GB = 100%)
                        memory_percent = min(100, memory_mb / 10)

                        self.traffic_throttler.update_system_load(
                            cpu_percent, memory_percent
                        )
                except:
                    pass

            # Check if request should be throttled
            client_ip = request.remote_addr
            path = request.path
            method = request.method
            user_agent = request.user_agent.string

            if self.traffic_throttler.should_throttle(
                client_ip, path, method, user_agent
            ):
                # Return 429 Too Many Requests
                from flask import jsonify

                return (
                    jsonify(
                        {
                            "error": "Too many requests",
                            "message": "Service is experiencing high load. Please try again later.",
                            "status": 429,
                        }
                    ),
                    429,
                )

        self.logger.info("Traffic throttler integrated with Flask")

    def _register_config_callbacks(self):
        """Register callbacks for config changes"""
        if not self.config_manager:
            return

        # Example: Reload database config
        self.config_manager.register_callback(
            "database.yaml", self._on_database_config_change
        )

        # Example: Reload service config
        self.config_manager.register_callback(
            "service.yaml", self._on_service_config_change
        )

        # Example: Reload monitoring config
        self.config_manager.register_callback(
            "monitoring.yaml", self._on_monitoring_config_change
        )

    def _on_database_config_change(self, new_config: Dict[str, Any], change):
        """Handle database configuration changes"""
        self.logger.info(f"🔄 Database configuration changed: {change.file_path}")

        # Update database connections
        if self.database_monitor and new_config:
            # Extract MongoDB URL
            mongodb_url = new_config.get("mongodb_url") or new_config.get(
                "database_url"
            )
            if mongodb_url:
                self.logger.info(f"Updating MongoDB URL to: {mongodb_url}")
                # In real implementation, you would update the connection

    def _on_service_config_change(self, new_config: Dict[str, Any], change):
        """Handle service configuration changes"""
        self.logger.info(f"🔄 Service configuration changed: {change.file_path}")

        # Update service monitoring
        if self.service_monitor and new_config:
            max_memory = new_config.get("max_memory_mb")
            max_cpu = new_config.get("max_cpu_percent")

            if max_memory:
                self.service_monitor.max_memory_mb = float(max_memory)

            if max_cpu:
                self.service_monitor.max_cpu_percent = float(max_cpu)

    def _on_monitoring_config_change(self, new_config: Dict[str, Any], change):
        """Handle monitoring configuration changes"""
        self.logger.info(f"🔄 Monitoring configuration changed: {change.file_path}")

        # Update monitoring intervals
        if new_config:
            check_interval = new_config.get("check_interval")
            if check_interval:
                self.config.check_interval = int(check_interval)

    def stop(self):
        """Stop the autonomous recovery agent"""
        if not self._running:
            return

        self.logger.info("🛑 Stopping Autonomous Recovery Agent...")
        self._running = False

        # Stop all components
        if self.service_monitor:
            self.service_monitor.stop()

        if self.database_monitor:
            self.database_monitor.stop()

        if self.recovery_engine:
            self.recovery_engine.stop()

        self.logger.info("✅ Autonomous Recovery Agent stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                # Check service health
                if self.service_monitor:
                    service_health = self.service_monitor.check_health()
                    if service_health and service_health.get("status") in [
                        "unhealthy",
                        "critical",
                    ]:
                        self._handle_service_unhealthy(service_health)

                # Check database health
                if self.database_monitor:
                    # FIX: Handle tuple return from check_health()
                    db_check_result = self.database_monitor.check_health()

                    # Check if it's a tuple (health_data, state_changed) or just health_data
                    if isinstance(db_check_result, tuple):
                        db_health, state_changed = db_check_result
                    else:
                        db_health = db_check_result

                    # Log state changes if available
                    if isinstance(db_check_result, tuple) and state_changed:
                        if db_health.get("is_reachable"):
                            self.logger.info(
                                f"✅ Database state changed to: {db_health.get('status')}"
                            )
                        else:
                            self.logger.warning(
                                f"⚠️ Database state changed to: {db_health.get('status')}"
                            )

                    # Trigger recovery if needed
                    if db_health and db_health.get("status") in [
                        "disconnected",
                        "error",
                    ]:
                        self._handle_database_unhealthy(db_health)

                # Sleep until next check
                time.sleep(self.config.check_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)

    def _handle_service_unhealthy(self, health_data: Dict[str, Any]):
        """Handle unhealthy service"""
        self.logger.warning(f"⚠️ Service unhealthy: {health_data.get('error_message')}")

        # Call custom callback
        if self.config.on_service_unhealthy:
            try:
                self.config.on_service_unhealthy(health_data)
            except Exception as e:
                self.logger.error(f"Error in service unhealthy callback: {e}")

        # Trigger automatic recovery
        if self.config.auto_recovery and self.recovery_engine:
            result = self.recovery_engine.recover_service(
                service_type="flask", health_data=health_data
            )

            # Call recovery completed callback
            if self.config.on_recovery_completed:
                try:
                    self.config.on_recovery_completed(result)
                except Exception as e:
                    self.logger.error(f"Error in recovery completed callback: {e}")

    def _handle_database_unhealthy(self, health_data: Dict[str, Any]):
        """Handle unhealthy database"""
        self.logger.warning(f"⚠️ Database unhealthy: {health_data.get('error_message')}")

        # Call custom callback
        if self.config.on_database_unhealthy:
            try:
                self.config.on_database_unhealthy(health_data)
            except Exception as e:
                self.logger.error(f"Error in database unhealthy callback: {e}")

        # Trigger automatic recovery
        if self.config.auto_recovery and self.recovery_engine:
            result = self.recovery_engine.recover_database(
                db_type="mongodb", health_data=health_data
            )

            # Check recovery result
            if result.get("success"):
                self.logger.info(f"✅ Recovery initiated: {result.get('message')}")

                # Monitor for recovery completion
                self._monitor_recovery_completion()
            else:
                self.logger.warning(f"⚠️ Recovery failed: {result.get('message')}")

            # Call recovery completed callback
            if self.config.on_recovery_completed:
                try:
                    self.config.on_recovery_completed(result)
                except Exception as e:
                    self.logger.error(f"Error in recovery completed callback: {e}")

    def _monitor_recovery_completion(self):
        """Monitor for recovery completion"""
        if not self.database_monitor:
            return

        # Start a thread to monitor recovery
        import threading

        def monitor():
            attempts = 0
            max_attempts = 30  # Monitor for 30 checks (approx 15 minutes)

            while attempts < max_attempts and self._running:
                try:
                    health, state_changed = self.database_monitor.check_health()

                    if health.get("is_reachable"):
                        self.logger.info("🎉 Database recovery completed successfully!")

                        # Reset recovery attempts
                        self.database_monitor.reset_recovery_attempts()
                        break

                    attempts += 1
                    time.sleep(30)  # Check every 30 seconds

                except Exception as e:
                    self.logger.error(f"Error monitoring recovery: {e}")
                    break

        thread = threading.Thread(target=monitor, daemon=True, name="RecoveryMonitor")
        thread.start()

    def _start_web_ui(self):
        """Start Web UI in a separate thread"""
        try:
            from .web_ui import start_web_ui

            self._web_ui_thread = threading.Thread(
                target=start_web_ui,
                args=(self.config.web_ui_host, self.config.web_ui_port, self),
                daemon=True,
                name="RecoveryAgentWebUI",
            )
            self._web_ui_thread.start()
            self.logger.info(
                f"🌐 Web UI started on http://{self.config.web_ui_host}:{self.config.web_ui_port}"
            )
        except Exception as e:
            self.logger.error(f"Failed to start Web UI: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        status = {
            "running": self._running,
            "service_monitoring": self.service_monitor is not None,
            "database_monitoring": self.database_monitor is not None,
            "auto_recovery": self.recovery_engine is not None,
            "web_ui_enabled": self.config.enable_web_ui,
        }

        # Add service health
        if self.service_monitor:
            status["service_health"] = self.service_monitor.check_health()

        # Add database health
        if self.database_monitor:
            status["database_health"] = self.database_monitor.check_health()

        return status

    def trigger_recovery(
        self, component: str, reason: str = "Manual trigger"
    ) -> Dict[str, Any]:
        """Manually trigger recovery for a component"""
        if component == "service" and self.recovery_engine:
            return self.recovery_engine.recover_service("flask", {"reason": reason})
        elif component == "database" and self.recovery_engine:
            return self.recovery_engine.recover_database("mongodb", {"reason": reason})
        else:
            return {"success": False, "error": f"Unknown component: {component}"}
