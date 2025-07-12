# ZenMon Agent

**Minimalistyczny agent monitoringu systemowego** - alternatywa dla Zabbix/Nagios

ZenMon Agent to lekki, napisany w Pythonie agent do zbierania metryk systemowych zgodnie z filozofią "Zen" - prostota i przystępność dla każdego użytkownika.

## 🎯 Funkcjonalności

Agent zbiera następujące metryki zgodnie z **UC30**:
- **CPU Usage** (% wykorzystania procesora)  
- **Memory Usage** (% wykorzystania pamięci RAM)
- **Disk Usage** (% wykorzystania przestrzeni dyskowej)
- **Network Response Time** (czas odpowiedzi sieci w ms)
- **Katalogi** (zajętość wybranych katalogów systemowych)

## 📋 Wymagania

- **Python 3.8+**
- **pip** (menedżer pakietów Python)
- **Biblioteki:** `requests`, `psutil`
- **ZenMon API** uruchomiona i dostępna

## 🚀 Szybka instalacja

### 1. Klonowanie repozytorium
```bash
git clone https://github.com/ChuckRipper/zenmon_agent_python.git
cd zenmon_agent_python
```

### 2. Instalacja zależności
```bash
pip install requests psutil
```

### 3. Uruchomienie agenta
```bash
python zenmon-agent-python.py http://localhost:8001/api 1
```

**Parametry:**
- `http://localhost:8001/api` - URL do ZenMon API
- `1` - ID hosta w systemie ZenMon

## 📁 Struktura projektu

```
zenmon_agent_python/
├── zenmon-agent-python.py      # Główny skrypt agenta
├── logs/                       # Katalog z logami (w .gitignore)
│   └── zenmon_agent.log        # Logi działania agenta
├── docker-test/                # Środowisko testowe Docker
│   ├── health_server.py        # Serwer health check
│   ├── load_test.py            # Skrypt testów obciążeniowych
│   ├── ubuntu/                 # Ubuntu 22.04 container
│   ├── rocky/                  # Rocky Linux 9 container
│   └── alpine/                 # Alpine Linux container
├── docker-compose.test.yml     # Orchestracja testów
├── .gitignore                  # Wykluczenia Git
└── README.md                   # Ta dokumentacja
```

## ⚙️ Konfiguracja

Agent przyjmuje parametry przez argumenty wiersza poleceń:

```bash
python zenmon-agent-python.py <API_URL> <HOST_ID> [opcje]
```

### Zmienne środowiskowe (opcjonalne):
- `COLLECTION_INTERVAL` - Interwał zbierania metryk w sekundach (domyślnie: 120)
- `LOG_LEVEL` - Poziom logowania (DEBUG, INFO, WARNING, ERROR)
- `ZENMON_AGENT_VERSION` - Wersja agenta (domyślnie: 1.0.0)

### Przykłady uruchomienia:
```bash
# Podstawowe uruchomienie
python zenmon-agent-python.py http://localhost:8001/api 1

# Z custom interwałem (60 sekund)
COLLECTION_INTERVAL=60 python zenmon-agent-python.py http://localhost:8001/api 1

# Z debugowaniem
LOG_LEVEL=DEBUG python zenmon-agent-python.py http://localhost:8001/api 1
```

## 🔧 Instalacja jako usługa systemowa

### Ubuntu/Debian (systemd):

1. **Utwórz plik usługi:**
```bash
sudo nano /etc/systemd/system/zenmon-agent.service
```

2. **Zawartość pliku:**
```ini
[Unit]
Description=ZenMon Agent
After=network.target

[Service]
Type=simple
User=zenmon
WorkingDirectory=/opt/zenmon
ExecStart=/usr/bin/python3 /opt/zenmon/zenmon-agent-python.py http://localhost:8001/api 1
Restart=always
RestartSec=10
Environment=COLLECTION_INTERVAL=120
Environment=LOG_LEVEL=INFO

[Install]
WantedBy=multi-user.target
```

3. **Aktywacja usługi:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable zenmon-agent
sudo systemctl start zenmon-agent
sudo systemctl status zenmon-agent
```

## 🐳 Testowanie z Docker

Projekt zawiera kompletne środowisko testowe z kontenerami różnych dystrybucji Linux.

### Szybki start testów
```bash
# Uruchomienie wszystkich agentów testowych
docker-compose -f docker-compose.test.yml up -d

# Sprawdzenie statusu
docker-compose -f docker-compose.test.yml ps

# Logi agentów
docker-compose -f docker-compose.test.yml logs -f

# Zatrzymanie
docker-compose -f docker-compose.test.yml down
```

### Dostępne kontenery testowe:
- **Ubuntu 22.04 LTS** - HOST_ID=10
- **Rocky Linux 9** - HOST_ID=11  
- **Alpine Linux 3.18** - HOST_ID=12

### Health check endpoints:
Każdy kontener udostępnia HTTP endpoint do monitorowania:
- `/health` - Status agenta z metrykami systemowymi
- `/info` - Informacje o agencie i konfiguracji

### Testy obciążeniowe:
```bash
# Uruchomienie z load testem
docker-compose -f docker-compose.test.yml --profile load-test up -d

