# Chat Session Management - REST API

Questa funzionalità permette di gestire conversazioni interattive per l'estrazione di PBI e progetti Azure DevOps tramite REST API.

## Funzionalità

Il sistema supporta la gestione di sessioni di chat in memoria con le seguenti capacità:

- ✅ Creazione di nuove sessioni di chat
- ✅ Aggiunta di messaggi a sessioni esistenti
- ✅ Visualizzazione di tutte le sessioni attive
- ✅ Recupero dettagli di una sessione specifica
- ✅ Eliminazione di sessioni
- ✅ Elaborazione di conversazioni per estrarre PBI e progetti
- ✅ Supporto per conversazioni interattive con domande e risposte

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
Aggiunge un messaggio a una sessione esistente.

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

### 5. `DELETE /chat/sessions/{chat_id}`
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

### 6. `POST /chat/sessions/{chat_id}/process`
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

## Flusso di Lavoro Tipico

1. **Crea una nuova sessione:**
   ```bash
   curl -X POST http://localhost:8000/chat/sessions
   # → Restituisce: {"chat_id": "...", "message": "..."}
   ```

2. **Aggiungi messaggi alla conversazione:**
   ```bash
   curl -X POST http://localhost:8000/chat/sessions/{chat_id}/messages \
     -H "Content-Type: application/json" \
     -d '{"role": "user", "content": "Voglio creare PBI per progetto X"}'
   
   curl -X POST http://localhost:8000/chat/sessions/{chat_id}/messages \
     -H "Content-Type: application/json" \
     -d '{"role": "assistant", "content": "Che funzionalità vuoi implementare?"}'
   
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
