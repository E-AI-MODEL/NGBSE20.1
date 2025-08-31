"""
Health check and monitoring module for NGBSE 20.1

Provides system status, performance metrics, and pipeline health information
for production monitoring and alerting.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logging import get_logger

LOGGER = get_logger(__name__)

class HealthChecker:
    """Health check system for NGBSE 20.1."""
    
    def __init__(self, output_dir: str = "out"):
        self.output_dir = Path(output_dir)
        self.start_time = time.time()
        self.health_metrics = {}
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health."""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": int(time.time() - self.start_time),
                "checks": {}
            }
            
            # Check output directory
            output_check = self._check_output_directory()
            health_status["checks"]["output_directory"] = output_check
            
            # Check recent activity
            activity_check = self._check_recent_activity()
            health_status["checks"]["recent_activity"] = activity_check
            
            # Check file system
            filesystem_check = self._check_filesystem()
            health_status["checks"]["filesystem"] = filesystem_check
            
            # Check performance
            performance_check = self._check_performance()
            health_status["checks"]["performance"] = performance_check
            
            # Overall status
            all_checks = list(health_status["checks"].values())
            if any(check.get("status") == "error" for check in all_checks):
                health_status["status"] = "degraded"
            if any(check.get("status") == "critical" for check in all_checks):
                health_status["status"] = "critical"
            
            return health_status
            
        except Exception as e:
            LOGGER.error("Health check failed: %s", e)
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "uptime_seconds": int(time.time() - self.start_time)
            }
    
    def _check_output_directory(self) -> Dict[str, Any]:
        """Check output directory health."""
        try:
            if not self.output_dir.exists():
                return {
                    "status": "error",
                    "message": "Output directory does not exist",
                    "path": str(self.output_dir)
                }
            
            if not self.output_dir.is_dir():
                return {
                    "status": "error", 
                    "message": "Output path is not a directory",
                    "path": str(self.output_dir)
                }
            
            # Check writability
            test_file = self.output_dir / ".health_test"
            try:
                test_file.write_text("health_check")
                test_file.unlink()
                writable = True
            except Exception:
                writable = False
            
            return {
                "status": "healthy" if writable else "error",
                "path": str(self.output_dir),
                "writable": writable,
                "exists": True,
                "is_directory": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Output directory check failed: {e}",
                "path": str(self.output_dir)
            }
    
    def _check_recent_activity(self) -> Dict[str, Any]:
        """Check recent pipeline activity."""
        try:
            findings_file = self.output_dir / "findings.json"
            stix_file = self.output_dir / "stix_bundle.json"
            history_dir = self.output_dir / "history"
            
            recent_activity = {
                "status": "healthy",
                "last_findings_update": None,
                "last_stix_update": None,
                "findings_count": 0,
                "history_files": 0
            }
            
            # Check findings file
            if findings_file.exists():
                try:
                    findings_data = json.loads(findings_file.read_text())
                    recent_activity["findings_count"] = len(findings_data)
                    recent_activity["last_findings_update"] = datetime.fromtimestamp(
                        findings_file.stat().st_mtime, tz=timezone.utc
                    ).isoformat()
                except Exception as e:
                    recent_activity["status"] = "error"
                    recent_activity["findings_error"] = str(e)
            
            # Check STIX file
            if stix_file.exists():
                try:
                    stix_data = json.loads(stix_file.read_text())
                    recent_activity["stix_objects"] = len(stix_data.get("objects", []))
                    recent_activity["last_stix_update"] = datetime.fromtimestamp(
                        stix_file.stat().st_mtime, tz=timezone.utc
                    ).isoformat()
                except Exception as e:
                    recent_activity["status"] = "error"
                    recent_activity["stix_error"] = str(e)
            
            # Check history directory
            if history_dir.exists():
                history_files = list(history_dir.glob("*.asset_scores.json"))
                recent_activity["history_files"] = len(history_files)
                
                if history_files:
                    # Check most recent history file
                    latest_history = max(history_files, key=lambda f: f.stat().st_mtime)
                    recent_activity["last_history_update"] = datetime.fromtimestamp(
                        latest_history.stat().st_mtime, tz=timezone.utc
                    ).isoformat()
            
            # Determine activity status
            if not recent_activity["last_findings_update"]:
                recent_activity["status"] = "warning"
                recent_activity["message"] = "No recent findings activity"
            elif recent_activity["findings_count"] == 0:
                recent_activity["status"] = "warning"
                recent_activity["message"] = "No findings collected"
            
            return recent_activity
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Recent activity check failed: {e}"
            }
    
    def _check_filesystem(self) -> Dict[str, Any]:
        """Check filesystem health."""
        try:
            # Check disk space
            stat = os.statvfs(self.output_dir)
            total_bytes = stat.f_frsize * stat.f_blocks
            free_bytes = stat.f_frsize * stat.f_bavail
            used_bytes = total_bytes - free_bytes
            
            disk_usage = {
                "total_gb": round(total_bytes / (1024**3), 2),
                "used_gb": round(used_bytes / (1024**3), 2),
                "free_gb": round(free_bytes / (1024**3), 2),
                "usage_percent": round((used_bytes / total_bytes) * 100, 1)
            }
            
            # Determine disk status
            if disk_usage["usage_percent"] > 90:
                disk_status = "critical"
            elif disk_usage["usage_percent"] > 80:
                disk_status = "warning"
            else:
                disk_status = "healthy"
            
            return {
                "status": disk_status,
                "disk_usage": disk_usage,
                "inodes": {
                    "total": stat.f_files,
                    "free": stat.f_ffree,
                    "usage_percent": round(((stat.f_files - stat.f_ffree) / stat.f_files) * 100, 1)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Filesystem check failed: {e}"
            }
    
    def _check_performance(self) -> Dict[str, Any]:
        """Check system performance metrics."""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "usage_percent": memory.percent
            }
            
            # Determine performance status
            if cpu_percent > 90 or memory_usage["usage_percent"] > 90:
                perf_status = "warning"
            elif cpu_percent > 70 or memory_usage["usage_percent"] > 70:
                perf_status = "warning"
            else:
                perf_status = "healthy"
            
            return {
                "status": perf_status,
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                "memory": memory_usage,
                "disk_io": {
                    "read_bytes": psutil.disk_io_counters().read_bytes if psutil.disk_io_counters() else 0,
                    "write_bytes": psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0
                }
            }
            
        except ImportError:
            return {
                "status": "warning",
                "message": "psutil not available for detailed performance metrics"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Performance check failed: {e}"
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        try:
            import psutil
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": int(time.time() - self.start_time),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": self._check_filesystem().get("disk_usage", {}),
                "process_info": {
                    "pid": os.getpid(),
                    "memory_mb": round(psutil.Process().memory_info().rss / (1024**2), 2),
                    "cpu_percent": psutil.Process().cpu_percent()
                }
            }
        except Exception as e:
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        try:
            # Check for running processes or recent activity
            findings_file = self.output_dir / "findings.json"
            
            if not findings_file.exists():
                return {
                    "status": "idle",
                    "message": "No pipeline activity detected",
                    "last_run": None
                }
            
            # Check last modification time
            last_modified = datetime.fromtimestamp(
                findings_file.stat().st_mtime, tz=timezone.utc
            )
            
            # Determine if pipeline is active
            time_since_last = datetime.now(timezone.utc) - last_modified
            
            if time_since_last.total_seconds() < 300:  # 5 minutes
                pipeline_status = "active"
                message = "Pipeline recently active"
            elif time_since_last.total_seconds() < 3600:  # 1 hour
                pipeline_status = "recent"
                message = "Pipeline active within last hour"
            else:
                pipeline_status = "idle"
                message = f"Pipeline idle for {time_since_last.total_seconds() / 3600:.1f} hours"
            
            return {
                "status": pipeline_status,
                "message": message,
                "last_run": last_modified.isoformat(),
                "time_since_last_seconds": int(time_since_last.total_seconds())
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Pipeline status check failed: {e}"
            }

def get_health_status(output_dir: str = "out") -> Dict[str, Any]:
    """Get comprehensive health status."""
    checker = HealthChecker(output_dir)
    return checker.check_system_health()

def get_metrics(output_dir: str = "out") -> Dict[str, Any]:
    """Get current performance metrics."""
    checker = HealthChecker(output_dir)
    return checker.get_metrics()

def get_pipeline_status(output_dir: str = "out") -> Dict[str, Any]:
    """Get current pipeline status."""
    checker = HealthChecker(output_dir)
    return checker.get_pipeline_status()