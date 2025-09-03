"""
Health monitoring for NGBSE 20.2.
Provides health checks and monitoring capabilities.
"""

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

import psutil

from ..logging import get_logger

LOGGER = get_logger(__name__)


@dataclass
class HealthStatus:
    """Health status for a component."""

    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    timestamp: str
    details: Dict[str, Any] = None


@dataclass
class SystemMetrics:
    """System performance metrics."""

    cpu_percent: float
    memory_percent: float
    disk_percent: float
    timestamp: str


class HealthChecker:
    """Health checker for NGBSE components."""

    def __init__(self):
        self.start_time = time.time()
        self.checks: List[callable] = [
            self._check_system_resources,
            self._check_config_files,
            self._check_credentials,
            self._check_network_connectivity,
        ]

    def check_health(self) -> Dict[str, Any]:
        """Run all health checks and return overall status."""
        results = []
        overall_status = "healthy"

        for check in self.checks:
            try:
                result = check()
                results.append(result)

                if result.status == "unhealthy":
                    overall_status = "unhealthy"
                elif result.status == "degraded" and overall_status == "healthy":
                    overall_status = "degraded"

            except Exception as e:
                error_result = HealthStatus(
                    name=check.__name__,
                    status="unhealthy",
                    message=f"Health check failed: {e}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                results.append(error_result)
                overall_status = "unhealthy"

        # Get system metrics
        metrics = self._get_system_metrics()

        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "checks": [result.__dict__ for result in results],
            "metrics": metrics.__dict__,
        }

    def _check_system_resources(self) -> HealthStatus:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            status = "healthy"
            message = "System resources normal"

            if cpu_percent > 90:
                status = "degraded"
                message = f"High CPU usage: {cpu_percent:.1f}%"
            elif memory.percent > 90:
                status = "degraded"
                message = f"High memory usage: {memory.percent:.1f}%"
            elif disk.percent > 90:
                status = "degraded"
                message = f"High disk usage: {disk.percent:.1f}%"

            return HealthStatus(
                name="system_resources",
                status=status,
                message=message,
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                },
            )

        except Exception as e:
            return HealthStatus(
                name="system_resources",
                status="unhealthy",
                message=f"Failed to check system resources: {e}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    def _check_config_files(self) -> HealthStatus:
        """Check if configuration files exist and are readable."""
        try:
            config_files = [
                "config/ngbse.config.yml",
                "config/rules.json",
                "config/seeds.jsonl",
            ]

            missing_files = []
            for file_path in config_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)

            if missing_files:
                return HealthStatus(
                    name="config_files",
                    status="degraded",
                    message=f"Missing config files: {', '.join(missing_files)}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    details={"missing_files": missing_files},
                )
            else:
                return HealthStatus(
                    name="config_files",
                    status="healthy",
                    message="All configuration files present",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        except Exception as e:
            return HealthStatus(
                name="config_files",
                status="unhealthy",
                message=f"Failed to check config files: {e}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    def _check_credentials(self) -> HealthStatus:
        """Check if required credentials are available."""
        try:
            required_creds = [
                "SHODAN_API_KEY",
                "CENSYS_API_ID",
                "CENSYS_API_SECRET",
                "LEAKIX_API_KEY",
                "URLSCAN_API_KEY",
                "GITHUB_TOKEN",
                "NEWS_API_KEY",
            ]

            missing_creds = []
            for cred in required_creds:
                if not os.getenv(cred):
                    missing_creds.append(cred)

            if len(missing_creds) == len(required_creds):
                return HealthStatus(
                    name="credentials",
                    status="unhealthy",
                    message="No API credentials configured",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    details={"missing_credentials": missing_creds},
                )
            elif missing_creds:
                return HealthStatus(
                    name="credentials",
                    status="degraded",
                    message=(
                        f"Some credentials missing: {len(missing_creds)}/"
                        f"{len(required_creds)}"
                    ),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    details={"missing_credentials": missing_creds},
                )
            else:
                return HealthStatus(
                    name="credentials",
                    status="healthy",
                    message="All credentials configured",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        except Exception as e:
            return HealthStatus(
                name="credentials",
                status="unhealthy",
                message=f"Failed to check credentials: {e}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    def _check_network_connectivity(self) -> HealthStatus:
        """Check basic network connectivity."""
        try:
            import requests

            # Test connectivity to common APIs
            test_urls = [
                "https://api.shodan.io",
                "https://search.censys.io",
                "https://leakix.net",
            ]

            failed_urls = []
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code >= 400:
                        failed_urls.append(url)
                except (requests.RequestException, ConnectionError, TimeoutError):
                    failed_urls.append(url)

            if len(failed_urls) == len(test_urls):
                return HealthStatus(
                    name="network_connectivity",
                    status="unhealthy",
                    message="No network connectivity to external APIs",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    details={"failed_urls": failed_urls},
                )
            elif failed_urls:
                return HealthStatus(
                    name="network_connectivity",
                    status="degraded",
                    message=(
                        f"Some API endpoints unreachable: {len(failed_urls)}/"
                        f"{len(test_urls)}"
                    ),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    details={"failed_urls": failed_urls},
                )
            else:
                return HealthStatus(
                    name="network_connectivity",
                    status="healthy",
                    message="All API endpoints reachable",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        except Exception as e:
            return HealthStatus(
                name="network_connectivity",
                status="unhealthy",
                message=f"Failed to check network connectivity: {e}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    def _get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        try:
            return SystemMetrics(
                cpu_percent=psutil.cpu_percent(),
                memory_percent=psutil.virtual_memory().percent,
                disk_percent=psutil.disk_usage("/").percent,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            LOGGER.warning(f"Failed to get system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )


def get_health_status() -> Dict[str, Any]:
    """Get current health status of NGBSE."""
    checker = HealthChecker()
    return checker.check_health()
