# FastMCP 2.0 Server - AzdoProjectHandler

Server FastMCP che espone `AzdoProjectHandler` come strumento principale per elaborare PBIs e progetti Azure DevOps.

## 🚀 Avvio rapido

### Installazione dipendenze

```bash
pip install mcp dspy-ai azure-devops google-generativeai pydantic msrest
```

### Configurazione variabili d'ambiente

Crea un file `.env` nella root del progetto:

```env
GEMINI_API_KEY=your-gemini-api-key
AZDO_PERSONAL_ACCESS_TOKEN=your-azdo-token
AZDO_ORGANIZATION=your-organization-name
```

### Esecuzione locale (test)

```bash
python main.py
```

### Configurazione con Claude Desktop

#### Windows
Modifica `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "azdo-handler": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "c:\\_\\Repos\\Sandbox\\dspy-test"
    }
  }
}
```

#### macOS/Linux
Modifica `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "azdo-handler": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "/path/to/dspy-test"
    }
  }
}
```

Riavvia Claude Desktop dopo la modifica.

## 🛠️ Tools disponibili

### 1. `initialize_azdo_handler()`

Inizializza il sistema configurando DSPy, Gemini e le credenziali Azure DevOps.

**Esempio di risposta:**
```json
{
  "success": true,
  "message": "Sistema inizializzato correttamente",
  "organization": "my-org"
}
```

---

### 2. `process_azdo_summary(summary: str)`

Elabora un sommario completo per estrarre sia PBIs che progetto Azure DevOps.

**Parametri:**
- `summary` (str): Testo del sommario da elaborare

**Esempio di risposta:**
```json
{
  "success": true,
  "message": "Elaborazione completata",
  "pbis_count": 3,
  "pbis": [
    {
      "title": "Implementare autenticazione utente",
      "description": "Sistema di login con OAuth2"
    },
    {
      "title": "Dashboard analytics",
      "description": "Visualizzazione metriche real-time"
    }
  ],
  "azdo_project": {
    "project": "MyProject"
  }
}
```

---

### 3. `extract_pbis_only(summary: str)`

Estrae solo i PBIs da un sommario.

**Parametri:**
- `summary` (str): Testo da cui estrarre i PBIs

**Esempio di risposta:**
```json
{
  "success": true,
  "message": "PBIs estratti con successo",
  "pbis_count": 2,
  "pbis": [...]
}
```

---

### 4. `extract_azdo_project_only(summary: str)`

Estrae solo il progetto Azure DevOps da un sommario.

**Parametri:**
- `summary` (str): Testo da cui estrarre il progetto

**Esempio di risposta:**
```json
{
  "success": true,
  "message": "Progetto Azure DevOps estratto",
  "azdo_project": {
    "project": "MyProject"
  }
}
```

---

### 5. `submit_pbis_to_azdo()`

Invia i PBIs correntemente caricati al backlog di Azure DevOps.

**Esempio di risposta:**
```json
{
  "success": true,
  "message": "Inviati 3 PBIs ad Azure DevOps con successo"
}
```

---

### 6. `get_handler_state()`

Recupera lo stato corrente (PBIs e progetto caricati).

**Esempio di risposta:**
```json
{
  "success": true,
  "pbis_count": 2,
  "pbis": [...],
  "azdo_project": {...}
}
```

---

### 7. `reset_handler()`

Reimposta il handler creando una nuova istanza vuota.

**Esempio di risposta:**
```json
{
  "success": true,
  "message": "Handler reimpostato con successo"
}
```

## 📝 Flusso di lavoro tipico

1. **Inizializza il sistema**
   ```
   Chiama: initialize_azdo_handler()
   ```

2. **Elabora un sommario**
   ```
   Chiama: process_azdo_summary(summary="Creare dashboard analytics con grafici...")
   ```

3. **Verifica lo stato**
   ```
   Chiama: get_handler_state()
   ```

4. **Invia i PBIs ad Azure DevOps**
   ```
   Chiama: submit_pbis_to_azdo()
   ```

5. **Reset per nuova sessione** (opzionale)
   ```
   Chiama: reset_handler()
   ```

## 🔍 Esempio d'uso con Claude

**Utente:**
> Inizializza il sistema e processa questo sommario: "Creare un sistema di autenticazione con login/logout, dashboard per visualizzare statistiche utente, e API REST per mobile app. Progetto: CustomerPortal"

**Claude risponderà utilizzando i tools:**
1. Chiamerà `initialize_azdo_handler()`
2. Chiamerà `process_azdo_summary(summary="...")`
3. Mostrerà i PBIs estratti
4. Chiederà conferma per inviare ad Azure DevOps
5. Se confermato, chiamerà `submit_pbis_to_azdo()`

## 🐛 Troubleshooting

### Il server non si avvia
- Verifica che tutte le dipendenze siano installate: `pip list | grep mcp`
- Controlla che il file `.env` esista e contenga tutte le variabili

### Claude Desktop non vede il server
- Controlla che il percorso in `claude_desktop_config.json` sia assoluto e corretto
- Verifica che `python` nel comando punti all'interprete corretto: `where python` (Windows) o `which python` (Unix)
- Riavvia Claude Desktop dopo ogni modifica alla configurazione

### Errori durante l'elaborazione
- Verifica le credenziali Azure DevOps
- Controlla che la chiave API Gemini sia valida
- Consulta i log per dettagli (stderr)

## 📚 Architettura

```
main.py (FastMCP Server)
├── AzdoProjectHandler (classe core)
│   ├── process_flow()
│   ├── process_pbi()
│   └── process_azdo()
├── Tools FastMCP (@mcp.tool())
│   ├── initialize_azdo_handler
│   ├── process_azdo_summary
│   ├── extract_pbis_only
│   ├── extract_azdo_project_only
│   ├── submit_pbis_to_azdo
│   ├── get_handler_state
│   └── reset_handler
└── Helper functions
    └── process_backlog_items()
```

## 🔐 Sicurezza

- Le credenziali vengono caricate da variabili d'ambiente (`.env`)
- Il token Azure DevOps non viene mai esposto nelle risposte
- Tutti gli errori sono loggati in modo sicuro senza esporre dati sensibili

## 📦 Dipendenze

| Pacchetto | Versione | Scopo |
|-----------|----------|-------|
| mcp | latest | Framework FastMCP per server MCP |
| dspy-ai | latest | Framework DSPy per LLM |
| azure-devops | latest | Client Azure DevOps API |
| google-generativeai | latest | Client Google Gemini |
| pydantic | latest | Validazione e configurazione |
| msrest | latest | Azure REST authentication |

## 📄 Licenza

Consulta il file LICENSE del progetto.
