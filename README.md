# MyFit Journal

Applicazione fitness con backend Python (`FastAPI`) e PostgreSQL.

## Funzionalita MVP
- Registrazione e login utente con sessione autenticata.
- Ogni utente vede solo i propri allenamenti, sessioni e statistiche.
- Vista mobile `/today` per visualizzare la scheda del giorno e registrare sessioni.
- Vista desktop `/workouts` per:
  - creare template allenamento riutilizzabili,
  - definire dettagli sport-specifici (nuoto, sala pesi, corsa),
  - scegliere esercizi da catalogo DB con autocomplete (zona muscolare automatica),
  - gestire corsi con sola durata,
  - associare allenamenti al calendario con ricorrenza settimanale.
- Mappa corpo fronte/retro con evidenza aree coinvolte dagli esercizi.
- Dashboard `/dashboard` con indicatori settimanali e trend ultimi 7 giorni.
- Schema PostgreSQL dedicato: `myfit`.

## Struttura
- `app/main.py`: routing e pagine.
- `app/models.py`: modelli SQLAlchemy.
- `app/services.py`: logica applicativa.
- `app/templates`: pagine Jinja2.
- `app/static`: CSS/JS.
- `deploy/`: unit `systemd` e config `nginx`.

## Setup locale
1. Crea ambiente virtuale:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Crea file ambiente:
   ```bash
   cp .env.example .env
   ```
   Imposta una `SECRET_KEY` lunga e casuale in produzione.
   Se pubblichi su HTTP interno (senza TLS), usa `SESSION_HTTPS_ONLY=false`.
   Se passi a HTTPS, imposta `SESSION_HTTPS_ONLY=true`.
3. Avvia app:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 3500
   ```

## Deploy Ubuntu (server)
1. Copia progetto in `/opt/my_fit_journal`.
2. Configura `.env` in `/opt/my_fit_journal/.env`.
3. Installa dipendenze in venv.
4. Copia unit file:
   ```bash
   sudo cp deploy/systemd/myfit-journal.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now myfit-journal
   ```
5. Configura nginx:
   ```bash
   sudo cp deploy/nginx/myfit-journal.conf /etc/nginx/sites-available/myfit-journal.conf
   sudo ln -s /etc/nginx/sites-available/myfit-journal.conf /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

Con questa configurazione l'app e raggiungibile su `http://IP_SERVER:3500`.

## Connessione DB richiesta
Nel file `.env` sono previsti questi valori:
- `DB_HOST=192.168.1.135`
- `DB_NAME=myfitjournal`
- `DB_SCHEMA=myfit`
- `DB_USER=miky2184`
- `DB_PASSWORD=kkpo2981`

Allo startup l'app crea lo schema `myfit` (se non esiste) e le tabelle necessarie.
Se esistono tabelle legacy senza ownership utente, l'app aggiunge i campi `user_id`
automaticamente e assegna i dati storici a un utente tecnico `legacy@myfit.local`.
Le pianificazioni ricorrenti sono salvate in `workout_schedules`.
