# ZenMon Agent - Python

**ZenMon Agent** to lekka aplikacja w języku Python, która zbiera metryki systemowe i wysyła je do aplikacji webowej ZenMon. Agent jest częścią systemu monitoringu ZenMon.

## 📋 Opis

Agent automatycznie wykrywa system operacyjny, zbiera kluczowe metryki (CPU, RAM, dysk, sieć) oraz monitoruje wskazane katalogi. Dane są wysyłane do API ZenMon przy użyciu uwierzytelniania Bearer token.

### Obsługiwane systemy operacyjne
- **Windows** (testowane na Windows 10/11)
- **Linux** (Ubuntu, CentOS, Debian, RHEL)
- **macOS** (podstawowe wsparcie)

## 🛠️ Użyte Technologie

- **Python 3.8+**
- **requests** - komunikacja HTTP z API
- **psutil** - zbieranie metryk systemowych
- **logging** - rejestrowanie zdarzeń
- **json** - serializacja danych
- **dataclasses** - struktury danych

## 📁 Struktura Projektu

```
zenmon_agent_python/
├── zenmon-agent-python-v1.0.py        # Agent podstawowy (v1.0)
├── zenmon-agent-python-v2.0.py        # Agent produkcyjny (v2.0)
├── docker-compose.test.yml             # Kontenery testowe Linux
├── docker-test/                        # Konfiguracje Docker
│   ├── alpine/
│   │   ├── Dockerfile                  # Alpine Linux container
│   │   └── supervisord.conf            # Supervisor config dla Alpine
│   ├── ubuntu/
│   │   ├── Dockerfile                  # Ubuntu 22.04 container
│   │   └── supervisord.conf            # Supervisor config dla Ubuntu
│   ├── rocky/
│   │   ├── Dockerfile                  # Rocky Linux 9 container
│   │   └── supervisord.conf            # Supervisor config dla Rocky
│   ├── health_server.py                # Health check server dla kontenerów
│   └── load_test.py                    # Load testing script
├── logs/                               # Katalog logów (git ignored)
│   └── .gitkeep                        # Zachowanie struktury w git
├── LICENSE.txt                         # Licencja MIT
├── zenmon_agent.log                    # Logi agenta (generowane)
└── README.md
```

## 🚀 Instrukcja Instalacji i Uruchomienia

### Wymagania
- **Python 3.8+**
- **pip** (menedżer pakietów Python)
- **PowerShell** (Windows) lub Terminal (Linux/macOS)
- **Działająca aplikacja ZenMon Laravel**

### 1. Klonowanie repozytorium
```bash
git clone https://github.com/ChuckRipper/zenmon_agent_python.git
cd zenmon_agent_python
```

### 2. Instalacja zależności Python
```bash
# Windows PowerShell
pip install psutil requests

# Linux/macOS
pip3 install psutil requests
```

**Uwaga**: Projekt nie zawiera pliku `requirements.txt` - instaluj zależności bezpośrednio jak powyżej.

### 3. Konfiguracja agenta

Edytuj parametry w pliku `zenmon-agent-python-v2.0.py`:

```python
# Konfiguracja agenta
API_URL = "http://localhost:8001/api"  # URL aplikacji Laravel
HOST_ID = 1                            # ID hosta w bazie danych
COLLECTION_INTERVAL = 120              # Interwał zbierania (sekundy)
```

### 4. Uruchomienie agenta

#### Windows (PowerShell)
```powershell
# Przejdź do katalogu projektu
cd zenmon_agent_python

# Uruchom agenta (Host ID = 1)
python zenmon-agent-python-v2.0.py
```

#### Linux/macOS
```bash
# Uruchom agenta
python3 zenmon-agent-python-v2.0.py

# Lub jako daemon (w tle)
nohup python3 zenmon-agent-python-v2.0.py &
```

## ⚙️ Konfiguracja

