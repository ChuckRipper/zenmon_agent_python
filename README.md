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

### 3. Sprawdzenie Host ID w bazie danych

Przed uruchomieniem agenta sprawdź dostępne Host ID w bazie:

```sql
-- Sprawdź dostępne hosty w DBeaver/MySQL Workbench
SELECT host_id, host_name, ip_address, operating_system 
FROM hosts 
ORDER BY host_id;
```

**Typowe Host ID:**
- `1` - Lokalny Windows (127.0.0.1)
- `2` - Ubuntu container (172.19.0.2)
- `3` - Alpine container (172.19.0.3)  
- `4` - Rocky container (172.19.0.4)

### 4. Uruchomienie agenta

**Składnia argumentów:**
```
python zenmon-agent-python-v2.0.py <API_URL> <HOST_ID> <LOGIN> <PASSWORD>
```

**Gdzie:**
- `API_URL`: URL aplikacji Laravel (np. http://localhost:8001/api)
- `HOST_ID`: ID hosta z tabeli `hosts` w bazie danych
- `LOGIN`: zenmon_agent (konto agenta)
- `PASSWORD`: zenmon_agent123 (hasło agenta)

#### Windows (PowerShell)
```powershell
# Przejdź do katalogu projektu
cd zenmon_agent_python

# Uruchom agenta z 4 argumentami (Host ID = 1 dla Windows)
python zenmon-agent-python-v2.0.py http://localhost:8001/api 1 zenmon_agent zenmon_agent123
```

#### Linux/macOS
```bash
# Uruchom agenta z 4 argumentami
python3 zenmon-agent-python-v2.0.py http://localhost:8001/api 1 zenmon_agent zenmon_agent123

# Lub jako daemon (w tle)
nohup python3 zenmon-agent-python-v2.0.py http://localhost:8001/api 1 zenmon_agent zenmon_agent123 &
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
```bash
# Aplikacja musi działać na 0.0.0.0:8001 (nie na 127.0.0.1!)
curl http://localhost:8001/api/public/health
# Powinno zwrócić: {"status":"ok","service":"ZenMon API"}
```

### 2. Sprawdź health check agenta (po uruchomieniu)
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
SELECT m.host_id, mt.metric_name, m.value, m.created_at 
FROM metrics m
JOIN metric_types mt ON m.metric_type_id = mt.metric_type_id
ORDER BY m.created_at DESC 
LIMIT 20;
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
**Rozwiązanie**: 
1. Sprawdź czy Laravel działa na `0.0.0.0:8001` (nie na `127.0.0.1:8001`)
2. Sprawdź firewall/antywirus
3. Sprawdź logi agenta: `tail -f logs/zenmon_agent.log`

### Problem: "Host ID not found"
**Rozwiązanie**: Sprawdź w bazie czy host o danym ID istnieje:
```sql
SELECT * FROM hosts WHERE host_id = 1;
```

### Problem: "Authentication failed"
**Rozwiązanie**: Sprawdź czy użytkownik `zenmon_agent` istnieje:
```sql
SELECT * FROM users WHERE login = 'zenmon_agent';
```

### Problem: Agent nie zbiera metryk
```bash
# Windows - sprawdź uprawnienia
# Linux - sprawdź czy psutil działa
python3 -c "import psutil; print(psutil.cpu_percent())"
```

### Problem: "Connection refused" z Dockera
**Rozwiązanie**: Sprawdź czy aplikacja Laravel działa na `0.0.0.0:8001`, nie na `localhost:8001`

## 🚀 Uruchomienie jako Usługa

### Windows (Service)
```powershell
# Użyj NSSM (Non-Sucking Service Manager)
nssm install ZenMonAgent "python" "C:\path\to\zenmon-agent-python-v2.0.py http://localhost:8001/api 1 zenmon_agent zenmon_agent123"
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
ExecStart=/usr/bin/python3 /opt/zenmon_agent/zenmon-agent-python-v2.0.py http://localhost:8001/api 1 zenmon_agent zenmon_agent123
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
1. Sprawdź logi: `logs/zenmon_agent.log`
2. Sprawdź połączenie: `curl API_URL/public/health`
3. Sprawdź czy Host ID istnieje w bazie
4. Sprawdź czy użytkownik `zenmon_agent` istnieje
5. Przetestuj w kontenerze Docker

---

**Autor**: Cezary Kalinowski i Przemysław Jancewicz
**Wersja**: 2.0  
**Python**: 3.8+  
**Kompatybilność**: Windows, Linux, macOS