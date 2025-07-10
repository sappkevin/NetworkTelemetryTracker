"""
Scaling and concurrency enhancements for Network Telemetry Service.

Provides connection pooling, async concurrency controls, circuit breakers,
and horizontal scaling utilities for high-availability deployments.
"""

import asyncio
import aiohttp
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import random
import json
from contextlib import asynccontextmanager
import weakref

from .config import Config
from .logging_config import TelemetryLogger


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 60          # Seconds before trying half-open
    success_threshold: int = 3          # Successes to close from half-open
    timeout: float = 10.0              # Request timeout in seconds


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pooling."""
    max_connections: int = 100          # Max connections per pool
    max_connections_per_host: int = 30  # Max per host
    keepalive_timeout: int = 30         # Keep connections alive
    connection_timeout: float = 10.0    # Connection timeout
    read_timeout: float = 30.0         # Read timeout


@dataclass
class ConcurrencyConfig:
    """Configuration for concurrency controls."""
    max_concurrent_targets: int = 50    # Max targets processed concurrently
    max_concurrent_operations: int = 100 # Max operations per target
    semaphore_timeout: float = 30.0     # Timeout for acquiring semaphore
    batch_size: int = 10               # Batch size for operations
    worker_pool_size: int = 20         # Number of worker tasks


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        """Initialize circuit breaker."""
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.logger = logging.getLogger(f'telemetry.circuit_breaker.{name}')
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info(f"Circuit breaker {self.name} attempting recovery")
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            await self._on_success()
            return result
            
        except Exception as e:
            await self._on_failure(e)
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    async def _on_success(self):
        """Handle successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.logger.info(f"Circuit breaker {self.name} closed (recovered)")
        
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset failure count on success
    
    async def _on_failure(self, exception: Exception):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.logger.warning(f"Circuit breaker {self.name} opened due to failures")
        
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
            self.logger.warning(f"Circuit breaker {self.name} reopened after failed recovery")
        
        self.logger.debug(f"Circuit breaker {self.name} failure: {exception}")


class ConnectionPool:
    """Enhanced connection pool for HTTP operations."""
    
    def __init__(self, config: ConnectionPoolConfig = None):
        """Initialize connection pool."""
        self.config = config or ConnectionPoolConfig()
        self.session = None
        self.logger = logging.getLogger('telemetry.connection_pool')
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Start the connection pool."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(
                total=None,
                connect=self.config.connection_timeout,
                sock_read=self.config.read_timeout
            )
            
            connector = aiohttp.TCPConnector(
                limit=self.config.max_connections,
                limit_per_host=self.config.max_connections_per_host,
                keepalive_timeout=self.config.keepalive_timeout,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            
            self.logger.info(f"Connection pool started with {self.config.max_connections} max connections")
    
    async def close(self):
        """Close the connection pool."""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("Connection pool closed")
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Perform GET request using pool."""
        if not self.session:
            await self.start()
        
        return await self.session.get(url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Perform POST request using pool."""
        if not self.session:
            await self.start()
        
        return await self.session.post(url, **kwargs)


class ConcurrencyController:
    """Controls concurrency and provides rate limiting."""
    
    def __init__(self, config: ConcurrencyConfig = None):
        """Initialize concurrency controller."""
        self.config = config or ConcurrencyConfig()
        self.target_semaphore = asyncio.Semaphore(self.config.max_concurrent_targets)
        self.operation_semaphore = asyncio.Semaphore(self.config.max_concurrent_operations)
        self.logger = logging.getLogger('telemetry.concurrency')
        
    @asynccontextmanager
    async def target_slot(self):
        """Acquire slot for target processing."""
        try:
            await asyncio.wait_for(
                self.target_semaphore.acquire(),
                timeout=self.config.semaphore_timeout
            )
            yield
        finally:
            self.target_semaphore.release()
    
    @asynccontextmanager
    async def operation_slot(self):
        """Acquire slot for operation processing."""
        try:
            await asyncio.wait_for(
                self.operation_semaphore.acquire(),
                timeout=self.config.semaphore_timeout
            )
            yield
        finally:
            self.operation_semaphore.release()
    
    async def run_batched(self, items: List, func: Callable, *args, **kwargs) -> List:
        """Run function on items in batches."""
        results = []
        batch_size = self.config.batch_size
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_tasks = []
            
            for item in batch:
                async with self.operation_slot():
                    task = asyncio.create_task(func(item, *args, **kwargs))
                    batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Small delay between batches to prevent overwhelming
            if i + batch_size < len(items):
                await asyncio.sleep(0.1)
        
        return results


class RetryPolicy:
    """Configurable retry policy with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, backoff_factor: float = 2.0):
        """Initialize retry policy."""
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger('telemetry.retry')
    
    async def execute(self, func: Callable, *args, **kwargs):
        """Execute function with retry policy."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    self.logger.error(f"All {self.max_retries} retry attempts failed")
                    raise
                
                delay = min(
                    self.base_delay * (self.backoff_factor ** attempt),
                    self.max_delay
                )
                
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0.1, 0.3) * delay
                total_delay = delay + jitter
                
                self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {total_delay:.2f}s: {e}")
                await asyncio.sleep(total_delay)
        
        raise last_exception