### Parametry konfiguracyjne
```python
@dataclass
class AgentConfig:
    api_url: str                    # URL API ZenMon
    host_id: int                    # ID hosta w bazie
    collection_interval: int = 120  # Interwał zbierania (sek)
    max_retries: int = 3            # Maksymalne próby wysyłki
    retry_delay: int = 10           # Opóźnienie między próbami
    timeout: int = 30               # Timeout HTTP
```

### Monitorowane katalogi (przykłady)

#### Windows
```python
MONITORED_DIRECTORIES = [
    "C:\\",                    # Katalog główny
    "C:\\Windows\\System32",   # System Windows
    "C:\\Program Files",       # Aplikacje
    "C:\\Users\\Public"        # Katalog użytkowników
]
```

#### Linux
```python
MONITORED_DIRECTORIES = [
    "/",                       # Root filesystem
    "/var/log",               # Logi systemowe
    "/tmp",                   # Pliki tymczasowe
    "/home",                  # Katalogi użytkowników
    "/var/www"                # Serwer web (opcjonalnie)
]
```

## 📊 Zbierane Metryki

### Metryki systemowe
- **CPU Usage (%)** - wykorzystanie procesora
- **Memory Usage (%)** - wykorzystanie pamięci RAM
- **Disk Usage (%)** - wykorzystanie dysku (partycja główna)
- **Network Latency (ms)** - czas odpowiedzi do serwera API

### Metryki katalogów
- **Rozmiar katalogu (bytes)** - całkowity rozmiar plików
- **Liczba plików** - ilość plików w katalogu
- **Timestamp** - czas pomiaru
- **Dodatkowe informacje** - metadane (rozmiar w MB, itp.)

### Informacje o systemie
- **System operacyjny** - Windows/Linux/macOS + wersja
- **Hostname** - nazwa komputera
- **IP Address** - adres IP (lokalny)
- **Wersja agenta** - identyfikacja wersji

## 🔄 Workflow Agenta

```
1. Start agenta
2. Wykrycie systemu operacyjnego
3. Uwierzytelnienie w API (POST /api/login)
4. Otrzymanie Bearer token
5. PĘTLA:
   a. Zbieranie metryk systemowych
   b. Skanowanie katalogów
   c. Wysyłanie metryk (POST /api/agent/metrics/batch)
   d. Wysyłanie heartbeat (POST /api/agent/heartbeat/{host_id})
   e. Oczekiwanie (COLLECTION_INTERVAL sekund)
6. Obsługa błędów i retry
```

## 🧪 Testowanie z Kontenerami Docker

Agent można przetestować na różnych dystrybucjach Linux używając kontenerów Docker:

### Uruchomienie środowisk testowych
```bash
# Wszystkie kontenery testowe
docker-compose -f docker-compose.test.yml up -d

# Tylko Ubuntu
docker-compose -f docker-compose.test.yml up ubuntu-agent

# Tylko Rocky Linux
docker-compose -f docker-compose.test.yml up rocky-agent

# Tylko Alpine
docker-compose -f docker-compose.test.yml up alpine-agent
```

### Testowanie w kontenerach
```bash
# Wejście do kontenera Ubuntu
docker exec -it zenmon_ubuntu_agent bash

# Sprawdzenie logów
docker-compose -f docker-compose.test.yml logs ubuntu-agent

# Sprawdzenie statusu
docker-compose -f docker-compose.test.yml ps
```

## 📝 Logi i Debugging

### Lokalizacja logów
- **Windows**: `zenmon_agent.log` (katalog agenta)
- **Linux**: `zenmon_agent.log` lub `/var/log/zenmon_agent.log`

### Poziomy logowania
- **DEBUG** - szczegółowe informacje diagnostyczne
- **INFO** - informacje o normalnej pracy
- **WARNING** - ostrzeżenia (problemy z komunikacją)
- **ERROR** - błędy krytyczne

