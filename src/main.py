"""
Network Telemetry Service - Main Entry Point

Simplified main service using the consolidated telemetry module.
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

from .config import Config
from .telemetry import NetworkTelemetry


class NetworkTelemetryService:
    """Main service orchestrator for network telemetry collection."""
    
    def __init__(self):
        self.config = Config()
        self.logger = self._setup_logging()
        self.telemetry: Optional[NetworkTelemetry] = None
        self.running = False
        
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for the service."""
        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, self.config.log_level))
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        try:
            os.makedirs('logs', exist_ok=True)
            file_handler = logging.FileHandler('logs/network_telemetry.log')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler: {e}")
        
        return logger
    
    async def initialize(self) -> bool:
        """Initialize all service components."""
        try:
            self.logger.info("Starting Network Telemetry Service initialization...")
            
            # Initialize telemetry system
            self.telemetry = NetworkTelemetry(self.config)
            if not await self.telemetry.initialize():
                self.logger.error("Failed to initialize telemetry system")
                return False
            
            # Test connectivity
            if not await self.telemetry.test_connectivity():
                self.logger.warning(f"Cannot reach target {self.config.target_fqdn}")
                return False
            
            self.logger.info("Service initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
    
    async def run_monitoring_cycle(self):
        """Execute a single monitoring cycle."""
        try:
            success = await self.telemetry.collect_and_store_metrics()
            
            if not success:
                self.logger.warning("Monitoring cycle failed")
                
        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")
    
    async def run(self):
        """Main service loop."""
        self.running = True
        self.logger.info("Network Telemetry Service started")
        
        # Initialize service first
        if not await self.initialize():
            self.logger.error("Failed to initialize service, exiting")
            return
        
        while self.running:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.telemetry:
                await self.telemetry.cleanup()
            self.logger.info("Service cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def stop(self):
        """Stop the service gracefully."""
        self.running = False
        self.logger.info("Service stop requested")


# Global service instance for signal handling
service_instance = None


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global service_instance
    if service_instance:
        service_instance.stop()


async def main():
    """Main function."""
    global service_instance
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    service_instance = NetworkTelemetryService()
    
    try:
        if not await service_instance.initialize():
            sys.exit(1)
        
        await service_instance.run()
        
    except Exception as e:
        logging.error(f"Service failed: {e}")
        sys.exit(1)
    
    finally:
        await service_instance.cleanup()


if __name__ == "__main__":
    asyncio.run(main())