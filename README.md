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
│   └── zenmon_agent.log                # Logi agenta (generowane)
├── LICENSE.txt                         # Licencja MIT
└── README.md
```

## 🚀 Instrukcja Instalacji i Uruchomienia

### Wymagania
- **Python 3.8+**
- **pip** (menedżer pakietów Python)
- **PowerShell** (Windows) lub Terminal (Linux/macOS)
- **Działająca aplikacja ZenMon Laravel** (instrukcja: [zenmon-laravel README](https://github.com/ChuckRipper/zenmon-laravel))

### 1. Klonowanie repozytorium
```bash
# Identyczne dla wszystkich terminali
git clone https://github.com/ChuckRipper/zenmon_agent_python.git
cd zenmon_agent_python
```

### 2. Instalacja zależności Python

#### PowerShell (Windows):
```powershell
# Instalacja pakietów
pip install psutil requests

# Sprawdź wersje
python --version
pip --version
```

#### Bash/Zsh/Ksh (Linux/macOS):
```bash
# Instalacja pakietów
pip3 install psutil requests

# Sprawdź wersje
python3 --version
pip3 --version
```

**Uwaga**: Projekt nie zawiera pliku `requirements.txt` - instaluj zależności bezpośrednio jak powyżej.

### 3. Sprawdzenie Host ID w bazie danych

Przed uruchomieniem agenta sprawdź dostępne Host ID w bazie danych ZenMon:

```sql
-- Sprawdź dostępne hosty w DBeaver/MySQL Workbench
SELECT host_id, host_name, ip_address, operating_system 
FROM hosts 
WHERE is_active = 1
ORDER BY host_id;
```

**Typowe Host ID z seedera:**
- `1` - Lokalny host (127.0.0.1) - Windows/Linux automatycznie wykryty
- `2` - Ubuntu container (172.19.0.2)
- `3` - Alpine container (172.19.0.3)  
- `4` - Rocky container (172.19.0.4)

### 4. Sprawdź czy aplikacja Laravel działa

**WAŻNE**: Aplikacja Laravel musi działać na `0.0.0.0:8001` (nie na `127.0.0.1:8001`)!

#### PowerShell:
```powershell
# Sprawdź health check
Invoke-RestMethod -Uri "http://localhost:8001/api/public/health"
# Powinno zwrócić: {"status":"ok","service":"ZenMon API"}
```

#### Bash/Zsh/Ksh:
```bash
# Sprawdź health check
curl http://localhost:8001/api/public/health
# Powinno zwrócić: {"status":"ok","service":"ZenMon API"}
```

### 5. Uruchomienie agenta

**Składnia argumentów:**
```
python zenmon-agent-python-v2.0.py <API_URL> <HOST_ID> <LOGIN> <PASSWORD>
```

**Gdzie:**
- `API_URL`: URL aplikacji Laravel (http://localhost:8001/api)
- `HOST_ID`: ID hosta z tabeli `hosts` w bazie danych
- `LOGIN`: zenmon_agent (konto agenta)
- `PASSWORD`: zenmon_agent123 (hasło agenta)

#### PowerShell (Windows):
```powershell
# Przejdź do katalogu projektu
cd zenmon_agent_python

# Uruchom agenta z 4 argumentami (Host ID = 1 dla lokalnego Windows)
python zenmon-agent-python-v2.0.py http://localhost:8001/api 1 zenmon_agent zenmon_agent123

