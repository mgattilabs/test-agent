# Chat Session Management - REST API

Questa funzionalità permette di gestire conversazioni interattive per l'estrazione di PBI e progetti Azure DevOps tramite REST API.

## Funzionalità

Il sistema supporta la gestione di sessioni di chat in memoria con le seguenti capacità:

- ✅ Creazione di nuove sessioni di chat
- ✅ **Analisi automatica durante l'aggiunta di messaggi** - Il sistema analizza la conversazione dopo ogni messaggio utente
- ✅ **Richiesta automatica di informazioni mancanti** - Se manca il progetto o i requisiti, il sistema chiede chiarimenti
- ✅ **Conferma prima della creazione PBI** - Quando le informazioni sono complete, richiede conferma prima di creare i PBI
- ✅ Visualizzazione di tutte le sessioni attive
- ✅ Recupero dettagli di una sessione specifica
- ✅ Eliminazione di sessioni
- ✅ Supporto per conversazioni interattive con domande e risposte

## Workflow Interattivo

Il nuovo workflow è completamente automatico:

1. **Utente aggiunge messaggio** → Sistema analizza automaticamente la conversazione
2. **Sistema valuta completezza**:
   - Se manca il progetto → Chiede il nome del progetto
   - Se mancano requisiti → Chiede di descrivere le funzionalità
   - Se tutto è presente → Richiede conferma per creare i PBI
3. **Utente conferma** → PBI creati automaticamente in Azure DevOps

## Endpoint API Disponibili

### 1. `POST /chat/sessions`
Crea una nuova sessione di chat.

**Risposta:**
```json
{
  "chat_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "message": "Sessione di chat creata con ID: a1b2c3d4-5678-90ef-ghij-klmnopqrstuv"
}
```

**Esempio curl:**
```bash
curl -X POST http://localhost:8000/chat/sessions
```

### 2. `POST /chat/sessions/{chat_id}/messages`
Aggiunge un messaggio a una sessione esistente. **NOVITÀ**: Se il messaggio è dall'utente, il sistema analizza automaticamente la conversazione e genera una risposta dell'assistente.

**Body:**
```json
{
  "role": "user",
  "content": "Voglio creare dei PBI per il progetto WebApp"
}
```

**Parametri:**
- `role`: Ruolo del mittente (`user`, `assistant`, `system`)
- `content`: Contenuto del messaggio

**Risposta:**
```json
{
  "message": "Messaggio aggiunto alla chat {chat_id}",
  "assistant_response": "Ho identificato il progetto 'WebApp', ma non ho ancora informazioni sufficienti...",
  "needs_confirmation": false,
  "session_status": "needs_info",
  "project": "WebApp",
  "pbi_count": 0
}
```

**Esempio curl:**
```bash
curl -X POST http://localhost:8000/chat/sessions/{chat_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"role": "user", "content": "Voglio creare dei PBI per il progetto WebApp"}'
```

### 3. `GET /chat/sessions`
Elenca tutte le sessioni di chat attive con informazioni riassuntive.

**Risposta:** Array di oggetti `ChatSessionSummary`

**Esempio curl:**
```bash
curl http://localhost:8000/chat/sessions
```

### 4. `GET /chat/sessions/{chat_id}`
Recupera i dettagli completi di una sessione specifica, inclusa la cronologia messaggi.

**Risposta:** Oggetto `ChatSession` completo

**Esempio curl:**
```bash
curl http://localhost:8000/chat/sessions/{chat_id}
```

### 5. `POST /chat/sessions/{chat_id}/confirm` ⭐ NUOVO
Conferma o rifiuta la creazione dei PBI estratti dalla conversazione. Questo endpoint viene utilizzato quando il sistema ha identificato progetto e PBI e richiede conferma.

**Body:**
```json
{
  "confirm": true
}
```

**Parametri:**
- `confirm`: `true` per confermare e creare i PBI, `false` per annullare

**Risposta (conferma):**
```json
{
  "message": "Creati con successo 3 PBI nel progetto 'WebApp'."
}
```

**Risposta (rifiuto):**
```json
{
  "message": "Creazione PBI annullata. Puoi continuare a modificare i requisiti."
}
```

**Esempio curl (conferma):**
```bash
curl -X POST http://localhost:8000/chat/sessions/{chat_id}/confirm \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

**Esempio curl (rifiuto):**
```bash
curl -X POST http://localhost:8000/chat/sessions/{chat_id}/confirm \
  -H "Content-Type: application/json" \
  -d '{"confirm": false}'
```

### 6. `DELETE /chat/sessions/{chat_id}`
Elimina una sessione di chat.

**Risposta:**
```json
{
  "message": "Sessione di chat {chat_id} eliminata con successo."
}
```

**Esempio curl:**
```bash
curl -X DELETE http://localhost:8000/chat/sessions/{chat_id}
```

### 7. `POST /chat/sessions/{chat_id}/process` (Legacy)
Elabora la cronologia di una chat per estrarre PBI e progetto Azure DevOps.

**Body:**
```json
{
  "create_pbis": true
}
```

**Parametri:**
- `create_pbis`: Se `true`, crea i PBI in Azure DevOps (default: `true`)

**Risposta:**
```json
{
  "message": "Elaborazione completata per chat {chat_id}. Estratti e creati N PBI nel progetto 'ProjectName'."
}
```

**Esempio curl:**
```bash
curl -X POST http://localhost:8000/chat/sessions/{chat_id}/process \
  -H "Content-Type: application/json" \
  -d '{"create_pbis": true}'
