# dspy-test - Azure DevOps PBI Extraction System

Sistema AI-powered per l'estrazione di Product Backlog Items (PBI) da riassunti in linguaggio naturale e creazione automatica in Azure DevOps.

## Caratteristiche Principali

- 🤖 **Estrazione AI**: Utilizza DSPy e Google Gemini per estrarre PBI da conversazioni naturali
- 💬 **Chat Sessions**: Gestione di conversazioni interattive per raccogliere requisiti
- 📝 **PBI Generation**: Creazione automatica di PBI strutturati in Azure DevOps
- 🚀 **REST API**: Endpoint HTTP per integrazione con altri sistemi

## Architettura

Il sistema espone una REST API FastAPI (`src/server_api.py`) che offre:
- Gestione completa di sessioni di chat
- Estrazione di PBI da conversazioni multi-turno
- Creazione automatica in Azure DevOps
- Pipeline di estrazione tramite moduli DSPy

## Installazione

### Requisiti
- Python >= 3.13
- uv package manager

### Setup

```bash
# Clona il repository
git clone <repository-url>
cd dspy-test

# Installa le dipendenze
uv sync

# Configura le variabili d'ambiente
cp .env.example .env
# Modifica .env con le tue credenziali
```

### Variabili d'Ambiente

```env
GEMINI_API_KEY=your_gemini_api_key
AZDO_PERSONAL_ACCESS_TOKEN=your_azure_devops_token
AZDO_ORGANIZATION=your_organization_name
```

## Utilizzo

### Avvio Server API

```bash
# Development
uvicorn src.server_api:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn src.server_api:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build
docker build -t dspy-test .

# Run
docker run -e GEMINI_API_KEY=... \
           -e AZDO_PERSONAL_ACCESS_TOKEN=... \
           -e AZDO_ORGANIZATION=... \
           -p 8000:8000 dspy-test
```

Accesso alla documentazione API: `http://localhost:8000/docs`

## Funzionalità

### 1. Chat Session Management

Gestione di conversazioni interattive per l'estrazione di PBI tramite REST API. Vedi [CHAT_SESSIONS.md](CHAT_SESSIONS.md) per dettagli completi.

**Endpoint disponibili:**
- `POST /chat/sessions` - Crea nuova sessione
- `GET /chat/sessions` - Elenca tutte le sessioni
- `GET /chat/sessions/{chat_id}` - Dettagli sessione specifica
- `POST /chat/sessions/{chat_id}/messages` - Aggiungi messaggio
- `DELETE /chat/sessions/{chat_id}` - Elimina sessione
- `POST /chat/sessions/{chat_id}/process` - Estrai PBI dalla conversazione

**Esempio di utilizzo (curl):**
```bash
# 1. Crea sessione
curl -X POST http://localhost:8000/chat/sessions

# 2. Aggiungi messaggi
curl -X POST http://localhost:8000/chat/sessions/{chat_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"role": "user", "content": "Voglio creare PBI per progetto WebApp"}'

# 3. Elabora conversazione
curl -X POST http://localhost:8000/chat/sessions/{chat_id}/process \
  -H "Content-Type: application/json" \
  -d '{"create_pbis": true}'
```

### 2. Direct Summary Processing

Elaborazione diretta di riassunti per estrazione veloce:

```bash
curl -X POST http://localhost:8000/pbi-creator \
  -H "Content-Type: application/json" \
  -d '{"summary": "Riassunto del progetto..."}'
```

## Struttura del Progetto

```
dspy-test/
├── src/
│   ├── server_api.py          # REST API FastAPI con chat management
│   ├── chat_manager.py        # Gestione sessioni chat
│   ├── models.py              # Modelli Pydantic (inclusi chat models)
│   ├── llm_client.py          # Client Gemini/DSPy
│   ├── azdo_client.py         # Client Azure DevOps
│   ├── config/
│   │   └── settings.py        # Configurazione ambiente
│   └── extractors/
│       ├── pbi.py             # Estrazione PBI
│       └── azdo.py            # Estrazione info progetto
├── CHAT_SESSIONS.md           # Documentazione chat sessions
├── pyproject.toml             # Dipendenze del progetto
└── Dockerfile                 # Container configuration
```

## Modelli Dati

### PBI (Product Backlog Item)
```python
class PBI(BaseModel):
    title: str          # Titolo breve e chiaro
    description: str    # Descrizione dettagliata
```

### ChatSession
```python
class ChatSession(BaseModel):
    chat_id: str                    # ID univoco
    messages: list[ChatMessage]     # Cronologia messaggi
    created_at: datetime            # Data creazione
    updated_at: datetime            # Ultimo aggiornamento
    project: str | None             # Progetto Azure DevOps
    pbis: list[PBI]                 # PBI estratti
    status: str                     # active/processing/completed/error
```

## Sviluppo

### Linting e Formattazione

```bash
# Check codice
uv run ruff check src/

# Formatta codice
uv run ruff format src/
```

### Testing

```bash
# Test manuale chat manager
uv run python /path/to/test_script.py
```

## Dipendenze Principali

- **dspy** (3.0.3): Framework per composizione LLM con ChainOfThought
- **fastmcp** (2.13.0.2): Implementazione Model Context Protocol
- **pydantic** (2.12.3): Validazione dati e settings da env
- **azure-devops** (7.1.0b4): Client API Azure DevOps

## Note Importanti

- Le sessioni di chat sono memorizzate **in memoria** (non persistenti tra riavvii)
- I prompt sono in italiano per coerenza con l'elaborazione
- Supporto per conversazioni multi-turno con context tracking
- ChainOfThought DSPy per reasoning tracciabile

## Licenza

[Specificare licenza]

## Contributors

[Lista contributors]
