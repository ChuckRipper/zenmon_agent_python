#!/usr/bin/env python3
"""
ZenMon Agent v2.0 - Professional Python Implementation
Author: Cezary Kalinowski
Description: Production-ready agent for collecting system metrics with Bearer token authentication

UC30: System resource monitoring (CPU, Memory, Disk, Network Response Time)
UC31: Secure data transmission to ZenMon API with JWT authentication
"""

import json # JSON serialization for metrics
import time # Time management for intervals and delays
import sys # System operations and command-line arguments
import os # System operations for file handling and platform detection
import platform # Platform detection for cross-compatibility
import requests # HTTP requests for API communication
import psutil # System performance metrics collection
import logging # Professional logging system
import signal # Signal handling for graceful shutdown
import shutil # Disk usage statistics
import hashlib # Secure password hashing
from datetime import datetime, timedelta # Date and time management
from typing import Dict, List, Optional, Any # Type hints for better code clarity
from dataclasses import dataclass # Data classes for configuration and token management
from logging.handlers import RotatingFileHandler # Rotating file handler for log files

# region Configuration Classes

@dataclass
class AgentConfig:
    """
    Agent configuration parameters
    """
    api_url: str
    host_id: int
    login: str
    password: str
    collection_interval: int = 120
    timeout: int = 30
    token_refresh_margin: int = 300  # 5 minutes before expiration
    enable_cpu_monitoring: bool = True
    enable_ram_monitoring: bool = True
    enable_disk_monitoring: bool = True
    enable_network_monitoring: bool = True

    def update_from_api(self, api_config: Dict[str, Any]) -> bool:
        """
        Aktualizuj konfigurację danymi z API
        
        Returns:
            bool: True if any configuration changed
        """
        # Store old values
        old_interval = self.collection_interval
        old_cpu = self.enable_cpu_monitoring
        old_ram = self.enable_ram_monitoring
        old_disk = self.enable_disk_monitoring
        old_network = self.enable_network_monitoring
        
        # Update values from API
        self.collection_interval = api_config.get('data_collection_interval', 120)
        self.enable_cpu_monitoring = api_config.get('enable_cpu_monitoring', True)
        self.enable_ram_monitoring = api_config.get('enable_ram_monitoring', True)
        self.enable_disk_monitoring = api_config.get('enable_disk_monitoring', True)
        self.enable_network_monitoring = api_config.get('enable_network_monitoring', True)
        
        # Check if anything changed
        config_changed = (
            old_interval != self.collection_interval or
            old_cpu != self.enable_cpu_monitoring or
            old_ram != self.enable_ram_monitoring or
            old_disk != self.enable_disk_monitoring or
            old_network != self.enable_network_monitoring
        )
        
        return config_changed

@dataclass
class AuthToken:
    """
    JWT authentication token data
    """
    token: str
    expires_at: datetime
    user_id: int
    username: str

# endregion

# region Logger