# Tylko load test (generuje metryki dla HOST_ID 13-17)
docker-compose -f docker-compose.test.yml up load-test
```

### Debugowanie kontenerów:
```bash
# Wejście do kontenera Ubuntu
docker exec -it zenmon_ubuntu_agent bash

# Wejście do kontenera Rocky Linux
docker exec -it zenmon_rocky_agent bash

# Sprawdzenie procesów w kontenerze
docker exec -it zenmon_ubuntu_agent supervisorctl status

# Logi agenta z kontenera
docker exec -it zenmon_ubuntu_agent tail -f /var/log/zenmon/agent.log
```

## 📡 API Endpoints (Agent → ZenMon)

Agent komunikuje się z następującymi endpointami ZenMon API:

### Wysyłanie metryk:
```http
POST /api/agent/metrics
Content-Type: application/json

{
  "metrics": [
    {
      "host_id": 1,
      "metric_name": "CPU Usage",
      "unit": "%",
      "value": 45.2,
      "timestamp": "2025-01-15T10:30:00Z"
    }
  ]
}
```

### Health check ZenMon API:
```http
GET /api/public/health
```

### Rejestracja agenta:
```http
POST /api/agent/register
Content-Type: application/json

{
  "ip_address": "192.168.1.10",
  "hostname": "server-01",
  "operating_system": "Ubuntu 22.04",
  "agent_version": "1.0.0"
}
```

## 📊 Logi i monitoring

### Lokalizacja logów:
- **Plik logów:** `logs/zenmon_agent.log`
- **Format:** `[TIMESTAMP] - LEVEL - MESSAGE`
- **Rotacja:** Automatyczna (nie przekroczy 50MB)

### Przykład logów:
```
2025-01-15 10:30:15 - INFO - ZenMon Agent started (Host ID: 1)
2025-01-15 10:30:15 - INFO - API URL: http://localhost:8001/api
2025-01-15 10:30:15 - INFO - Collection interval: 120 seconds
2025-01-15 10:32:15 - INFO - Cycle completed successfully (4 metrics)
2025-01-15 10:34:15 - ERROR - Failed to send metrics: Connection timeout
```

### Poziomy logowania:
- **DEBUG** - Szczegółowe informacje diagnostyczne
- **INFO** - Standardowe operacje agenta  
- **WARNING** - Ostrzeżenia nie blokujące działania
- **ERROR** - Błędy wymagające uwagi

## 🔍 Rozwiązywanie problemów

### Agent nie może połączyć się z API
```bash
# Sprawdź dostępność API
curl http://localhost:8001/api/public/health

# Sprawdź konfigurację sieci
ping localhost

# Sprawdź logi agenta
tail -f logs/zenmon_agent.log
```

### Wysokie zużycie CPU/pamięci
```bash
# Zwiększ interwał zbierania metryk
COLLECTION_INTERVAL=300 python zenmon-agent-python.py http://localhost:8001/api 1

# Sprawdź logi pod kątem błędów
grep ERROR logs/zenmon_agent.log
```

### Agent nie wysyła metryk katalogów
- Sprawdź uprawnienia do katalogów systemowych
- Uruchom agenta z uprawnieniami sudo (jeśli potrzebne)
- Sprawdź czy katalogi istnieją w systemie

### Problemy z kontenerami Docker
```bash
# Sprawdź czy ZenMon API jest dostępna z kontenera
docker-compose -f docker-compose.test.yml logs network-check

# Rebuild obrazów po zmianach
docker-compose -f docker-compose.test.yml build --no-cache

# Sprawdź health check kontenerów
docker inspect zenmon_ubuntu_agent | jq '.[0].State.Health'
```

## 📈 Wydajność i ograniczenia

### Zalecane parametry:
- **Interwał zbierania:** 60-300 sekund (domyślnie: 120s)
- **RAM:** ~10-20MB podczas działania
- **CPU:** <1% przy normalnej pracy
- **Sieć:** ~1-5KB na cykl zbierania

### Ograniczenia:
- Agent musi mieć dostęp do katalogów systemowych
- Wymaga połączenia sieciowego z ZenMon API
- Niektóre metryki mogą wymagać uprawnień root

## 🤝 Wkład w rozwój

1. Fork repozytorium
2. Utwórz branch dla nowej funkcjonalności
3. Dodaj testy do nowej funkcjonalności  
4. Wyślij Pull Request

### Struktura kodu:
- **Kod zgodny z PEP 8**
- **Dokumentacja przez docstrings** (format C#)
- **Regiony organizujące kod** (#region/#endregion)
- **Obsługa błędów** we wszystkich operacjach

## 📄 Licencja

MIT License - zobacz plik `LICENSE` dla szczegółów.

## 🔗 Linki

### Repozytoria GitHub:
- **ZenMon Agent (Python):** https://github.com/ChuckRipper/zenmon_agent_python
- **ZenMon Web Application (Laravel):** https://github.com/ChuckRipper/zenmon-laravel

### Lokalne endpointy (development):
- **ZenMon Web Application:** http://localhost:8001
- **ZenMon API:** http://localhost:8001/api  
- **API Health Check:** http://localhost:8001/api/public/health
- **Swagger Documentation:** http://localhost:8001/api/documentation

---

**ZenMon** - *Monitoring w stylu Zen: prosty, minimalistyczny, skuteczny* 🧘‍♂️