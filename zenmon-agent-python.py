#!/usr/bin/env python3
"""
ZenMon Agent v1.0 - Python Implementation
Autor: ZenMon Development Team
Opis: Agent do zbierania metryk systemowych i wysyłania do ZenMon API

UC30: Zbieranie danych o zasobach systemu
UC31: Przesyłanie danych do aplikacji webowej
"""

import json
import time
import sys
import os
import platform
import requests
import psutil
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """
    Konfiguracja agenta
    """
    api_url: str
    host_id: int
    collection_interval: int = 120
    max_retries: int = 3
    retry_delay: int = 10
    timeout: int = 30

class ZenMonLogger:
    """
    Logger dla agenta ZenMon (Windows-compatible)
    """
    
    def __init__(self, log_level: str = "INFO"):
        """
        Inicjalizacja loggera
        
        Args:
            log_level: Poziom logowania (DEBUG, INFO, WARNING, ERROR)
        """
        self.logger = logging.getLogger('ZenMonAgent')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Console handler with UTF-8 encoding
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler('zenmon_agent.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter without problematic characters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """Log info message (remove problematic characters)"""
        clean_message = self._clean_message(message)
        self.logger.info(clean_message)
    
    def error(self, message: str):
        """Log error message (remove problematic characters)"""
        clean_message = self._clean_message(message)
        self.logger.error(clean_message)
    
    def warning(self, message: str):
        """Log warning message (remove problematic characters)"""
        clean_message = self._clean_message(message)
        self.logger.warning(clean_message)
    
    def debug(self, message: str):
        """Log debug message (remove problematic characters)"""
        clean_message = self._clean_message(message)
        self.logger.debug(clean_message)
    
    def _clean_message(self, message: str) -> str:
        """Remove problematic Unicode characters for Windows console"""
        # Replace emoji and special chars with text equivalents
        replacements = {
            '🚀': '[START]',
            '📡': '[API]',
            '🏠': '[HOST]',
            '⏱️': '[TIME]',
            '🔄': '[LOOP]',
            '📊': '[DATA]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARN]',
            '⏳': '[WAIT]',
            '🛑': '[STOP]'
        }
        
        for emoji, replacement in replacements.items():
            message = message.replace(emoji, replacement)
        
        return message

class SystemMetricsCollector:
    """
    Kolektor metryk systemowych (UC30: Zbieranie danych o zasobach systemu)
    """
    
    def __init__(self, logger: ZenMonLogger):
        """
        Inicjalizacja kolektora
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.system_info = self._get_system_info()
        self.logger.info(f"System info: {self.system_info['os']} {self.system_info['platform']}")
    
    def _get_system_info(self) -> Dict[str, Any]:
        """
        Pobieranie informacji o systemie
        
        Returns:
            Słownik z informacjami o systemie
        """
        return {
            'os': platform.system(),
            'platform': platform.platform(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'hostname': platform.node(),
            'python_version': platform.python_version()
        }
    
    def collect_cpu_metrics(self) -> Dict[str, Any]:
        """
        Zbieranie metryk CPU
        
        Returns:
            Słownik z metrykami CPU
        """
        try:
            # Pobieranie wykorzystania CPU (średnia z 1 sekundy)
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            additional_info = {
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'cpu_count_physical': psutil.cpu_count(logical=False),
                'system_info': self.system_info
            }
            
            if cpu_freq:
                additional_info['cpu_frequency'] = {
                    'current': cpu_freq.current,
                    'min': cpu_freq.min,
                    'max': cpu_freq.max
                }
            
            self.logger.debug(f"CPU metrics collected: {cpu_percent}%")
            
            return {
                'metric_name': 'CPU',
                'value': round(cpu_percent, 2),
                'additional_info': additional_info
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting CPU metrics: {e}")
            return None
    
    def collect_memory_metrics(self) -> Dict[str, Any]:
        """
        Zbieranie metryk pamięci RAM
        
        Returns:
            Słownik z metrykami RAM
        """
        try:
            memory = psutil.virtual_memory()
            
            additional_info = {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'free_gb': round(memory.free / (1024**3), 2),
                'cached_gb': round(getattr(memory, 'cached', 0) / (1024**3), 2),
                'system_info': self.system_info
            }
            
            self.logger.debug(f"RAM metrics collected: {memory.percent}%")
            
            return {
                'metric_name': 'RAM',
                'value': round(memory.percent, 2),
                'additional_info': additional_info
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting RAM metrics: {e}")
            return None
    
    def collect_disk_metrics(self, path: str = '/') -> Dict[str, Any]:
        """
        Zbieranie metryk dysku
        
        Args:
            path: Ścieżka do sprawdzenia (domyślnie '/' dla Linux, 'C:\\' dla Windows)
            
        Returns:
            Słownik z metrykami dysku
        """
        try:
            # Dostosowanie ścieżki do systemu operacyjnego
            if platform.system() == 'Windows' and path == '/':
                path = 'C:\\'
            
            disk = psutil.disk_usage(path)
            disk_percent = (disk.used / disk.total) * 100
            
            additional_info = {
                'path': path,
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'system_info': self.system_info
            }
            
            # Dodatkowe informacje o dyskach
            try:
                disk_partitions = []
                for partition in psutil.disk_partitions():
                    try:
                        partition_usage = psutil.disk_usage(partition.mountpoint)
                        disk_partitions.append({
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'total_gb': round(partition_usage.total / (1024**3), 2),
                            'used_percent': round((partition_usage.used / partition_usage.total) * 100, 2)
                        })
                    except PermissionError:
                        continue
                
                additional_info['all_partitions'] = disk_partitions
            except:
                pass
            
            self.logger.debug(f"Disk metrics collected: {disk_percent:.2f}%")
            
            return {
                'metric_name': 'Disk',
                'value': round(disk_percent, 2),
                'additional_info': additional_info
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting disk metrics: {e}")
            return None
    
    def collect_network_metrics(self, target_url: str) -> Dict[str, Any]:
        """
        Zbieranie metryk sieci (ping do serwera API)
        
        Args:
            target_url: URL do testowania połączenia
            
        Returns:
            Słownik z metrykami sieci
        """
        try:
            start_time = time.time()
            
            try:
                response = requests.get(target_url, timeout=5)
                response_time_ms = (time.time() - start_time) * 1000
                
                additional_info = {
                    'target_url': target_url,
                    'status_code': response.status_code,
                    'server_reachable': True,
                    'response_size_bytes': len(response.content),
                    'system_info': self.system_info
                }
                
                # Dodatkowe informacje o sieci
                try:
                    network_stats = psutil.net_io_counters()
                    additional_info['network_stats'] = {
                        'bytes_sent': network_stats.bytes_sent,
                        'bytes_recv': network_stats.bytes_recv,
                        'packets_sent': network_stats.packets_sent,
                        'packets_recv': network_stats.packets_recv
                    }
                except:
                    pass
                
                self.logger.debug(f"Network metrics collected: {response_time_ms:.2f}ms")
                
                return {
                    'metric_name': 'Network',
                    'value': round(response_time_ms, 2),
                    'additional_info': additional_info
                }
                
            except requests.RequestException as e:
                # Sieć niedostępna
                response_time_ms = 9999.0
                
                additional_info = {
                    'target_url': target_url,
                    'server_reachable': False,
                    'error': str(e),
                    'system_info': self.system_info
                }
                
                self.logger.warning(f"Network unreachable: {e}")
                
                return {
                    'metric_name': 'Network',
                    'value': response_time_ms,
                    'additional_info': additional_info
                }
                
        except Exception as e:
            self.logger.error(f"Error collecting network metrics: {e}")
            return None
    
    def collect_all_metrics(self, api_health_url: str) -> List[Dict[str, Any]]:
        """
        Zbieranie wszystkich metryk systemowych
        
        Args:
            api_health_url: URL health check API do testowania sieci
            
        Returns:
            Lista słowników z metrykami
        """
        metrics = []
        
        # CPU
        cpu_metric = self.collect_cpu_metrics()
        if cpu_metric:
            metrics.append(cpu_metric)
        
        # RAM
        ram_metric = self.collect_memory_metrics()
        if ram_metric:
            metrics.append(ram_metric)
        
        # Disk
        disk_metric = self.collect_disk_metrics()
        if disk_metric:
            metrics.append(disk_metric)
        
        # Network
        network_metric = self.collect_network_metrics(api_health_url)
        if network_metric:
            metrics.append(network_metric)
        
        self.logger.info(f"Collected {len(metrics)} metrics")
        return metrics

class ZenMonApiClient:
    """
    Klient API ZenMon (UC31: Przesyłanie danych do aplikacji webowej)
    """
    
    def __init__(self, config: AgentConfig, logger: ZenMonLogger):
        """
        Inicjalizacja klienta API
        
        Args:
            config: Konfiguracja agenta
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.api_url = config.api_url.rstrip('/')
        self.metric_types = {}
        self.session = requests.Session()
        
        # Headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': f'ZenMon-Agent-Python/1.0 ({platform.system()})'
        })
    
    def initialize(self) -> bool:
        """
        Inicjalizacja - pobranie typów metryk z API
        
        Returns:
            True jeśli inicjalizacja się powiodła
        """
        try:
            self.logger.info("Initializing API client...")
            
            # Test connection
            health_url = f'{self.api_url}/public/health'
            response = self.session.get(health_url, timeout=self.config.timeout)
            
            if response.status_code == 200:
                health_data = response.json()
                self.logger.info(f"Connected to ZenMon API v{health_data.get('version', 'unknown')}")
            else:
                self.logger.error(f"Health check failed: {response.status_code}")
                return False
            
            # Get metric types
            metric_types_url = f'{self.api_url}/public/metric-types'
            response = self.session.get(metric_types_url, timeout=self.config.timeout)
            
            if response.status_code == 200:
                data = response.json()
                for metric_type in data['data']:
                    self.metric_types[metric_type['metric_name']] = metric_type['metric_type_id']
                
                self.logger.info(f"Loaded {len(self.metric_types)} metric types: {list(self.metric_types.keys())}")
                return True
            else:
                self.logger.error(f"Failed to get metric types: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"API initialization failed: {e}")
            return False
    
    def send_metrics(self, metrics: List[Dict[str, Any]]) -> bool:
        """
        Wysyłanie metryk do API (batch)
        
        Args:
            metrics: Lista metryk z collect_all_metrics()
            
        Returns:
            True jeśli wysłanie się powiodło
        """
        if not metrics:
            self.logger.warning("No metrics to send")
            return True
        
        # Konwersja metryk do formatu API
        api_metrics = []
        timestamp = datetime.now().isoformat()
        
        for metric in metrics:
            metric_name = metric['metric_name']
            
            if metric_name not in self.metric_types:
                self.logger.warning(f"Unknown metric type: {metric_name}")
                continue
            
            api_metric = {
                'host_id': self.config.host_id,
                'metric_type_id': self.metric_types[metric_name],
                'value': metric['value'],
                'timestamp': timestamp,
                'additional_info': metric.get('additional_info', {})
            }
            api_metrics.append(api_metric)
        
        if not api_metrics:
            self.logger.warning("No valid metrics to send")
            return False
        
        # Wysyłanie z retry
        for attempt in range(self.config.max_retries):
            try:
                batch_url = f'{self.api_url}/public/metrics/batch'
                payload = {'metrics': api_metrics}
                
                response = self.session.post(
                    batch_url,
                    json=payload,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 201:
                    result = response.json()
                    self.logger.info(f"✅ Sent {result.get('count', len(api_metrics))} metrics successfully")
                    return True
                else:
                    self.logger.error(f"❌ Failed to send metrics: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error sending metrics (attempt {attempt + 1}): {e}")
            
            if attempt < self.config.max_retries - 1:
                self.logger.info(f"Retrying in {self.config.retry_delay} seconds...")
                time.sleep(self.config.retry_delay)
        
        self.logger.error(f"❌ Failed to send metrics after {self.config.max_retries} attempts")
        return False

class ZenMonAgent:
    """
    Główna klasa agenta ZenMon
    """
    
    def __init__(self, config: AgentConfig):
        """
        Inicjalizacja agenta
        
        Args:
            config: Konfiguracja agenta
        """
        self.config = config
        self.logger = ZenMonLogger()
        self.collector = SystemMetricsCollector(self.logger)
        self.api_client = ZenMonApiClient(config, self.logger)
        self.running = False
    
    def start(self) -> None:
        """
        Uruchomienie agenta
        """
        self.logger.info("[START] Starting ZenMon Agent v1.0")
        self.logger.info(f"[API] API URL: {self.config.api_url}")
        self.logger.info(f"[HOST] Host ID: {self.config.host_id}")
        self.logger.info(f"[TIME] Collection interval: {self.config.collection_interval}s")
        
        # Inicjalizacja API
        if not self.api_client.initialize():
            self.logger.error("[ERROR] Failed to initialize API client")
            sys.exit(1)
        
        self.logger.info("[LOOP] Starting metrics collection loop...")
        self.running = True
        
        try:
            while self.running:
                self._collect_and_send_metrics()
                self._wait_for_next_cycle()
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Received interrupt signal, stopping agent...")
            self.stop()
        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {e}")
            self.stop()
            sys.exit(1)
    
    def stop(self) -> None:
        """
        Zatrzymanie agenta
        """
        self.running = False
        self.logger.info("✅ ZenMon Agent stopped")
    
    def _collect_and_send_metrics(self) -> None:
        """
        Zbieranie i wysyłanie metryk (jeden cykl)
        """
        try:
            # Zbieranie metryk
            health_url = f'{self.config.api_url}/public/health'
            metrics = self.collector.collect_all_metrics(health_url)
            
            if metrics:
                # Wysyłanie metryk
                success = self.api_client.send_metrics(metrics)
                
                if success:
                    self.logger.info(f"📊 Cycle completed successfully ({len(metrics)} metrics)")
                else:
                    self.logger.error("❌ Failed to send metrics")
            else:
                self.logger.warning("⚠️  No metrics collected")
                
        except Exception as e:
            self.logger.error(f"❌ Error in collection cycle: {e}")
    
    def _wait_for_next_cycle(self) -> None:
        """
        Oczekiwanie do następnego cyklu
        """
        self.logger.info(f"⏳ Next collection in {self.config.collection_interval} seconds")
        time.sleep(self.config.collection_interval)

def main():
    """
    Funkcja główna
    """
    if len(sys.argv) != 3:
        print("Usage: python zenmon_agent.py <API_URL> <HOST_ID>")
        print("Example: python zenmon_agent.py http://localhost:8001/api 1")
        sys.exit(1)
    
    api_url = sys.argv[1]
    host_id = int(sys.argv[2])
    
    # Konfiguracja agenta
    config = AgentConfig(
        api_url=api_url,
        host_id=host_id,
        collection_interval=120,  # 2 minuty
        max_retries=3,
        retry_delay=10,
        timeout=30
    )
    
    # Uruchomienie agenta
    agent = ZenMonAgent(config)
    agent.start()

if __name__ == "__main__":
    main()

"""
INSTALACJA I URUCHOMIENIE:

1. Zainstaluj wymagane biblioteki:
   pip install psutil requests

2. Uruchom agenta:
   python zenmon_agent.py http://localhost:8001/api 1

3. Agent będzie:
   - Zbierać metryki CPU, RAM, Disk, Network co 120 sekund
   - Wysyłać dane na endpoint /api/public/metrics/batch
   - Logować do pliku zenmon_agent.log
   - Automatycznie retry przy błędach

FUNKCJONALNOŚCI:
✅ UC30: Zbieranie metryk systemowych (CPU, RAM, Disk, Network)
✅ UC31: Wysyłanie danych przez API (/public/metrics/batch)
✅ Retry mechanism przy błędach sieci
✅ Szczegółowe logowanie
✅ Dodatkowe informacje systemowe w additional_info
✅ Cross-platform (Windows/Linux)
✅ Health check connection
✅ Graceful shutdown (Ctrl+C)
"""