class AgentLogger:
    """
    Professional logging system with DEBUG visibility
    """
    
    def __init__(self, log_level: str = "DEBUG"):  # Changed default to DEBUG
        """
        Initialize logger
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.logger = logging.getLogger('ZenMonAgent')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Ensure logs directory exists
        # Check if running in container (has supervisor logs)
        if os.path.exists("/var/log/zenmon"):
            log_file = "/var/log/zenmon/zenmon_agent.log"  # Container path
        else:
            log_file = os.path.join("logs", "zenmon_agent.log")  # Local development
            os.makedirs("logs", exist_ok=True)
        
        # Console handler - NOW SHOWS DEBUG TOO
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)  # Changed from INFO to DEBUG
        
        # File handler - already DEBUG
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Enhanced formatter for better readability
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers if not already present
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
            
        # Log the logging configuration
        self.info(f"Logger initialized - Level: {log_level}, Console: DEBUG, File: DEBUG")
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)

# endregion

# region Authentication & Token Management

class TokenManager:
    """
    JWT token authentication manager with smart refresh
    """
    
    def __init__(self, config: AgentConfig, logger: AgentLogger):
        """
        Initialize token manager
        
        Args:
            config: Agent configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.current_token: Optional[AuthToken] = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': f'ZenMon-Agent-Python/2.0'
        })
    
    def authenticate(self) -> bool:
        """
        Authenticate and obtain JWT token
        
        Returns:
            bool: True if authentication successful
        """
        try:
            url = f"{self.config.api_url}/login"
            payload = {
                "login": self.config.login,
                "password": self.config.password
            }
            
            self.logger.debug(f"Authentication attempt - URL: {url}, Login: {self.config.login}")
            
            response = self.session.post(url, json=payload, timeout=self.config.timeout)
            
            self.logger.debug(f"Authentication response - Status: {response.status_code}, Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                token_string = data['token']
                user_info = data['user']
                
                expires_at = datetime.now() + timedelta(minutes=480)
                
                self.current_token = AuthToken(
                    token=token_string,
                    expires_at=expires_at,
                    user_id=user_info['id'],
                    username=user_info['login']
                )
                
                self.session.headers['Authorization'] = f'Bearer {token_string}'
                
                self.logger.debug(f"JWT token acquired: {token_string[:20]}...{token_string[-10:]} (expires: {expires_at})")
                self.logger.debug(f"User info: ID={user_info['id']}, Role={user_info.get('role', 'N/A')}")
                self.logger.info(f"Authentication successful for: {user_info['login']}")
                return True
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', 'Unknown error')
                    self.logger.error(f"Authentication failed: HTTP {response.status_code} - {error_message}")
                    self.logger.debug(f"Error response body: {error_data}")
                except:
                    self.logger.error(f"Authentication failed: HTTP {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            self.logger.error(f"Authentication request failed: {str(e)}")
            self.logger.debug(f"Request exception details: {type(e).__name__}: {str(e)}")
            return False
        except KeyError as e:
            self.logger.error(f"Authentication response missing required field: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Authentication unexpected error: {str(e)}")
            self.logger.debug(f"Exception details: {type(e).__name__}: {str(e)}")
            return False
    
    def is_token_valid(self) -> bool:
        """
        Check if current token is valid and not expiring soon
        
        Returns:
            bool: True if token is valid
        """
        if not self.current_token:
            return False
        
        time_until_expiry = self.current_token.expires_at - datetime.now()
        return time_until_expiry.total_seconds() > self.config.token_refresh_margin
    
    def refresh_token_if_needed(self) -> bool:
        """
        Refresh token if expiring within margin
        
        Returns:
            bool: True if token is valid after refresh attempt
        """
        if not self.current_token:
            self.logger.debug("No current token, initiating authentication")
            return self.authenticate()
        
        time_until_expiry = self.current_token.expires_at - datetime.now()
        minutes_left = time_until_expiry.total_seconds() / 60
        
        self.logger.debug(f"Token status check - Minutes until expiry: {minutes_left:.1f}, Refresh margin: {self.config.token_refresh_margin/60:.1f}")
        
        if minutes_left <= (self.config.token_refresh_margin / 60):
            self.logger.info(f"Token expires in {int(minutes_left)} minutes, refreshing")
            self.logger.debug(f"Current token: {self.current_token.token[:20]}...{self.current_token.token[-10:]}")
            return self.authenticate()
        
        self.logger.debug(f"Token still valid for {minutes_left:.1f} minutes")
        return True

# endregion

# region Metrics Collectors

class SystemMetricsCollector:
    """
    System performance metrics collector (UC30)
    """
    
    def __init__(self, config: AgentConfig, logger: AgentLogger, api_client=None):
        """
        Initialize metrics collector
        
        Args:
            config: Agent configuration
            logger: Logger instance
            api_client: API client for configuration (optional)
        """
        self.config = config
        self.logger = logger
        self.hostname = platform.node()
        self.api_client = api_client

    def collect_cpu_metric(self) -> Optional[Dict[str, Any]]:
        """
        Collect CPU utilization percentage using high-frequency sampling
        Matches Task Manager measurement methodology
        
        Returns:
            Optional[Dict[str, Any]]: CPU metric data or None if failed
        """
        try:
            self.logger.debug("Collecting CPU metric using high-frequency sampling...")
            start_time = time.time()
            
            # Method 1: High-frequency sampling (Task Manager style)
            self.logger.debug("CPU Method 1: High-frequency sampling (10 samples)")
            psutil.cpu_percent()  # Initialize baseline
            cpu_samples = []
            for i in range(10):
                sample = psutil.cpu_percent(interval=0.1)  # 100ms intervals
                cpu_samples.append(sample)
                self.logger.debug(f"CPU sample {i+1}: {sample:.1f}%")
            
            cpu_percent_hf = sum(cpu_samples) / len(cpu_samples)
            
            # Method 2: Short interval measurement
            self.logger.debug("CPU Method 2: Short interval (0.5s)")
            cpu_percent_short = psutil.cpu_percent(interval=0.5)
            
            # Method 3: Per-CPU with shorter interval
            self.logger.debug("CPU Method 3: Per-CPU short interval")
            cpu_percent_per_cpu = psutil.cpu_percent(interval=0.3, percpu=True)
            cpu_percent_percpu = sum(cpu_percent_per_cpu) / len(cpu_percent_per_cpu) if cpu_percent_per_cpu else 0
            
            # Method 4: Burst sampling (capture spikes)
            self.logger.debug("CPU Method 4: Burst sampling")
            burst_samples = []
            for i in range(5):
                burst_sample = psutil.cpu_percent(interval=0.05)  # 50ms very fast
                burst_samples.append(burst_sample)
            cpu_percent_burst = max(burst_samples)  # Take highest from burst
            
            # Choose method that captures dynamic load best
            cpu_values = [cpu_percent_hf, cpu_percent_short, cpu_percent_percpu, cpu_percent_burst]
            
            # Weighted average favoring higher values (spikes are important)
            weights = [0.4, 0.2, 0.2, 0.2]  # High-frequency gets most weight
            cpu_percent_weighted = sum(val * weight for val, weight in zip(cpu_values, weights))
            
            # Also calculate max for comparison
            cpu_percent_max = max(cpu_values)
            
            # Choose the weighted average (more stable than max, more accurate than simple average)
            cpu_percent = cpu_percent_weighted
            
            # System information
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)
            
            collection_time = time.time() - start_time
            
            self.logger.debug(f"CPU high-frequency samples: {[f'{x:.1f}%' for x in cpu_samples]}")
            self.logger.debug(f"CPU burst samples: {[f'{x:.1f}%' for x in burst_samples]}")
            self.logger.debug(f"CPU measurement methods - HF: {cpu_percent_hf:.1f}%, Short: {cpu_percent_short:.1f}%, PerCPU: {cpu_percent_percpu:.1f}%, Burst: {cpu_percent_burst:.1f}%")
            self.logger.debug(f"CPU final values - Weighted: {cpu_percent_weighted:.1f}%, Max: {cpu_percent_max:.1f}%, Chosen: {cpu_percent:.1f}%")
            self.logger.debug(f"Per-CPU values: {[f'{x:.1f}%' for x in cpu_percent_per_cpu[:8]]}")
            
            # Validation - this should now be much closer to Task Manager
            if cpu_percent < 5.0:
                self.logger.warning(f"CPU usage: {cpu_percent:.1f}% - may still be underestimated compared to Task Manager")
            elif cpu_percent >= 15.0:
                self.logger.info(f"CPU usage: {cpu_percent:.1f}% - good correlation with Task Manager expected")
            
            metric_data = {
                'host_id': self.config.host_id,
                'metric_type_id': 1,
                'value': round(cpu_percent, 2),
                'timestamp': datetime.now().isoformat(),
                'additional_info': {
                    'hostname': self.hostname,
                    'cpu_count_logical': cpu_count_logical,
                    'cpu_count_physical': cpu_count_physical,
                    'cpu_cores_ratio': round(cpu_count_logical / cpu_count_physical, 1) if cpu_count_physical > 0 else 1,
                    'collection_time_seconds': round(collection_time, 3),
                    'measurement_methods': {
                        'high_frequency_avg': round(cpu_percent_hf, 2),
                        'short_interval': round(cpu_percent_short, 2),
                        'percpu_short': round(cpu_percent_percpu, 2),
                        'burst_peak': round(cpu_percent_burst, 2),
                        'weighted_average': round(cpu_percent_weighted, 2),
                        'max_value': round(cpu_percent_max, 2),
                        'final_chosen': round(cpu_percent, 2)
                    },
                    'sampling_details': {
                        'hf_samples': [round(x, 1) for x in cpu_samples],
                        'burst_samples': [round(x, 1) for x in burst_samples],
                        'per_cpu_values': [round(x, 1) for x in cpu_percent_per_cpu[:16]]
                    },
                    'methodology': 'high_frequency_weighted_sampling'
                }
            }
            
            self.logger.debug(f"CPU metric prepared: {cpu_percent:.2f}% (HF weighted sampling)")
            return metric_data
            
        except psutil.Error as e:
            self.logger.error(f"CPU metric collection failed (psutil error): {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"CPU metric collection failed: {str(e)}")
            return None
    
    def collect_memory_metric(self) -> Optional[Dict[str, Any]]:
        """
        Collect memory utilization percentage
        
        Returns:
            Optional[Dict[str, Any]]: Memory metric data or None if failed
        """
        try:
            self.logger.debug("Collecting memory metric...")
            start_time = time.time()
            
            memory = psutil.virtual_memory()
            total_gb = round(memory.total / (1024**3), 2)
            available_gb = round(memory.available / (1024**3), 2)
            used_gb = round((memory.total - memory.available) / (1024**3), 2)
            
            collection_time = time.time() - start_time
            self.logger.debug(f"Memory metric collected - Usage: {memory.percent}%, Total: {total_gb}GB, Used: {used_gb}GB, Available: {available_gb}GB, Collection time: {collection_time:.3f}s")
            
            metric_data = {
                'host_id': self.config.host_id,
                'metric_type_id': 2,  # ✅ RAM = 2 (correct)
                'value': round(memory.percent, 2),
                'timestamp': datetime.now().isoformat(),
                'additional_info': {
                    'hostname': self.hostname,
                    'total_gb': total_gb,
                    'available_gb': available_gb,
                    'used_gb': used_gb,
                    'collection_time_seconds': round(collection_time, 3)
                }
            }
            
            self.logger.debug(f"Memory metric data: {metric_data}")
            return metric_data
            
        except psutil.Error as e:
            self.logger.error(f"Memory metric collection failed (psutil error): {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Memory metric collection failed: {str(e)}")
            return None
    
    # def collect_disk_metric(self) -> Optional[Dict[str, Any]]:
    #     """
    #     Collect disk utilization percentage
        
    #     Returns:
    #         Optional[Dict[str, Any]]: Disk metric data or None if failed
    #     """
    #     try:
    #         self.logger.debug("Collecting disk metric...")
    #         start_time = time.time()
            
    #         path = 'C:\\' if platform.system() == 'Windows' else '/'
    #         self.logger.debug(f"Checking disk usage for path: {path}")
            
    #         disk_usage = shutil.disk_usage(path)
    #         total = disk_usage.total
    #         used = total - disk_usage.free
    #         percent = (used / total) * 100 if total > 0 else 0
            
    #         total_gb = round(total / (1024**3), 2)
    #         used_gb = round(used / (1024**3), 2)
    #         free_gb = round(disk_usage.free / (1024**3), 2)
            
    #         collection_time = time.time() - start_time
    #         self.logger.debug(f"Disk metric collected - Usage: {percent:.2f}%, Total: {total_gb}GB, Used: {used_gb}GB, Free: {free_gb}GB, Collection time: {collection_time:.3f}s")
            
    #         metric_data = {
    #             'host_id': self.config.host_id,
    #             'metric_type_id': 3,
    #             'value': round(percent, 2),
    #             'timestamp': datetime.now().isoformat(),
    #             'additional_info': {
    #                 'hostname': self.hostname,
    #                 'path': path,
    #                 'total_gb': total_gb,
    #                 'used_gb': used_gb,
    #                 'free_gb': free_gb
    #             }
    #         }
            
    #         self.logger.debug(f"Disk metric data: {metric_data}")
    #         return metric_data
            
    #     except OSError as e:
    #         self.logger.error(f"Disk metric collection failed (OS error): {str(e)}")
    #         self.logger.debug(f"OS error details: {type(e).__name__}: {str(e)}")
    #         return None
    #     except Exception as e:
    #         self.logger.error(f"Disk metric collection failed: {str(e)}")
    #         self.logger.debug(f"Exception details: {type(e).__name__}: {str(e)}")
    #         return None
    
    def collect_network_metric(self, health_check_url: str) -> Optional[Dict[str, Any]]:
        """
        Collect network response time metric
        
        Args:
            health_check_url: URL to test network connectivity
            
        Returns:
            Optional[Dict[str, Any]]: Network metric data or None if failed
        """
        try:
            self.logger.debug(f"Collecting network metric - Testing: {health_check_url}")
            start_time = time.time()
            
            response = requests.get(health_check_url, timeout=10)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            collection_time = time.time() - start_time
            self.logger.debug(f"Network metric collected - Response time: {response_time_ms}ms, HTTP status: {response.status_code}, Collection time: {collection_time:.3f}s")
            
            metric_data = {
                'host_id': self.config.host_id,
                'metric_type_id': 3,  # ✅ FIXED: Network = 3 (was 4)
                'value': float(response_time_ms),
                'timestamp': datetime.now().isoformat(),
                'additional_info': {
                    'hostname': self.hostname,
                    'test_url': health_check_url,
                    'http_status': response.status_code,
                    'collection_time_seconds': round(collection_time, 3)
                }
            }
            
            self.logger.debug(f"Network metric data: {metric_data}")
            return metric_data
            
        except requests.Timeout:
            self.logger.warning(f"Network metric collection - timeout after 10s for {health_check_url}")
            return {
                'host_id': self.config.host_id,
                'metric_type_id': 3,  # ✅ FIXED: Network = 3 (was 4)
                'value': 10000.0,  # 10 second timeout
                'timestamp': datetime.now().isoformat(),
                'additional_info': {
                    'hostname': self.hostname,
                    'test_url': health_check_url,
                    'error': 'timeout',
                    'collection_time_seconds': 10.0
                }
            }
        except Exception as e:
            self.logger.error(f"Network metric collection failed: {str(e)}")
            return None
    
    def collect_storage_metrics(self) -> List[Dict[str, Any]]:
        """
        Collect storage metrics for all mounted drives/directories
        UC30: Enhanced storage monitoring with multiple drives
        
        Returns:
            List[Dict[str, Any]]: List of storage metrics for each drive/directory
        """
        storage_metrics = []
        
        try:
            self.logger.debug("Collecting storage metrics for all drives/directories...")
            
            if platform.system() == 'Windows':
                # Windows: Get all drive letters
                drives = self._get_windows_drives()
                base_metric_type_id = 4  # Storage starts from ID 4
                
                for i, drive in enumerate(drives):
                    metric = self._collect_single_storage_metric(
                        path=drive,
                        metric_type_id=base_metric_type_id + i,
                        drive_name=drive.replace(':', '')
                    )
                    if metric:
                        storage_metrics.append(metric)
                        
            else:
                # Linux/Unix: Monitor key directories
                # Try to get directories from API with fallback to defaults
                fallback_directories = ['/root', '/var', '/tmp', '/home', '/usr']
                
                try:
                    if self.api_client:
                        api_directories = self.api_client.get_monitored_directories()
                        if api_directories and len(api_directories) > 0:
                            directories = api_directories
                            self.logger.info(f"📁 Using API directories: {directories}")
                        else:
                            directories = fallback_directories
                            self.logger.warning(f"📁 API returned empty list, using fallback: {directories}")
                    else:
                        directories = fallback_directories
                        self.logger.warning(f"📁 No API client, using fallback: {directories}")
                except Exception as e:
                    directories = fallback_directories
                    self.logger.error(f"📁 API error: {e}, using fallback: {directories}")
                
                base_metric_type_id = 4  # Storage starts from ID 4
                
                for i, directory in enumerate(directories):
                    if os.path.exists(directory):
                        metric = self._collect_single_storage_metric(
                            path=directory,
                            metric_type_id=base_metric_type_id + i,
                            drive_name=directory.replace('/', '_').strip('_')
                        )
                        if metric:
                            storage_metrics.append(metric)
            
            self.logger.debug(f"Storage metrics collected: {len(storage_metrics)} drives/directories")
            return storage_metrics
            
        except Exception as e:
            self.logger.error(f"Storage metrics collection failed: {str(e)}")
            return []

    def _get_windows_drives(self) -> List[str]:
        """
        Get list of available Windows drive letters
        
        Returns:
            List[str]: List of drive letters (e.g., ['C:', 'D:', 'E:'])
        """
        drives = []
        try:
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:"
                if os.path.exists(drive + "\\"):
                    drives.append(drive)
            return drives
        except Exception as e:
            self.logger.warning(f"Failed to enumerate Windows drives: {str(e)}")
            return ['C:']  # Fallback to C: drive

    def _collect_single_storage_metric(self, path: str, metric_type_id: int, drive_name: str) -> Optional[Dict[str, Any]]:
        """
        Collect storage metric for a single path
        
        Args:
            path: Path to collect metrics for
            metric_type_id: Unique metric type ID for this storage location
            drive_name: Human-readable name for the drive/directory
            
        Returns:
            Optional[Dict[str, Any]]: Storage metric data or None if failed
        """
        try:
            start_time = time.time()
            
            # Get disk usage
            usage = shutil.disk_usage(path)
            total_gb = round(usage.total / (1024**3), 2)
            free_gb = round(usage.free / (1024**3), 2)
            used_gb = round((usage.total - usage.free) / (1024**3), 2)
            used_percent = round((used_gb / total_gb) * 100, 2) if total_gb > 0 else 0
            
            collection_time = time.time() - start_time
            self.logger.debug(f"Storage metric for {drive_name} ({path}) - Usage: {used_percent}%, Total: {total_gb}GB, Used: {used_gb}GB, Free: {free_gb}GB")
            
            metric_data = {
                'host_id': self.config.host_id,
                'metric_type_id': metric_type_id,  # ✅ FIXED: Storage = 4+ (was 3)
                'value': used_percent,
                'timestamp': datetime.now().isoformat(),
                'additional_info': {
                    'hostname': self.hostname,
                    'drive_name': drive_name,
                    'path': path,
                    'total_gb': total_gb,
                    'used_gb': used_gb,
                    'free_gb': free_gb,
                    'collection_time_seconds': round(collection_time, 3)
                }
            }
            
            return metric_data
            
        except PermissionError:
            self.logger.warning(f"Permission denied accessing {path}")
            return None
        except Exception as e:
            self.logger.error(f"Storage metric collection failed for {path}: {str(e)}")
            return None

    def collect_all_metrics(self, health_check_url: str) -> List[Dict[str, Any]]:
        """
        Collect all system metrics (UC30) with configuration-based filtering
        
        Args:
            health_check_url: URL for network health check
            
        Returns:
            List[Dict[str, Any]]: List of all collected metrics based on configuration
        """
        metrics = []
        collection_results = []
        
        self.logger.debug("Starting metrics collection with configuration filtering...")
        
        # CPU Metric (ID: 1)
        if self.config.enable_cpu_monitoring:
            cpu_metric = self.collect_cpu_metric()
            if cpu_metric:
                metrics.append(cpu_metric)
                collection_results.append("CPU: ✓")
            else:
                collection_results.append("CPU: ✗")
        else:
            collection_results.append("CPU: disabled")
        
        # Memory Metric (ID: 2)
        if self.config.enable_ram_monitoring:
            memory_metric = self.collect_memory_metric()
            if memory_metric:
                metrics.append(memory_metric)
                collection_results.append("RAM: ✓")
            else:
                collection_results.append("RAM: ✗")
        else:
            collection_results.append("RAM: disabled")
        
        # Network Metric (ID: 3)
        if self.config.enable_network_monitoring:
            network_metric = self.collect_network_metric(health_check_url)
            if network_metric:
                metrics.append(network_metric)
                collection_results.append("Network: ✓")
            else:
                collection_results.append("Network: ✗")
        else:
            collection_results.append("Network: disabled")
        
        # Storage Metrics (ID: 4-53)
        if self.config.enable_disk_monitoring:
            storage_metrics = self.collect_storage_metrics()
            if storage_metrics:
                metrics.extend(storage_metrics)
                collection_results.append(f"Storage: ✓ ({len(storage_metrics)} drives)")
            else:
                collection_results.append("Storage: ✗")
        else:
            collection_results.append("Storage: disabled")
        
        enabled_count = sum([
            self.config.enable_cpu_monitoring,
            self.config.enable_ram_monitoring, 
            self.config.enable_network_monitoring,
            self.config.enable_disk_monitoring
        ])
        
        success_count = len(metrics)
        
        self.logger.debug(f"Metrics collection summary: {success_count} metrics collected from {enabled_count} enabled types - {', '.join(collection_results)}")
        
        if enabled_count == 0:
            self.logger.warning("All monitoring types are disabled")
        elif success_count == 0:
            self.logger.warning("No metrics collected successfully")
        else:
            self.logger.info(f"Metrics collection: {success_count} metrics from {enabled_count} enabled monitoring types")
        
        return metrics

# endregion

# region API Client

class AuthenticatedApiClient:
    """
    Secure API client with Bearer token authentication (UC31)
    """
    
    def __init__(self, config: AgentConfig, token_manager: TokenManager, logger: AgentLogger):
        """
        Initialize API client
        
        Args:
            config: Agent configuration
            token_manager: Token manager instance
            logger: Logger instance
        """
        self.config = config
        self.token_manager = token_manager
        self.logger = logger
    
    def send_metrics(self, metrics: List[Dict[str, Any]]) -> bool:
        """
        Send metrics to API endpoint with authentication
        
        Args:
            metrics: List of metrics to send
            
        Returns:
            bool: True if metrics sent successfully
        """
        if not metrics:
            self.logger.debug("No metrics to send, skipping transmission")
            return True
        
        self.logger.debug(f"Preparing to send {len(metrics)} metrics")
        
        if not self.token_manager.refresh_token_if_needed():
            self.logger.error("Token refresh failed, cannot send metrics")
            return False
        
        try:
            url = f"{self.config.api_url}/agent/metrics/batch"
            payload = {
                'metrics': metrics,
                'agent_info': {
                    'version': '2.0',
                    'platform': platform.system(),
                    'hostname': platform.node()
                }
            }
            
            self.logger.debug(f"Sending POST request to: {url}")
            self.logger.debug(f"Request payload size: {len(json.dumps(payload))} bytes")
            self.logger.debug(f"Authorization header: Bearer {self.token_manager.session.headers.get('Authorization', 'N/A')[7:27]}...")
            
            start_time = time.time()
            response = self.token_manager.session.post(
                url, json=payload, timeout=self.config.timeout
            )
            response_time = time.time() - start_time
            
            self.logger.debug(f"Response received - Status: {response.status_code}, Time: {response_time:.3f}s, Content-Length: {len(response.content)}")
            
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    self.logger.debug(f"Metrics sent successfully - Response: {response_data}")
                except:
                    self.logger.debug("Metrics sent successfully - Response not JSON")
                return True
                
            elif response.status_code == 401:
                self.logger.warning("Authentication failed (401), attempting token refresh")
                try:
                    error_data = response.json()
                    self.logger.debug(f"401 error response: {error_data}")
                except:
                    self.logger.debug(f"401 error response (non-JSON): {response.text}")
                    
                if self.token_manager.authenticate():
                    self.logger.debug("Token refresh successful, retrying metrics submission")
                    return self.send_metrics(metrics)
                else:
                    self.logger.error("Token refresh failed after 401 error")
                    return False
                    
            elif response.status_code == 422:
                try:
                    error_data = response.json()
                    self.logger.error(f"Validation error (422): {error_data}")
                except:
                    self.logger.error(f"Validation error (422): {response.text}")
                return False
                
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', 'Unknown error')
                    self.logger.error(f"Metrics submission failed: HTTP {response.status_code} - {error_message}")
                    self.logger.debug(f"Error response: {error_data}")
                except:
                    self.logger.error(f"Metrics submission failed: HTTP {response.status_code} - {response.text}")
                return False
                
        except requests.Timeout as e:
            self.logger.error(f"Metrics transmission timeout: {str(e)}")
            self.logger.debug(f"Timeout after {self.config.timeout}s")
            return False
        except requests.ConnectionError as e:
            self.logger.error(f"Metrics transmission connection error: {str(e)}")
            self.logger.debug(f"Connection error details: {type(e).__name__}: {str(e)}")
            return False
        except requests.RequestException as e:
            self.logger.error(f"Metrics transmission request error: {str(e)}")
            self.logger.debug(f"Request error details: {type(e).__name__}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Metrics transmission unexpected error: {str(e)}")
            self.logger.debug(f"Exception details: {type(e).__name__}: {str(e)}")
            return False
    
    def send_heartbeat(self) -> bool:
        """
        Send heartbeat to maintain connection status
        
        Returns:
            bool: True if heartbeat sent successfully
        """
        self.logger.debug("Preparing to send heartbeat")
        
        if not self.token_manager.refresh_token_if_needed():
            self.logger.error("Token refresh failed, cannot send heartbeat")
            return False
        
        try:
            url = f"{self.config.api_url}/agent/heartbeat/{self.config.host_id}"
            payload = {
                'timestamp': datetime.now().isoformat(),
                'status': 'online',
                'agent_version': '2.0'
            }
            
            self.logger.debug(f"Sending heartbeat to: {url}")
            self.logger.debug(f"Heartbeat payload: {payload}")
            
            start_time = time.time()
            response = self.token_manager.session.post(
                url, json=payload, timeout=self.config.timeout
            )
            response_time = time.time() - start_time
            
            self.logger.debug(f"Heartbeat response - Status: {response.status_code}, Time: {response_time:.3f}s")
            
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    self.logger.debug(f"Heartbeat successful - Response: {response_data}")
                except:
                    self.logger.debug("Heartbeat successful - Response not JSON")
                return True
            else:
                try:
                    error_data = response.json()
                    self.logger.warning(f"Heartbeat failed: HTTP {response.status_code} - {error_data}")
                except:
                    self.logger.warning(f"Heartbeat failed: HTTP {response.status_code} - {response.text}")
                return False
            
        except requests.Timeout as e:
            self.logger.warning(f"Heartbeat timeout: {str(e)}")
            return False
        except requests.ConnectionError as e:
            self.logger.warning(f"Heartbeat connection error: {str(e)}")
            return False
        except requests.RequestException as e:
            self.logger.warning(f"Heartbeat request error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Heartbeat unexpected error: {str(e)}")
            self.logger.debug(f"Exception details: {type(e).__name__}: {str(e)}")
            return False

    def get_agent_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Pobierz konfigurację agenta z API
        """
        if not self.token_manager.refresh_token_if_needed():
            self.logger.error("Token refresh failed, cannot get configuration")
            return None
            
        try:
            url = f"{self.config.api_url}/agent/configuration/{self.config.host_id}"
            
            response = self.token_manager.session.get(url, timeout=self.config.timeout)
            
            if response.status_code == 200:
                config_data = response.json()
                self.logger.info(f"✅ Agent configuration loaded from API")
                return config_data
            else:
                self.logger.warning(f"⚠️ Failed to load configuration: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error loading agent configuration: {e}")
            return None
    
    def get_monitored_directories(self) -> List[str]:
        """
        Pobierz listę katalogów do monitorowania (Linux)
        """
        if not self.token_manager.refresh_token_if_needed():
            self.logger.error("Token refresh failed, cannot get directories")
            return ['/root', '/var', '/tmp', '/home', '/usr']  # fallback
            
        try:
            url = f"{self.config.api_url}/agent/monitored-directories/{self.config.host_id}"
            
            response = self.token_manager.session.get(url, timeout=self.config.timeout)
            
            if response.status_code == 200:
                data = response.json()
                directories = data.get('directories', [])
                fallback_used = data.get('directory_info', {}).get('fallback_used', False)
                
                if fallback_used:
                    self.logger.info(f"📁 Using fallback directories: {directories}")
                else:
                    self.logger.info(f"📁 Loaded {len(directories)} configured directories")
                
                return directories
            else:
                self.logger.warning(f"⚠️ Failed to load directories: {response.status_code}")
                return ['/root', '/var', '/tmp', '/home', '/usr']  # fallback
                
        except Exception as e:
            self.logger.error(f"❌ Error loading monitored directories: {e}")
            return ['/root', '/var', '/tmp', '/home', '/usr']  # fallback

# endregion

# region Main Agent Class

class ZenMonAgent:
    """
    Main ZenMon Agent with Bearer authentication and smart heartbeat timing
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize ZenMon Agent
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.logger = AgentLogger()
        self.token_manager = TokenManager(config, self.logger)
        self.api_client = AuthenticatedApiClient(config, self.token_manager, self.logger)
        self.metrics_collector = SystemMetricsCollector(config, self.logger, self.api_client)
        self.running = False
        self.last_heartbeat = datetime.now() - timedelta(minutes=10)  # Force first heartbeat
        self.heartbeat_interval = timedelta(minutes=5)  # 5 minute heartbeat
        self.last_config_refresh = datetime.now() - timedelta(minutes=15)  # Force first config refresh
        self.config_refresh_interval = timedelta(minutes=10)  # 10 minute config refresh
        
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
    
    def _shutdown_handler(self, signum, frame):
        """
        Handle shutdown signals gracefully
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Shutdown signal received: {signum}")
        self.running = False
    
    def start(self):
        """
        Start the monitoring agent
        """
        self.logger.info("ZenMon Agent v2.0 starting...")
        self.logger.info(f"Configuration: API={self.config.api_url}, Host={self.config.host_id}, Interval={self.config.collection_interval}s")
        
        if not self.token_manager.authenticate():
            self.logger.error("Initial authentication failed, cannot start agent")
            return
        
        self.running = True
        api_config = self.api_client.get_agent_configuration()
        if api_config:
            config_changed = self.config.update_from_api(api_config)
            if config_changed:
                self.logger.info(f"Collection interval updated to: {self.config.collection_interval}s")
        else:
            self.logger.warning("Using default configuration (API config failed to load)")
        
        self.logger.info("Agent started successfully - monitoring system metrics")
        
        while self.running:
            try:
                # Check if heartbeat is needed (every 5 minutes)
                if self._should_send_heartbeat():
                    self._send_heartbeat()
                
                # Check if config refresh is needed (every 10 minutes)
                if self._should_refresh_config():
                    self._refresh_config_if_needed()
                        
                # Collect and send metrics
                self._collect_and_send_metrics()
                        
                # Wait for next cycle
                self._wait_for_next_cycle()
                
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                self.logger.error(f"Agent cycle error: {str(e)}")
                self._wait_for_next_cycle()
        
        self.logger.info("ZenMon Agent stopped")
    
    def _should_send_heartbeat(self) -> bool:
        """
        Check if heartbeat should be sent based on time interval
        
        Returns:
            bool: True if heartbeat should be sent
        """
        time_since_last = datetime.now() - self.last_heartbeat
        return time_since_last >= self.heartbeat_interval
    
    def _send_heartbeat(self):
        """
        Send heartbeat to maintain connection status
        """
        try:
            self.logger.debug("Sending scheduled heartbeat")
            success = self.api_client.send_heartbeat()
            
            if success:
                self.last_heartbeat = datetime.now()
                self.logger.debug("Heartbeat sent successfully")
            else:
                self.logger.warning("Heartbeat failed")
                
        except Exception as e:
            self.logger.error(f"Heartbeat error: {str(e)}")
    
    def _collect_and_send_metrics(self):
        """
        Collect system metrics and send to API
        """
        try:
            health_check_url = f"{self.config.api_url}/public/health"
            metrics = self.metrics_collector.collect_all_metrics(health_check_url)
            
            if metrics:
                success = self.api_client.send_metrics(metrics)
                if success:
                    self.logger.info(f"Metrics transmission successful: {len(metrics)} metrics sent")
                else:
                    self.logger.warning(f"Metrics transmission failed for {len(metrics)} metrics")
            else:
                self.logger.warning("No metrics collected")
                
        except Exception as e:
            self.logger.error(f"Metrics collection error: {str(e)}")
    
    def _wait_for_next_cycle(self):
        """
        Wait for next collection cycle with graceful shutdown support
        """
        self.logger.debug(f"Waiting {self.config.collection_interval} seconds until next cycle")
        
        total_slept = 0
        sleep_step = 1
        
        while total_slept < self.config.collection_interval and self.running:
            time.sleep(sleep_step)
            total_slept += sleep_step
            
            # Log progress every 30 seconds
            if total_slept % 30 == 0 and total_slept < self.config.collection_interval:
                remaining = self.config.collection_interval - total_slept
                self.logger.debug(f"Still waiting - Slept: {total_slept}s, Remaining: {remaining}s")
        
        if not self.running:
            self.logger.debug("Sleep interrupted by shutdown signal")
        else:
            self.logger.debug(f"Wait completed - Total sleep time: {total_slept}s")

    def _should_refresh_config(self) -> bool:
            """
            Check if configuration should be refreshed based on time interval
            
            Returns:
                bool: True if config should be refreshed
            """
            time_since_last = datetime.now() - self.last_config_refresh
            return time_since_last >= self.config_refresh_interval
        
    def _refresh_config_if_needed(self):
        """
        Refresh agent configuration from API if needed
        """
        try:
            self.logger.debug("Checking if config refresh is needed")
            api_config = self.api_client.get_agent_configuration()
            
            if api_config:
                config_changed = self.config.update_from_api(api_config)
                self.last_config_refresh = datetime.now()
                
                if config_changed:
                    self.logger.info(f"Configuration updated: interval={self.config.collection_interval}s, CPU={self.config.enable_cpu_monitoring}, RAM={self.config.enable_ram_monitoring}, Network={self.config.enable_network_monitoring}, Disk={self.config.enable_disk_monitoring}")
                else:
                    self.logger.debug("Configuration checked - no changes")
            else:
                self.logger.warning("Config refresh failed - keeping current settings")
                
        except Exception as e:
            self.logger.error(f"Config refresh error: {str(e)}")

# endregion

# region Main Function

def main():
    """
    Main entry point
    """
    if len(sys.argv) != 5:
        print("Usage: python zenmon-agent-python-v2.0.py <API_URL> <HOST_ID> <LOGIN> <PASSWORD>")
        print("Example: python zenmon-agent-python-v2.0.py http://localhost:8001/api 10 admin admin123")
        sys.exit(1)
    
    try:
        api_url = sys.argv[1]
        host_id = int(sys.argv[2])
        login = sys.argv[3]
        password = sys.argv[4]
    except ValueError:
        print("Error: HOST_ID must be a valid integer")
        sys.exit(1)
    
    config = AgentConfig(
        api_url=api_url,
        host_id=host_id,
        login=login,
        password=password
    )
    
    agent = ZenMonAgent(config)
    agent.start()

if __name__ == "__main__":
    main()

# endregion

"""
FUNCTIONALITY SUMMARY:
✅ UC30: System metrics collection (CPU, Memory, Disk, Network Response Time)
✅ UC31: Secure data transmission with Bearer token authentication
✅ Professional code structure with C# regions
✅ Smart token refresh (5 minutes before expiration)
✅ Minimal bloatware and clean logging
✅ Graceful shutdown handling
✅ Cross-platform compatibility (Windows/Linux)

USAGE:
python zenmon-agent-python-v2.0.py http://localhost:8001/api 10 admin admin123
"""