```

## Flusso di Lavoro Tipico (Nuovo Workflow Automatico)

### Esempio Completo di Conversazione

1. **Crea una nuova sessione:**
   ```bash
   curl -X POST http://localhost:8000/chat/sessions
   # → Restituisce: {"chat_id": "abc123", "message": "..."}
   ```

2. **Primo messaggio utente (manca info progetto):**
   ```bash
   curl -X POST http://localhost:8000/chat/sessions/abc123/messages \
     -H "Content-Type: application/json" \
     -d '{"role": "user", "content": "Voglio creare dei PBI"}'
   
   # Risposta automatica:
   # {
   #   "assistant_response": "Non ho identificato il progetto Azure DevOps. Puoi specificare il nome del progetto?",
   #   "session_status": "needs_info",
   #   "needs_confirmation": false
   # }
   ```

3. **Secondo messaggio utente (mancano requisiti):**
   ```bash
   curl -X POST http://localhost:8000/chat/sessions/abc123/messages \
     -H "Content-Type: application/json" \
     -d '{"role": "user", "content": "Il progetto è WebApp"}'
   
   # Risposta automatica:
   # {
   #   "assistant_response": "Ho identificato il progetto 'WebApp', ma non ho ancora informazioni sufficienti per creare PBI. Puoi descrivere le funzionalità?",
   #   "session_status": "needs_info",
   #   "project": "WebApp",
   #   "needs_confirmation": false
   # }
   ```

4. **Terzo messaggio utente (informazioni complete):**
   ```bash
   curl -X POST http://localhost:8000/chat/sessions/abc123/messages \
     -H "Content-Type: application/json" \
     -d '{"role": "user", "content": "Sistema di login con 2FA, dashboard vendite con grafici, gestione clienti CRUD"}'
   
   # Risposta automatica:
   # {
   #   "assistant_response": "Perfetto! Ho identificato il progetto 'WebApp' e ho estratto 3 PBI:\n1. Implementare sistema di login con 2FA\n2. Creare dashboard vendite con grafici\n3. Sviluppare gestione clienti CRUD\n\nVuoi che proceda con la creazione?",
   #   "session_status": "ready_for_confirmation",
   #   "project": "WebApp",
   #   "pbi_count": 3,
   #   "needs_confirmation": true
   # }
   ```

5. **Conferma creazione PBI:**
   ```bash
   curl -X POST http://localhost:8000/chat/sessions/abc123/confirm \
     -H "Content-Type: application/json" \
     -d '{"confirm": true}'
   
   # Risposta:
   # {
   #   "message": "Creati con successo 3 PBI nel progetto 'WebApp'."
   # }
   ```

### Note Importanti

- ⚠️ **Non è più necessario chiamare manualmente** `/process` - l'analisi è automatica
- ✅ Il sistema **aggiunge automaticamente** le risposte dell'assistente alla conversazione
- ✅ Il sistema **guida l'utente** chiedendo le informazioni mancanti
- ✅ La **conferma è richiesta** prima di creare PBI in Azure DevOps
   
   curl -X POST http://localhost:8000/chat/sessions/{chat_id}/messages \
     -H "Content-Type: application/json" \
     -d '{"role": "user", "content": "Sistema di login e dashboard"}'
   ```

3. **Visualizza la conversazione:**
   ```bash
   curl http://localhost:8000/chat/sessions/{chat_id}
   ```

4. **Elabora la conversazione:**
   ```bash
   curl -X POST http://localhost:8000/chat/sessions/{chat_id}/process \
     -H "Content-Type: application/json" \
     -d '{"create_pbis": true}'
   # → Estrae PBI dalla conversazione e li crea in Azure DevOps
   ```

5. **Opzionale - Elimina la sessione:**
   ```bash
   curl -X DELETE http://localhost:8000/chat/sessions/{chat_id}
   ```

## Modelli Dati

### ChatMessage
- `role`: Ruolo del mittente (user, assistant, system)
- `content`: Contenuto del messaggio
- `timestamp`: Data e ora del messaggio

### ChatSession
- `chat_id`: Identificatore univoco della sessione
- `messages`: Lista di messaggi nella conversazione
- `created_at`: Data di creazione
- `updated_at`: Data ultimo aggiornamento
- `project`: Progetto Azure DevOps identificato (opzionale)
- `pbis`: Lista di PBI estratti
- `status`: Stato della sessione (active, processing, completed, error)

## Note Tecniche

- Le sessioni sono memorizzate **in memoria** e non persistono tra i riavvii del server
- Il sistema utilizza DSPy con Gemini per l'estrazione intelligente di PBI e progetti
- La conversazione completa viene analizzata durante l'elaborazione
- Il sistema supporta conversazioni in italiano con risposte naturali

## Endpoint Legacy

### `POST /pbi-creator`
L'endpoint originale è ancora disponibile per l'elaborazione diretta di riassunti senza gestione di sessioni.

**Body:**
```json
{
  "summary": "Riassunto completo del progetto con tutti i requisiti..."
}
```

**Esempio curl:**
```bash
curl -X POST http://localhost:8000/pbi-creator \
  -H "Content-Type: application/json" \
  -d '{"summary": "Progetto WebApp: implementare login, dashboard e gestione utenti"}'
```

**Quando usare:**
- Per elaborazioni one-shot senza conversazione interattiva
- Quando si ha già un riassunto completo da elaborare

**Quando usare le chat sessions:**
- Per conversazioni interattive
- Quando servono chiarimenti o domande
- Per costruire gradualmente i requisiti
