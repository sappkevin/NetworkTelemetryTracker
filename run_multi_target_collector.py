#!/usr/bin/env python3
"""
Collect telemetry data for one or more FQDNs, as specified in the environment variable TARGET_FQDNS (comma-separated).
Falls back to TARGET_FQDN or 'google.com' if not set.
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, 'src')

from src.config import Config
from src.telemetry import NetworkTelemetry

async def collect_for_targets(targets):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info(f"Collecting telemetry data for targets: {targets}")
    logger.info("=" * 50)
    for i, target in enumerate(targets):
        try:
            logger.info(f"Collecting data for {target} ({i+1}/{len(targets)})")
            os.environ['TARGET_FQDN'] = target
            config = Config()
            telemetry = NetworkTelemetry(config)
            if await telemetry.initialize():
                success = await telemetry.collect_and_store_metrics()
                if success:
                    logger.info(f"✅ Successfully collected data for {target}")
                else:
                    logger.warning(f"⚠️ Failed to collect data for {target}")
                await telemetry.cleanup()
            else:
                logger.error(f"❌ Failed to initialize telemetry for {target}")
            if i < len(targets) - 1:
                await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Error collecting data for {target}: {e}")
    logger.info("All target data collection complete!")

if __name__ == "__main__":
    # Read targets from environment
    fqdn_env = os.getenv('TARGET_FQDNS')
    if fqdn_env:
        targets = [t.strip() for t in fqdn_env.split(',') if t.strip()]
    else:
        single = os.getenv('TARGET_FQDN', 'google.com')
        targets = [single]
    asyncio.run(collect_for_targets(targets)) 