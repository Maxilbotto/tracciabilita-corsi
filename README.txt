## Importazione del database

1. Apri phpMyAdmin.
2. Crea un nuovo database chiamato `tracciabilita_corsi`.
3. Seleziona il database appena creato.
4. Vai nella scheda **"Importa"**.
5. Carica il file `tracciabilita_corsi.sql` incluso nel progetto.
6. Clicca su **"Esegui"** per importare.

Assicurati che il file `config.py` (o `.env`) punti a questo database.

ISTRUZIONI DETTAGLIATE:

Tracciabilità Corsi - Applicazione Web Flask
============================================

Questa applicazione permette di gestire corsi, dipendenti e partecipazioni. È sviluppata in Python con il micro-framework Flask e utilizza un database MySQL.

REQUISITI
---------
- Python 3.8 o superiore
- MySQL Server (ad esempio con phpMyAdmin)
- pip (Python package manager)
- virtualenv (opzionale, ma consigliato)

INSTALLAZIONE
-------------

1. Estrai il contenuto dello ZIP in una cartella locale.

2. Crea un ambiente virtuale (facoltativo ma consigliato):
   - Windows:
     python -m venv venv
     venv\Scripts\activate
   - Linux/macOS:
     python3 -m venv venv
     source venv/bin/activate

3. Installa i pacchetti richiesti:
   pip install -r requirements.txt

4. Configura il file delle variabili d'ambiente:
   - Copia il file `.env.example` e rinominalo in `.env`
   - Modifica i valori con le credenziali del tuo database MySQL:

     DB_USER=il_tuo_utente_mysql
     DB_PASSWORD=la_tua_password

5. Crea il database:
   - Nome: tracciabilita_corsi
   - Importa il file `tracciabilita_corsi.sql` tramite phpMyAdmin oppure via terminale:

     mysql -u [utente] -p tracciabilita_corsi < tracciabilita_corsi.sql

6. Avvia l'applicazione:
   flask run

   L'app sarà accessibile da:
   http://127.0.0.1:5000


STRUTTURA DEL PROGETTO
-----------------------
tracciabilita-corsi/
├── app.py
├── templates/
├── static/
├── tracciabilita_corsi.sql
├── requirements.txt
├── .env.example
└── readme.txt

TECNOLOGIE USATE
----------------
- Python
- Flask
- MySQL
- HTML + CSS
- Bootstrap
- Jinja2 (templating)
- phpMyAdmin (per gestione database)

LICENZA
-------
Questo progetto è distribuito sotto licenza MIT.

