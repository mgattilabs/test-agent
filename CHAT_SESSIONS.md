# Chat Session Management

Questa funzionalità permette di gestire conversazioni interattive per l'estrazione di PBI e progetti Azure DevOps.

## Funzionalità

Il sistema supporta ora la gestione di sessioni di chat in memoria con le seguenti capacità:

- ✅ Creazione di nuove sessioni di chat
- ✅ Aggiunta di messaggi a sessioni esistenti
- ✅ Visualizzazione di tutte le sessioni attive
- ✅ Recupero dettagli di una sessione specifica
- ✅ Eliminazione di sessioni
- ✅ Elaborazione di conversazioni per estrarre PBI e progetti
- ✅ Supporto per conversazioni interattive con domande e risposte

## Strumenti MCP Disponibili

### 1. `create_chat_session()`
Crea una nuova sessione di chat.

**Ritorna:** ID della nuova sessione creata

**Esempio:**
```
Sessione di chat creata con ID: a1b2c3d4-5678-90ef-ghij-klmnopqrstuv
```

### 2. `add_message_to_chat(chat_id, role, content)`
Aggiunge un messaggio a una sessione esistente.

**Parametri:**
- `chat_id`: ID della sessione di chat
- `role`: Ruolo del mittente (`user`, `assistant`, `system`)
- `content`: Contenuto del messaggio

**Esempio:**
```python
add_message_to_chat(
    chat_id="a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
    role="user",
    content="Voglio creare dei PBI per il progetto WebApp"
)
```

### 3. `list_chat_sessions()`
Elenca tutte le sessioni di chat attive con informazioni riassuntive.

**Ritorna:** Lista di sessioni con dettagli (ID, numero messaggi, progetto, PBI, status, data creazione)

### 4. `get_chat_session(chat_id)`
Recupera i dettagli completi di una sessione specifica, inclusa la cronologia messaggi.

**Parametri:**
- `chat_id`: ID della sessione di chat

**Ritorna:** Dettagli completi della sessione con tutti i messaggi

### 5. `delete_chat_session(chat_id)`
Elimina una sessione di chat.

**Parametri:**
- `chat_id`: ID della sessione da eliminare

**Ritorna:** Conferma dell'eliminazione

### 6. `process_chat_session(chat_id, create_pbis=True)`
Elabora la cronologia di una chat per estrarre PBI e progetto Azure DevOps.

**Parametri:**
- `chat_id`: ID della sessione da elaborare
- `create_pbis`: Se `True`, crea i PBI in Azure DevOps (default: `True`)

**Ritorna:** Risultato dell'elaborazione con dettagli sui PBI estratti

**Esempio:**
```python
process_chat_session(
    chat_id="a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
    create_pbis=True
)
```

## Flusso di Lavoro Tipico

1. **Crea una nuova sessione:**
   ```
   create_chat_session()
   → Restituisce: chat_id
   ```

2. **Aggiungi messaggi alla conversazione:**
   ```
   add_message_to_chat(chat_id, "user", "Voglio creare PBI per progetto X")
   add_message_to_chat(chat_id, "assistant", "Che funzionalità vuoi implementare?")
   add_message_to_chat(chat_id, "user", "Sistema di login e dashboard")
   ```

3. **Visualizza la conversazione:**
   ```
   get_chat_session(chat_id)
   ```

4. **Elabora la conversazione:**
   ```
   process_chat_session(chat_id, create_pbis=True)
   → Estrae PBI dalla conversazione e li crea in Azure DevOps
   ```

5. **Opzionale - Elimina la sessione:**
   ```
   delete_chat_session(chat_id)
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

## Funzione Legacy

### `process_azdo_summary(summary)`
La funzione originale è ancora disponibile per l'elaborazione diretta di riassunti senza gestione di sessioni.

**Quando usare:**
- Per elaborazioni one-shot senza conversazione interattiva
- Quando si ha già un riassunto completo da elaborare

**Quando usare le chat sessions:**
- Per conversazioni interattive
- Quando servono chiarimenti o domande
- Per costruire gradualmente i requisiti
