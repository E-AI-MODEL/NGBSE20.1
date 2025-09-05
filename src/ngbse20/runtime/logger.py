import logging
import os


class SecurityFilter(logging.Filter):
    """Filter to redact sensitive information from logs."""

    def __init__(self) -> None:
        super().__init__()
        # Patterns to redact
        self.sensitive_patterns = [
            r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{8,})["\']?',
            r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{8,})["\']?',
            r'secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{8,})["\']?',
            r'password["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{8,})["\']?',
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records to redact sensitive information."""
        if hasattr(record, "getMessage"):
            message = record.getMessage()
            for pattern in self.sensitive_patterns:
                import re

                message = re.sub(
                    pattern,
                    lambda m: m.group(0).replace(m.group(1), "***REDACTED***"),
                    message,
                    flags=re.IGNORECASE,
                )
            record.msg = message
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configure logging with security considerations."""
    # Check if we're in production
    env = os.getenv("ENV", "prod").lower()
    is_production = env in ["prod", "production"]

    # Override DEBUG in production unless explicitly allowed
    if is_production and level.upper() == "DEBUG":
        debug_override = os.getenv("ALLOW_DEBUG_IN_PROD", "false").lower()
        if debug_override not in ["true", "1", "yes"]:
            level = "INFO"
            print("WARNING: DEBUG logging disabled in production. " "Set ALLOW_DEBUG_IN_PROD=true to override.")

    lvl = getattr(logging, level.upper(), logging.INFO)

    # Configure logging
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        force=True,  # Override any existing configuration
    )

    # Add security filter to root logger
    root_logger = logging.getLogger()
    security_filter = SecurityFilter()
    root_logger.addFilter(security_filter)

    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={level.upper()}, environment={env}")

    if is_production and level.upper() == "DEBUG":
        logger.warning("DEBUG logging is enabled in production environment")