class WorkerPool:
    """Worker pool for processing tasks concurrently."""
    
    def __init__(self, worker_count: int = 10, queue_size: int = 1000):
        """Initialize worker pool."""
        self.worker_count = worker_count
        self.queue = asyncio.Queue(maxsize=queue_size)
        self.workers = []
        self.running = False
        self.logger = logging.getLogger('telemetry.worker_pool')
    
    async def start(self):
        """Start worker pool."""
        if self.running:
            return
        
        self.running = True
        self.workers = []
        
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        self.logger.info(f"Started worker pool with {self.worker_count} workers")
    
    async def stop(self):
        """Stop worker pool."""
        if not self.running:
            return
        
        self.running = False
        
        # Add sentinel values to wake up workers
        for _ in range(self.worker_count):
            await self.queue.put(None)
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.logger.info("Worker pool stopped")
    
    async def submit(self, func: Callable, *args, **kwargs) -> asyncio.Future:
        """Submit task to worker pool."""
        if not self.running:
            await self.start()
        
        future = asyncio.Future()
        task = (func, args, kwargs, future)
        
        await self.queue.put(task)
        return future
    
    async def _worker(self, name: str):
        """Worker coroutine."""
        self.logger.debug(f"Worker {name} started")
        
        while self.running:
            try:
                task = await self.queue.get()
                
                if task is None:  # Sentinel value
                    break
                
                func, args, kwargs, future = task
                
                try:
                    result = await func(*args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
                finally:
                    self.queue.task_done()
            
            except Exception as e:
                self.logger.error(f"Worker {name} error: {e}")
        
        self.logger.debug(f"Worker {name} stopped")


class ScalingManager:
    """Manages scaling configuration and provides scaling utilities."""
    
    def __init__(self, config: Config):
        """Initialize scaling manager."""
        self.config = config
        self.connection_pool = None
        self.concurrency_controller = None
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_policy = RetryPolicy()
        self.worker_pool = None
        self.logger = logging.getLogger('telemetry.scaling')
        
        # Load scaling configuration from environment
        self._load_scaling_config()
    
    def _load_scaling_config(self):
        """Load scaling configuration from environment variables."""
        import os
        
        # Connection pool config
        pool_config = ConnectionPoolConfig(
            max_connections=int(os.getenv('MAX_CONNECTIONS', '100')),
            max_connections_per_host=int(os.getenv('MAX_CONNECTIONS_PER_HOST', '30')),
            keepalive_timeout=int(os.getenv('KEEPALIVE_TIMEOUT', '30')),
            connection_timeout=float(os.getenv('CONNECTION_TIMEOUT', '10.0')),
            read_timeout=float(os.getenv('READ_TIMEOUT', '30.0'))
        )
        
        # Concurrency config
        concurrency_config = ConcurrencyConfig(
            max_concurrent_targets=int(os.getenv('MAX_CONCURRENT_TARGETS', '50')),
            max_concurrent_operations=int(os.getenv('MAX_CONCURRENT_OPERATIONS', '100')),
            batch_size=int(os.getenv('BATCH_SIZE', '10')),
            worker_pool_size=int(os.getenv('WORKER_POOL_SIZE', '20'))
        )
        
        # Circuit breaker config
        circuit_config = CircuitBreakerConfig(
            failure_threshold=int(os.getenv('CIRCUIT_FAILURE_THRESHOLD', '5')),
            recovery_timeout=int(os.getenv('CIRCUIT_RECOVERY_TIMEOUT', '60')),
            success_threshold=int(os.getenv('CIRCUIT_SUCCESS_THRESHOLD', '3')),
            timeout=float(os.getenv('CIRCUIT_TIMEOUT', '10.0'))
        )
        
        self.connection_pool = ConnectionPool(pool_config)
        self.concurrency_controller = ConcurrencyController(concurrency_config)
        self.circuit_breaker_config = circuit_config
        
        self.logger.info("Scaling configuration loaded")
    
    async def start(self):
        """Start scaling components."""
        await self.connection_pool.start()
        
        if not self.worker_pool:
            self.worker_pool = WorkerPool(
                worker_count=self.concurrency_controller.config.worker_pool_size
            )
            await self.worker_pool.start()
        
        self.logger.info("Scaling manager started")
    
    async def stop(self):
        """Stop scaling components."""
        if self.connection_pool:
            await self.connection_pool.close()
        
        if self.worker_pool:
            await self.worker_pool.stop()
        
        self.logger.info("Scaling manager stopped")
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, self.circuit_breaker_config)
        
        return self.circuit_breakers[name]
    
    async def execute_with_scaling(self, name: str, func: Callable, *args, **kwargs):
        """Execute function with all scaling features."""
        circuit_breaker = self.get_circuit_breaker(name)
        
        async def protected_func():
            return await self.retry_policy.execute(func, *args, **kwargs)
        
        return await circuit_breaker.call(protected_func)
    
    async def process_targets_concurrently(self, targets: List[str], 
                                         process_func: Callable) -> List:
        """Process multiple targets with concurrency control."""
        results = []
        
        async def process_target(target):
            async with self.concurrency_controller.target_slot():
                return await self.execute_with_scaling(
                    f"target_{target}", 
                    process_func, 
                    target
                )
        
        # Use worker pool for processing
        tasks = []
        for target in targets:
            future = await self.worker_pool.submit(process_target, target)
            tasks.append(future)
        
        # Wait for all tasks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300  # 5 minute timeout
            )
        except asyncio.TimeoutError:
            self.logger.error("Target processing timed out")
            results = [Exception("Timeout") for _ in targets]
        
        return results
    
    def get_scaling_metrics(self) -> Dict[str, Any]:
        """Get current scaling metrics."""
        metrics = {
            'circuit_breakers': {},
            'connection_pool': {
                'max_connections': self.connection_pool.config.max_connections,
                'session_active': self.connection_pool.session is not None
            },
            'concurrency': {
                'target_slots_available': self.concurrency_controller.target_semaphore._value,
                'operation_slots_available': self.concurrency_controller.operation_semaphore._value,
                'max_concurrent_targets': self.concurrency_controller.config.max_concurrent_targets,
                'max_concurrent_operations': self.concurrency_controller.config.max_concurrent_operations
            },
            'worker_pool': {
                'worker_count': self.worker_pool.worker_count if self.worker_pool else 0,
                'queue_size': self.worker_pool.queue.qsize() if self.worker_pool else 0,
                'running': self.worker_pool.running if self.worker_pool else False
            }
        }
        
        # Add circuit breaker states
        for name, breaker in self.circuit_breakers.items():
            metrics['circuit_breakers'][name] = {
                'state': breaker.state.value,
                'failure_count': breaker.failure_count,
                'success_count': breaker.success_count
            }
        
        return metrics