# W tle (PowerShell Job)
Start-Job -ScriptBlock { python zenmon-agent-python-v2.0.py http://localhost:8001/api 1 zenmon_agent zenmon_agent123 }
```

#### Bash/Zsh/Ksh (Linux/macOS):
```bash
# Uruchom agenta z 4 argumentami
python3 zenmon-agent-python-v2.0.py http://localhost:8001/api 1 zenmon_agent zenmon_agent123

# Lub jako daemon (w tle)
nohup python3 zenmon-agent-python-v2.0.py http://localhost:8001/api 1 zenmon_agent zenmon_agent123 &

# Sprawdź proces w tle
ps aux | grep zenmon
```

## ⚙️ Konfiguracja

Agent v2.0 **NIE WYMAGA** edycji kodu. Wszystkie parametry są przekazywane jako argumenty CLI.

### Zmiana interwału zbierania
Interwał jest kontrolowany przez aplikację Laravel (domyślnie 120 sekund).
Można go zmienić przez API lub w konfiguracji hosta w bazie danych.

### Monitorowane katalogi (automatyczne)

#### Windows
Agent automatycznie wykrywa dyski systemowe (C:, D:, E:, itp.)

#### Linux
Agent pobiera listę katalogów z API Laravel lub używa domyślnych:
```
/root       # Katalog root
/var        # Pliki systemowe
/tmp        # Pliki tymczasowe
/home       # Katalogi użytkowników
/usr        # Programy systemowe
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

## 🧪 Sprawdzenie działania

### 1. Sprawdź czy aplikacja Laravel działa

#### PowerShell:
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/public/health"
# Powinno zwrócić: {"status":"ok","service":"ZenMon API"}
```

#### Bash/Zsh/Ksh:
```bash
curl http://localhost:8001/api/public/health
# Powinno zwrócić: {"status":"ok","service":"ZenMon API"}
```

### 2. Sprawdź health check agenta (po uruchomieniu)

#### PowerShell:
```powershell
# Windows agent (lokalny)
Invoke-RestMethod -Uri "http://127.0.0.1:8080/health"

# Docker agents
Invoke-RestMethod -Uri "http://172.19.0.2:8080/health"  # Ubuntu
Invoke-RestMethod -Uri "http://172.19.0.3:8080/health"  # Alpine
Invoke-RestMethod -Uri "http://172.19.0.4:8080/health"  # Rocky
```

#### Bash/Zsh/Ksh:
```bash
# Windows agent (lokalny)
curl http://127.0.0.1:8080/health

# Docker agents
curl http://172.19.0.2:8080/health  # Ubuntu
curl http://172.19.0.3:8080/health  # Alpine
curl http://172.19.0.4:8080/health  # Rocky
```

### 3. Sprawdź czy metryki są zapisywane
```sql
-- W DBeaver sprawdź najnowsze metryki
SELECT m.host_id, mt.metric_name, m.value, m.timestamp 
FROM metrics m
JOIN metric_types mt ON m.metric_type_id = mt.metric_type_id
ORDER BY m.timestamp DESC 
LIMIT 20;
```

## 🧪 Testowanie z Kontenerami Docker

Agent można przetestować na różnych dystrybucjach Linux używając kontenerów Docker:

### Uruchomienie środowisk testowych
```bash
# Identyczne dla wszystkich terminali
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
# Identyczne dla wszystkich terminali
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
- **Docker**: Logi supervisor + aplikacji w kontenerze

### Poziomy logowania
- **DEBUG** - szczegółowe informacje diagnostyczne
- **INFO** - informacje o normalnej pracy
- **WARNING** - ostrzeżenia (problemy z komunikacją)
- **ERROR** - błędy krytyczne

### Przeglądanie logów

#### PowerShell:
```powershell
# Tail logów agenta
Get-Content zenmon_agent.log -Wait

# Logi kontenerów Docker
docker-compose -f docker-compose.test.yml logs -f ubuntu-agent
```

#### Bash/Zsh/Ksh:
```bash
# Tail logów agenta
tail -f zenmon_agent.log

# Logi kontenerów Docker
docker-compose -f docker-compose.test.yml logs -f ubuntu-agent
```

### Przykłady logów
```
2025-01-15 10:30:15 - ZenMonAgent - INFO - 🚀 Agent started for host ID 1
2025-01-15 10:30:16 - ZenMonAgent - INFO - 💻 System detected: Windows 10
2025-01-15 10:30:17 - ZenMonAgent - INFO - 🔐 Authentication successful, token received
2025-01-15 10:30:18 - ZenMonAgent - INFO - 📊 Collected metrics: CPU=25.3%, RAM=64.1%, Disk=45.7%
2025-01-15 10:30:19 - ZenMonAgent - INFO - ✅ Metrics submitted successfully (4 metrics)
2025-01-15 10:30:20 - ZenMonAgent - INFO - 💗 Heartbeat sent successfully
```

## 🔧 Rozwiązywanie Problemów

### Problem: Agent nie może się połączyć z API

#### PowerShell:
```powershell
# 1. Sprawdź czy Laravel działa na 0.0.0.0:8001
php artisan serve --host=0.0.0.0 --port=8001

# 2. Sprawdź firewall
Get-NetFirewallProfile

# 3. Sprawdź logi agenta
Get-Content zenmon_agent.log -Wait
```

#### Bash/Zsh/Ksh:
```bash
# 1. Sprawdź czy Laravel działa na 0.0.0.0:8001  
php artisan serve --host=0.0.0.0 --port=8001

# 2. Sprawdź firewall (Linux)
sudo ufw status
sudo ufw allow 8001

# 3. Sprawdź logi agenta
tail -f zenmon_agent.log
```

### Problem: "Host ID not found"
**Rozwiązanie**: Sprawdź w bazie czy host o danym ID istnieje:
```sql
SELECT * FROM hosts WHERE host_id = 1 AND is_active = 1;
```

### Problem: "Authentication failed"
**Rozwiązanie**: Sprawdź czy użytkownik `zenmon_agent` istnieje:
```sql
SELECT * FROM users WHERE login = 'zenmon_agent' AND is_active = 1;
```

### Problem: Agent nie zbiera metryk

#### PowerShell:
```powershell
# Sprawdź czy psutil działa
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%')"

# Sprawdź uprawnienia (Windows)
whoami /priv
```

#### Bash/Zsh/Ksh:
```bash
# Sprawdź czy psutil działa
python3 -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%')"

# Sprawdź uprawnienia (Linux)
id
```

### Problem: "Connection refused" z Dockera
**Rozwiązanie**: Sprawdź czy aplikacja Laravel działa na `0.0.0.0:8001`, nie na `localhost:8001`

### Problem: "ModuleNotFoundError: No module named 'psutil'"

#### PowerShell:
```powershell
# Reinstaluj pakiety
pip uninstall psutil requests
pip install psutil requests

# Sprawdź instalację
pip list | Select-String psutil
```

#### Bash/Zsh/Ksh:
```bash
# Reinstaluj pakiety
pip3 uninstall psutil requests
pip3 install psutil requests

# Sprawdź instalację
pip3 list | grep psutil
```

## 🚀 Uruchomienie jako Usługa

### Windows (Service)
```powershell
# Użyj NSSM (Non-Sucking Service Manager)
# Pobierz z: https://nssm.cc/download

# Zainstaluj jako usługę
nssm install ZenMonAgent python "C:\path\to\zenmon-agent-python-v2.0.py" "http://localhost:8001/api" "1" "zenmon_agent" "zenmon_agent123"

# Skonfiguruj usługę
nssm set ZenMonAgent AppDirectory "C:\path\to\zenmon_agent_python"
nssm set ZenMonAgent DisplayName "ZenMon Monitoring Agent"
nssm set ZenMonAgent Description "ZenMon system monitoring agent"

# Uruchom usługę
nssm start ZenMonAgent

# Sprawdź status
Get-Service ZenMonAgent
```

### Linux (systemd)
```bash
# Utwórz plik /etc/systemd/system/zenmon-agent.service
sudo tee /etc/systemd/system/zenmon-agent.service > /dev/null <<EOF
[Unit]
Description=ZenMon Monitoring Agent
After=network.target

[Service]
Type=simple
User=zenmon
Group=zenmon
WorkingDirectory=/opt/zenmon_agent
ExecStart=/usr/bin/python3 /opt/zenmon_agent/zenmon-agent-python-v2.0.py http://localhost:8001/api 1 zenmon_agent zenmon_agent123
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Przeładuj systemd
sudo systemctl daemon-reload

# Włącz i uruchom usługę
sudo systemctl enable zenmon-agent
sudo systemctl start zenmon-agent

# Sprawdź status
sudo systemctl status zenmon-agent

# Sprawdź logi
sudo journalctl -u zenmon-agent -f
```

### macOS (launchd)
```bash
# Utwórz plik ~/Library/LaunchAgents/com.zenmon.agent.plist
cat > ~/Library/LaunchAgents/com.zenmon.agent.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.zenmon.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/zenmon-agent-python-v2.0.py</string>
        <string>http://localhost:8001/api</string>
        <string>1</string>
        <string>zenmon_agent</string>
        <string>zenmon_agent123</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Załaduj usługę
launchctl load ~/Library/LaunchAgents/com.zenmon.agent.plist

# Sprawdź status
launchctl list | grep zenmon
```

## 🔒 Bezpieczeństwo

- **Token Authentication** - Bearer token z API Laravel
- **HTTPS** - użyj HTTPS w produkcji (`https://your-domain.com/api`)
- **Uprawnienia** - uruchom agenta z ograniczonymi uprawnieniami
- **Firewall** - otwórz tylko potrzebne porty (8001 HTTP/HTTPS)
- **Szyfrowanie** - token przechowywany w pamięci (nie na dysku)

## 📈 Monitoring Agenta

### Sprawdzenie statusu przez API
```bash
# Sprawdź status hosta
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8001/api/hosts/1/status

# Sprawdź ostatnie metryki
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8001/api/hosts/1/metrics/latest
```

### Monitoring przez logi

#### PowerShell:
```powershell
# Sprawdź ostatnie heartbeats
Get-Content zenmon_agent.log | Select-String "Heartbeat sent" | Select-Object -Last 5
```

#### Bash/Zsh/Ksh:
```bash
# Sprawdź ostatnie heartbeats
tail -f zenmon_agent.log | grep "Heartbeat sent"
```

### Metryki wydajności agenta
- **Czas zbierania metryk** - <5 sekund
- **Czas wysyłania danych** - <10 sekund
- **Zużycie CPU** - <5%
- **Zużycie RAM** - <50MB

## 🤝 Rozwój

### Dodanie nowej metryki
1. Dodaj funkcję zbierającą metrykę w sekcji `#region Methods`
2. Zaktualizuj `collect_system_metrics()`
3. Przetestuj z różnymi systemami operacyjnymi
4. Dodaj obsługę błędów i logging

### Konwencje kodu Python
```python
# Regiony (jak w C#)
#region Fields
# zmienne globalne i konfiguracja
#endregion

#region Classes  
# definicje klas (AgentConfig, MetricCollector, etc.)
#endregion

#region Methods
# funkcje główne i pomocnicze
#endregion

# Dokumentacja metod (zgodnie z Google Style)
def example_method(param1: str, param2: int = 0) -> str:
    """
    Przykładowa metoda zgodna z konwencjami ZenMon
    
    Args:
        param1: Pierwszy parametr (opis)
        param2: Drugi parametr z wartością domyślną
        
    Returns:
        Wynik operacji jako string
        
    Raises:
        ValueError: Gdy param1 jest pusty
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    
    return f"Result: {param1} + {param2}"
```

### Testowanie nowych funkcji
```bash
# Uruchom w trybie debug
python zenmon-agent-python-v2.0.py http://localhost:8001/api 1 zenmon_agent zenmon_agent123 --debug

# Test jednostkowy (jeśli dodane)
python -m pytest tests/

# Test integracji z kontenerami
docker-compose -f docker-compose.test.yml up --build
```

## 📞 Wsparcie

W przypadku problemów sprawdź w kolejności:

1. **Logi agenta**: `zenmon_agent.log`
2. **Połączenie z API**: `curl http://localhost:8001/api/public/health`
3. **Host ID w bazie**: `SELECT * FROM hosts WHERE host_id = X;`
4. **Użytkownik agenta**: `SELECT * FROM users WHERE login = 'zenmon_agent';`
5. **Logi Laravel**: `storage/logs/laravel.log`
6. **Test w kontenerze**: Docker environment dla eliminacji problemów środowiska

### Przydatne komendy diagnostyczne

#### PowerShell:
```powershell
# Sprawdź proces agenta
Get-Process python | Where-Object {$_.CommandLine -like "*zenmon*"}

# Sprawdź połączenia sieciowe
netstat -an | Select-String "8001\|8080"
```

#### Bash/Zsh/Ksh:
```bash
# Sprawdź proces agenta
ps aux | grep zenmon

# Sprawdź połączenia sieciowe
netstat -tulpn | grep -E "8001|8080"
```

---

**Autorzy**: Cezary Kalinowski i Przemysław Jancewicz  
**Wersja**: 2.0  
**Python**: 3.8+  
**Kompatybilność**: Windows, Linux, macOS  
**Integracja**: [ZenMon Laravel API](https://github.com/ChuckRipper/zenmon-laravel)