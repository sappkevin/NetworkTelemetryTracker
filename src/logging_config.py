"""
Structured logging configuration for the Network Telemetry Service.

Provides centralized logging setup with multiple output formats,
log levels, and structured JSON logging for production environments.
"""

import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
import os


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': os.getpid(),
            'thread_id': record.thread,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add custom fields from extra
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process',
                          'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, separators=(',', ':'))


class TelemetryLogger:
    """Enhanced logging setup for telemetry service."""
    
    @staticmethod
    def setup_logging(
        log_level: str = "INFO",
        log_format: str = "console",
        log_file: Optional[str] = None,
        enable_json: bool = False
    ) -> logging.Logger:
        """
        Set up comprehensive logging for the telemetry service.
        
        Args:
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Format type (console, detailed, json)
            log_file: Optional log file path
            enable_json: Enable JSON structured logging
            
        Returns:
            Configured logger instance
        """
        
        # Define log formats
        formats = {
            'console': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'detailed': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
            'simple': '%(levelname)s: %(message)s'
        }
        
        # Create formatters
        console_formatter = logging.Formatter(
            formats.get(log_format, formats['console']),
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        json_formatter = JSONFormatter()
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        if enable_json:
            console_handler.setFormatter(json_formatter)
        else:
            console_handler.setFormatter(console_formatter)
        
        root_logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            # Ensure log directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, log_level.upper()))
            
            if enable_json:
                file_handler.setFormatter(json_formatter)
            else:
                detailed_formatter = logging.Formatter(
                    formats['detailed'],
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(detailed_formatter)
            
            root_logger.addHandler(file_handler)
        
        # Create telemetry-specific logger
        telemetry_logger = logging.getLogger('telemetry')
        
        return telemetry_logger
    
    @staticmethod
    def create_operation_logger(operation_name: str) -> logging.Logger:
        """Create a logger for specific operations with context."""
        return logging.getLogger(f'telemetry.{operation_name}')
    
    @staticmethod
    def log_performance_metrics(
        logger: logging.Logger,
        operation: str,
        duration: float,
        success: bool,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log performance metrics in a structured format."""
        metrics = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'success': success,
            'performance_metric': True
        }
        
        if additional_data:
            metrics.update(additional_data)
        
        if success:
            logger.info(f"Operation completed: {operation}", extra=metrics)
        else:
            logger.warning(f"Operation failed: {operation}", extra=metrics)
    
    @staticmethod
    def log_telemetry_collection(
        logger: logging.Logger,
        target: str,
        collected_fields: int,
        collection_time: float,
        errors: Optional[List[str]] = None
    ):
        """Log telemetry collection results."""
        collection_data = {
            'target': target,
            'collected_fields': collected_fields,
            'collection_time_ms': round(collection_time * 1000, 2),
            'telemetry_collection': True
        }
        
        if errors:
            collection_data['errors'] = errors
            logger.warning(f"Telemetry collection completed with errors for {target}", extra=collection_data)
        else:
            logger.info(f"Telemetry collection successful for {target}", extra=collection_data)


class ServiceHealthLogger:
    """Specialized logger for service health monitoring."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_service_start(self, service_name: str, config: Dict[str, Any]):
        """Log service startup."""
        startup_data = {
            'service_name': service_name,
            'config': config,
            'event_type': 'service_start'
        }
        self.logger.info(f"Service starting: {service_name}", extra=startup_data)
    
    def log_service_stop(self, service_name: str, reason: str = "normal"):
        """Log service shutdown."""
        shutdown_data = {
            'service_name': service_name,
            'shutdown_reason': reason,
            'event_type': 'service_stop'
        }
        self.logger.info(f"Service stopping: {service_name}", extra=shutdown_data)
    
    def log_health_check(self, status: str, details: Dict[str, Any]):
        """Log health check results."""
        health_data = {
            'health_status': status,
            'health_details': details,
            'event_type': 'health_check'
        }
        
        if status == 'healthy':
            self.logger.info("Service health check passed", extra=health_data)
        else:
            self.logger.error("Service health check failed", extra=health_data)
    
    def log_database_connection(self, database: str, status: str, details: Optional[Dict] = None):
        """Log database connection status."""
        db_data = {
            'database': database,
            'connection_status': status,
            'event_type': 'database_connection'
        }
        
        if details:
            db_data.update(details)
        
        if status == 'connected':
            self.logger.info(f"Database connection established: {database}", extra=db_data)
        else:
            self.logger.error(f"Database connection failed: {database}", extra=db_data)


# Default logging configuration
DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            '()': JSONFormatter,
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'detailed',
            'filename': 'logs/telemetry.log',
            'mode': 'a',
        }
    },
    'loggers': {
        'telemetry': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'telemetry.network': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'telemetry.database': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['console']
    }
}


def setup_production_logging():
    """Set up production-ready logging configuration."""
    return TelemetryLogger.setup_logging(
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        log_format='detailed',
        log_file='logs/network_telemetry.log',
        enable_json=os.getenv('LOG_FORMAT', '').lower() == 'json'
    )


def setup_development_logging():
    """Set up development logging configuration."""
    return TelemetryLogger.setup_logging(
        log_level='DEBUG',
        log_format='console',
        log_file='logs/telemetry_dev.log',
        enable_json=False
    )