### Przykłady logów
```
2025-01-15 10:30:15 - ZenMonAgent - INFO - Agent started for host ID 1
2025-01-15 10:30:16 - ZenMonAgent - INFO - System detected: Windows 10
2025-01-15 10:30:17 - ZenMonAgent - INFO - Authentication successful, token received
2025-01-15 10:30:18 - ZenMonAgent - INFO - Collected metrics: CPU=25.3%, RAM=64.1%, Disk=45.7%
2025-01-15 10:30:19 - ZenMonAgent - INFO - Metrics submitted successfully (4 metrics)
2025-01-15 10:30:20 - ZenMonAgent - INFO - Heartbeat sent successfully
```

## 🔧 Rozwiązywanie Problemów

### Problem: Agent nie może się połączyć z API
```bash
# Sprawdź dostępność API
curl http://localhost:8001/api/public/health

# Sprawdź logi agenta
tail -f zenmon_agent.log

# Sprawdź konfigurację sieci
ping localhost
```

### Problem: Błędy uwierzytelniania
```python
# Sprawdź konfigurację w kodzie agenta
API_URL = "http://localhost:8001/api"  # Poprawny URL?
# Sprawdź czy użytkownik istnieje w bazie Laravel
```

### Problem: Agent nie zbiera metryk
```bash
# Windows - sprawdź uprawnienia
# Linux - sprawdź czy psutil działa
python3 -c "import psutil; print(psutil.cpu_percent())"
```

## 🚀 Uruchomienie jako Usługa

### Windows (Service)
```powershell
# Użyj NSSM (Non-Sucking Service Manager)
nssm install ZenMonAgent "python" "C:\path\to\zenmon-agent-python-v2.0.py"
nssm start ZenMonAgent
```

### Linux (systemd)
```bash
# Utwórz plik /etc/systemd/system/zenmon-agent.service
[Unit]
Description=ZenMon Agent
After=network.target

[Service]
Type=simple
User=zenmon
WorkingDirectory=/opt/zenmon_agent
ExecStart=/usr/bin/python3 /opt/zenmon_agent/zenmon-agent-python-v2.0.py
Restart=always

[Install]
WantedBy=multi-user.target

# Włącz usługę
sudo systemctl enable zenmon-agent
sudo systemctl start zenmon-agent
```

## 🔒 Bezpieczeństwo

- **Token Authentication** - Bearer token z API Laravel
- **HTTPS** - użyj HTTPS w produkcji
- **Uprawnienia** - uruchom agenta z ograniczonymi uprawnieniami
- **Firewall** - otwórz tylko potrzebne porty (8001 HTTP/HTTPS)

## 📈 Monitoring Agenta

### Sprawdzenie statusu
```python
# Via API ZenMon
GET /api/hosts/{host_id}/status

# Via logi
tail -f zenmon_agent.log | grep "Heartbeat sent"
```

### Metryki wydajności agenta
- **Czas zbierania metryk** - <5 sekund
- **Czas wysyłania danych** - <10 sekund
- **Zużycie CPU** - <5%
- **Zużycie RAM** - <50MB

## 🤝 Rozwój

### Dodanie nowej metryki
1. Dodaj funkcję zbierającą metrykę
2. Zaktualizuj `collect_system_metrics()`
3. Przetestuj z różnymi systemami operacyjnymi
4. Dodaj obsługę błędów

### Konwencje kodu Python
```python
# Regiony (jak w C#)
#region Fields
# zmienne globalne
#endregion

#region Classes  
# definicje klas
#endregion

#region Methods
# funkcje
#endregion

# Dokumentacja metod
def example_method(param1: str, param2: int = 0) -> str:
    """
    Przykładowa metoda
    
    Args:
        param1: Pierwszy parametr
        param2: Drugi parametr (domyślnie 0)
        
    Returns:
        Wynik operacji
    """
    return f"Result: {param1} + {param2}"
```

## 📞 Wsparcie

W przypadku problemów:
1. Sprawdź logi: `zenmon_agent.log`
2. Sprawdź połączenie: `curl API_URL/public/health`
3. Sprawdź konfigurację sieci
4. Przetestuj w kontenerze Docker

---

**Autor**: Cezary Kalinowski i Przemysław Jancewicz
**Wersja**: 2.0  
**Python**: 3.8+  
**Kompatybilność**: Windows, Linux, macOS