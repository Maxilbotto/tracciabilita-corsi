# Copyright (c) 2025 Massimiliano Bottoli
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import csv
import os
from io import StringIO
from io import TextIOWrapper  # Importa TextIOWrapper
from flask import render_template, request, redirect, url_for, Response, send_from_directory, jsonify, flash
from datetime import datetime
import mysql.connector
from werkzeug.utils import secure_filename

from flask import Flask

app = Flask(__name__)
# Aggiungi questa riga per inizializzare il supporto per i messaggi flash
app.secret_key = 'QuestaEUnaChiaveTemporanea123'  # Sostituisci con una chiave sicura e casuale

# Configurazione del database MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'tracciabilita_corsi'

def get_db():
    """Funzione per stabilire e ottenere una connessione al database."""
    try:
        mydb = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        return mydb
    except mysql.connector.Error as err:
        print(f"Errore nella connessione al database: {err}")
        return None

UPLOAD_FOLDER = 'uploads'  # Definisci la cartella dove salvare i file
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}  # Definisci le estensioni consentite
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/carica_dipendenti_csv', methods=['POST'])
def carica_dipendenti_csv():
    errore_csv = None
    db = get_db()
    cursor_insert = None
    cursor_check = None
    try:
        if not db:
            flash('Impossibile connettersi al database.', 'danger')
            return render_template('aggiungi_dipendente.html')

        cursor_insert = db.cursor()

        if 'file_csv' not in request.files:
            errore_csv = 'Nessun file selezionato.'
            return render_template('aggiungi_dipendente.html', errore_csv=errore_csv)

        file = request.files['file_csv']

        if file.filename == '':
            errore_csv = 'Nessun file selezionato.'
            return render_template('aggiungi_dipendente.html', errore_csv=errore_csv)

        if file and file.filename.endswith('.csv'):
            csvfile = TextIOWrapper(file.stream, encoding='utf-8')
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                if not row:
                    print("Riga vuota trovata. Saltando.")
                    continue

                nome = row.get('nome')
                cognome = row.get('cognome')
                if nome and cognome:
                    try:  # Aggiunto un try-except interno
                        cursor_check = db.cursor()
                        query_check = "SELECT id_dipendente FROM dipendenti WHERE nome = %s AND cognome = %s"
                        values_check = (nome, cognome)
                        cursor_check.execute(query_check, values_check)
                        existing_dipendente = cursor_check.fetchone()
                        if cursor_check.with_rows:  # Consuma il risultato se presente
                            cursor_check.fetchall()
                    finally:
                        if cursor_check:
                            cursor_check.close()  # Chiudi il cursore *sempre*

                    if existing_dipendente:
                        flash(f'Avviso: Il dipendente "{nome} {cognome}" esiste già. Scegli un\'opzione.', 'warning')
                        return render_template('aggiungi_dipendente.html',
                                              nome_duplicato=nome,
                                              cognome_duplicato=cognome,
                                              nome_originale=nome,
                                              cognome_originale=cognome)
                    else:
                        query_insert = "INSERT INTO dipendenti (nome, cognome) VALUES (%s, %s)"
                        values_insert = (nome, cognome)
                        cursor_insert.execute(query_insert, values_insert)
                else:
                    print(f"Riga incompleta trovata. Saltando: {row}")
                    flash('Il file CSV deve contenere le colonne "nome" e "cognome". Alcune righe sono state saltate.', 'warning')
                    continue

            db.commit()
            return redirect(url_for('lista_dipendenti'))
        else:
            errore_csv = 'File non valido. Si prega di caricare un file CSV.'
    except mysql.connector.Error as e:
        if db:
            db.rollback()
        errore_csv = f'Errore durante la lettura del file CSV: {e}'
    except Exception as e:
        if db:
            db.rollback()
        errore_csv = f'Si è verificato un errore: {e}'
    finally:
        if cursor_insert:
            cursor_insert.close()
        if cursor_check:
            cursor_check.close()
        if db and db.is_connected():
            db.close()

    return render_template('aggiungi_dipendente.html', errore_csv=errore_csv)

@app.route('/sovrascrivi_dipendente', methods=['POST'])
def sovrascrivi_dipendente():
    db = get_db()
    if not db:
        flash('Impossibile connettersi al database.', 'danger')
        return redirect(url_for('aggiungi_dipendente'))  # O dove appropriato

    cursor = db.cursor()
    nome = request.form['nome']
    cognome = request.form['cognome']

    try:
        # Esegui l'UPDATE per sovrascrivere i dati esistenti
        query_update = "UPDATE dipendenti SET nome = %s, cognome = %s WHERE nome = %s AND cognome = %s"
        values_update = (nome, cognome, request.form['nome_originale'], request.form['cognome_originale'])
        cursor.execute(query_update, values_update)

        if cursor.rowcount > 0:
            db.commit()
            flash(f'Dipendente "{nome} {cognome}" sovrascritto con successo.', 'success')
        else:
            flash(f'Impossibile trovare il dipendente "{request.form['nome_originale']} {request.form['cognome_originale']}" per la sovrascrittura.', 'warning')

    except mysql.connector.Error as e:
        db.rollback()
        flash(f'Errore durante la sovrascrittura del dipendente: {e}', 'danger')

    finally:
        cursor.close()
        db.close()

    return redirect(url_for('aggiungi_dipendente'))  # O dove appropriato

@app.route('/cerca_corsi_live')
def cerca_corsi():
    query = request.args.get('q')
    risultati = []
    db = get_db()
    if db and query:
        cursor = db.cursor(dictionary=True)
        # Query con ricerca full-text
        sql_query = """
        SELECT id_corso, titolo
        FROM corsi_formazione
        WHERE MATCH(titolo) AGAINST (%s IN BOOLEAN MODE)
        LIMIT 10;
        """
        try:
            # Aggiunge wildcard * per ricerche parziali (es. "sic" trova "sicurezza")
            cursor.execute(sql_query, (query + '*',))
            risultati = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Errore durante la ricerca dei corsi: {err}")
        finally:
            cursor.close()
            db.close()
    return jsonify(risultati)


@app.route('/cerca_dipendenti')
def cerca_dipendenti():
    query = request.args.get('q')
    risultati = []
    db = get_db()
    if db and query:
        cursor = db.cursor(dictionary=True)
        # Utilizza la ricerca full-text
        sql_query = """
        SELECT id_dipendente, nome, cognome
        FROM dipendenti
        WHERE MATCH(nome, cognome) AGAINST (%s IN BOOLEAN MODE)
        LIMIT 10;
        """
        try:
            # Aggiunge il wildcard * per ottenere risultati parziali (es. "mar" → Mario)
            cursor.execute(sql_query, (query + '*',))
            risultati = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Errore durante la ricerca dei dipendenti: {err}")
        finally:
            cursor.close()
            db.close()
    return jsonify(risultati)

@app.route('/scarica_attestato/<filename>')
def scarica_attestato(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/test_db')
def test_db():
    db = get_db()
    if db:
        cursor = db.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        cursor.close()
        db.close()
        return f"Connessione al database riuscita! Risultato: {result}"
    else:
        return "Impossibile connettersi al database."

@app.route('/')
def index():
    crediti = {
        'autore': 'Massimiliano Bottoli',
        'anno': '2025',
        'email': 'massimiliano.bottoli@gmail.com',
        'organizzazione': 'Me, myself and I',
        'note': 'MIT License 2025 Massimiliano Bottoli - Per aggiungere colonne al database contattami e personalizzerò il software per le tue esigenze.'
    }
    return render_template('index.html', crediti=crediti)

@app.route('/dipendenti')
def lista_dipendenti():
    query = request.args.get('q')
    export = request.args.get('export')
    id_dipendente_filtro = request.args.get('id')  # Parametro per filtrare per ID
    db = get_db()
    dipendenti = []
    crediti = {
        'autore': 'Massimiliano Bottoli',
        'anno': '2025',
        'email': 'massimiliano.bottoli@gmail.com',
        'organizzazione': 'Me, myself and I',
        'note': 'MIT License 2025 Massimiliano Bottoli - Per aggiungere colonne al database contattami e personalizzerò il software per le tue esigenze.'
    }
    if db:
        cursor = db.cursor(dictionary=True)
        sql_query = "SELECT id_dipendente, nome, cognome FROM dipendenti"
        where_clause = ""
        values = ()

        if id_dipendente_filtro:  # Se è presente un ID, filtra per ID
            where_clause = " WHERE id_dipendente = %s"
            values = (id_dipendente_filtro,)
        elif query:  # Altrimenti, filtra per nome/cognome
            search_term = f"%{query}%"
            where_clause = " WHERE nome LIKE %s OR cognome LIKE %s"
            values = (search_term, search_term)

        full_query = sql_query + where_clause + " ORDER BY nome, cognome;"
        print(f"Query: {full_query}, Valori: {values}")  # Debug

        try:
            cursor.execute(full_query, values)
            dipendenti = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Errore database: {err}")
            flash(f"Errore database: {err}", 'danger') # Mostra l'errore all'utente
        finally:
            cursor.close()
            db.close()

        if export:
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID Dipendente', 'Nome', 'Cognome'])
            for dipendente in dipendenti:
                writer.writerow([dipendente['id_dipendente'], dipendente['nome'], dipendente['cognome']])
            csv_output = output.getvalue()
            return Response(csv_output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=dipendenti.csv'})

        return render_template('lista_dipendenti.html', dipendenti=dipendenti, query=query, id_dipendente_filtro=id_dipendente_filtro, crediti=crediti)
    else:
        flash("Impossibile connettersi al database per visualizzare i dipendenti.", 'danger')
        return render_template('lista_dipendenti.html', dipendenti=[], query=query, id_dipendente_filtro=id_dipendente_filtro, crediti=crediti)

@app.route('/corsi')
def lista_corsi():
    query = request.args.get('q')
    export = request.args.get('export')
    db = get_db()
    crediti = {  # Definisci il dizionario crediti
        'autore': 'Massimiliano Bottoli',
        'anno': '2025',
        'email': 'massimiliano.bottoli@gmail.com',
        'organizzazione': 'Me, myself and I',
        'note': 'MIT License 2025 Massimiliano Bottoli - Per aggiungere colonne al database contattami e personalizzerò il software per le tue esigenze.'
    }
    if db:
        cursor = db.cursor(dictionary=True)
        sql_query = "SELECT id_corso, titolo, numero_ore, ente_erogatore, descrizione, tipologia, data_inizio, data_fine, costo FROM corsi_formazione"
        where_clause = ""
        values = ()
        if query:
            search_term = f"%{query}%"
            where_clause = " WHERE titolo LIKE %s OR ente_erogatore LIKE %s"
            values = (search_term, search_term)
            cursor.execute(sql_query + where_clause + " ORDER BY titolo;", values)
            corsi = cursor.fetchall()
        else:
            cursor.execute(sql_query + " ORDER BY titolo;")
            corsi = cursor.fetchall()
        cursor.close()
        db.close()

        if export:
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID Corso', 'Titolo', 'Numero Ore', 'Ente Erogatore', 'Descrizione', 'Tipologia', 'Data Inizio', 'Data Fine', 'Costo'])
            for corso in corsi:
                writer.writerow([corso['id_corso'], corso['titolo'], corso['numero_ore'], corso['ente_erogatore'],
                                 corso.get('descrizione', ''), corso.get('tipologia', ''),
                                 corso.get('data_inizio', ''), corso.get('data_fine', ''), corso.get('costo', '')])
            csv_output = output.getvalue()
            return Response(csv_output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=corsi.csv'})

        return render_template('lista_corsi.html', corsi=corsi, query=query, crediti=crediti) # Passa crediti
    else:
        return "Impossibile connettersi al database per visualizzare i corsi."

@app.route('/aggiungi_dipendente', methods=['GET', 'POST'])
def aggiungi_dipendente():
    errore = None
    crediti = {
        'autore': 'Massimiliano Bottoli',
        'anno': '2025',
        'email': 'massimiliano.bottoli@gmail.com',
        'organizzazione': 'Me, myself and I',
        'note': 'MIT License 2025 Massimiliano Bottoli - Per aggiungere colonne al database contattami e personalizzerò il software per le tue esigenze.'
    }
    if request.method == 'POST':
        nome = request.form['nome']
        cognome = request.form['cognome']

        if not nome:
            errore = 'Il nome è obbligatorio.'
        elif not cognome:
            errore = 'Il cognome è obbligatorio.'
        else:
            db = get_db()
            if db:
                cursor = db.cursor()
                query = "INSERT INTO dipendenti (nome, cognome) VALUES (%s, %s)"
                values = (nome, cognome)
                cursor.execute(query, values)
                db.commit()
                cursor.close()
                db.close()
                return redirect(url_for('lista_dipendenti')) # Reindirizza dopo l'aggiunta
            else:
                errore = 'Impossibile connettersi al database per aggiungere il dipendente.'

    return render_template('aggiungi_dipendente.html', errore=errore, crediti=crediti) # Mostra il form (con o senza errore)

@app.route('/aggiungi_corso', methods=['GET', 'POST'])
def aggiungi_corso():
    errore = None
    crediti = {  # Definisci il dizionario crediti
        'autore': 'Massimiliano Bottoli',
        'anno': '2025',
        'email': 'massimiliano.bottoli@gmail.com',
        'organizzazione': 'Me, myself and I',
        'note': 'MIT License 2025 Massimiliano Bottoli - Per aggiungere colonne al database contattami e personalizzerò il software per le tue esigenze.'
    }
    if request.method == 'POST':
        titolo = request.form['titolo']
        ore_str = request.form['ore']
        minuti_str = request.form['minuti']
        ente_erogatore = request.form['ente_erogatore']
        descrizione = request.form.get('descrizione')
        tipologia = request.form.get('tipologia')
        data_inizio = request.form.get('data_inizio')
        data_fine = request.form.get('data_fine')
        costo_str = request.form.get('costo')

        if not titolo:
            errore = 'Il titolo del corso è obbligatorio.'
        elif not ore_str:
            errore = 'Le ore sono obbligatorie.'
        elif not minuti_str:
            errore = 'I minuti sono obbligatori.'
        elif not ente_erogatore:
            errore = 'L\'ente erogatore è obbligatorio.'
        else:
            try:
                ore = int(ore_str)
                minuti = int(minuti_str)
                if minuti < 0 or minuti > 59:
                    errore = 'I minuti devono essere compresi tra 0 e 59.'

                durata_minuti = ore * 60 + minuti
                costo = float(costo_str) if costo_str else None

                # Gestisci le date vuote
                data_inizio_db = data_inizio if data_inizio else None
                data_fine_db = data_fine if data_fine else None

                db = get_db()
                if db and not errore: # Procedi solo se la connessione è ok e non ci sono errori di validazione
                    cursor = db.cursor()
                    query = """
                    INSERT INTO corsi_formazione (titolo, numero_ore, ente_erogatore, descrizione, tipologia, data_inizio, data_fine, costo, durata_minuti)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    # Calcola numero_ore come float per retrocompatibilità
                    numero_ore_float = durata_minuti / 60.0 if durata_minuti is not None else None
                    values = (titolo, numero_ore_float, ente_erogatore, descrizione, tipologia, data_inizio_db, data_fine_db, costo, durata_minuti)
                    cursor.execute(query, values)
                    db.commit()
                    cursor.close()
                    db.close()
                    return redirect(url_for('lista_corsi')) # Reindirizza alla pagina dei corsi dopo l'aggiunta
                elif not db:
                    errore = 'Impossibile connettersi al database per aggiungere il corso.'

            except ValueError:
                errore = 'Le ore e i minuti devono essere numeri interi validi.'
            except Exception as e:
                errore = f'Si è verificato un errore: {e}'

    return render_template('aggiungi_corso.html', errore=errore, crediti=crediti) # Passa crediti al template

@app.route('/registra_partecipazione', methods=['GET', 'POST'])
def registra_partecipazione():
    errore = None
    db = get_db()
    dipendenti = []
    corsi = []
    cursor = None  # Inizializza il cursore
    crediti = {  # Definisci il dizionario crediti
        'autore': 'Massimiliano Bottoli',
        'anno': '2025',
        'email': 'massimiliano.bottoli@gmail.com',
        'organizzazione': 'Me, myself and I',
        'note': 'MIT License 2025 Massimiliano Bottoli - Per aggiungere colonne al database contattami e personalizzerò il software per le tue esigenze.'
    }

    try:
        if db:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT id_dipendente, nome, cognome FROM dipendenti ORDER BY nome, cognome;")
            dipendenti = cursor.fetchall()
            cursor.execute("SELECT id_corso, titolo FROM corsi_formazione ORDER BY titolo;")
            corsi = cursor.fetchall()

            if request.method == 'POST':
                id_dipendente_str = request.form['id_dipendente']
                id_corso_str = request.form['id_corso']
                data_completamento_str = request.form['data_completamento']
                certificato_allegato_testo = request.form.get('certificato_allegato')
                data_scadenza_certificazione_str = request.form.get('data_scadenza_certificazione')
                costo_sostenuto_str = request.form.get('costo_sostenuto')
                note = request.form.get('note')

                certificato_allegato_filename = certificato_allegato_testo  # Inizializza con il valore testuale

                if 'certificato_allegato_file' in request.files:
                    file = request.files['certificato_allegato_file']
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        certificato_allegato_filename = filename  # Usa il nome del file caricato

                if not id_dipendente_str:
                    errore = 'Seleziona un dipendente.'
                elif not id_corso_str:
                    errore = 'Seleziona un corso.'
                elif not data_completamento_str:
                    errore = 'La data di completamento è obbligatoria.'
                else:
                    try:
                        id_dipendente = int(id_dipendente_str)
                        id_corso = int(id_corso_str)
                        data_completamento = datetime.strptime(data_completamento_str, '%Y-%m-%d').date()
                        data_scadenza_certificazione = datetime.strptime(data_scadenza_certificazione_str, '%Y-%m-%d').date() if data_scadenza_certificazione_str else None
                        costo_sostenuto = float(costo_sostenuto_str) if costo_sostenuto_str else None

                        query = "INSERT INTO partecipazioni (id_dipendente, id_corso, data_completamento, certificato_allegato, data_scadenza_certificazione, costo_sostenuto, note) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                        values = (id_dipendente, id_corso, data_completamento, certificato_allegato_filename, data_scadenza_certificazione, costo_sostenuto, note)
                        cursor.execute(query, values)
                        db.commit()
                        return redirect(url_for('lista_partecipazioni'))
                    except ValueError:
                        errore = 'Formato della data non valido (AAAA-MM-GG).'
                    except Exception as e:
                        errore = f'Si è verificato un errore durante l\'inserimento: {e}'
        else:
            errore = "Impossibile connettersi al database."

    finally:
        if db and db.is_connected():
            if cursor:
                cursor.close()
            db.close()

    return render_template('registra_partecipazione.html', dipendenti=dipendenti, corsi=corsi, errore=errore, crediti=crediti)

@app.route('/lista_partecipazioni')
def lista_partecipazioni():
    query = request.args.get('ricerca_dipendente')
    export = request.args.get('export')
    sort_by = request.args.get('sort')
    order = request.args.get('order')
    filtro_dipendente = request.args.get('filtro_dipendente')  # Corretto: filtro_dipendente
    print("DEBUG: filtro_dipendente ricevuto dal browser:", filtro_dipendente)
    filtro_corso = request.args.get('filtro_corso')

    print(f"DEBUG: Parametri - query: '{query}', filtro_dipendente: '{filtro_dipendente}', filtro_corso: '{filtro_corso}'")

    db = get_db()
    partecipazioni = []
    tutti_dipendenti = []
    tutti_corsi = []
    crediti = {
        'autore': 'Massimiliano Bottoli',
        'anno': '2025',
        'email': 'massimiliano.bottoli@gmail.com',
        'organizzazione': 'Me, myself and I',
        'note': 'MIT License 2025 Massimiliano Bottoli - Per aggiungere colonne al database contattami e personalizzerò il software per le tue esigenze.'
    }
    if db:
        cursor = db.cursor(dictionary=True)
        sql_query = """
            SELECT
                p.id_partecipazione,
                d.nome AS nome_dipendente,
                d.cognome AS cognome_dipendente,
                c.titolo AS titolo_corso,
                p.data_completamento,
                p.certificato_allegato,
                p.data_scadenza_certificazione,
                p.costo_sostenuto,
                p.note
            FROM partecipazioni p
            JOIN dipendenti d ON p.id_dipendente = d.id_dipendente
            JOIN corsi_formazione c ON p.id_corso = c.id_corso            
        """
        where_conditions = []  # Usa una lista per le condizioni WHERE
        values = []  # Usa una lista per i valori
        order_by_clause = " ORDER BY p.data_completamento DESC"

        if query and not filtro_dipendente and not filtro_corso:
            search_term = f"%{query}%"
            where_conditions.append("(d.nome LIKE %s OR d.cognome LIKE %s OR c.titolo LIKE %s)")
            values.extend([search_term, search_term, search_term])  # Usa extend

        if filtro_dipendente:  # Corretto: filtro_dipendente
            where_conditions.append("p.id_dipendente = %s")
            values.append(filtro_dipendente)  # Usa append

        if filtro_corso:
            where_conditions.append("p.id_corso = %s")
            values.append(filtro_corso)  # Usa append

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)  # Costruisci WHERE dinamicamente

        if sort_by:
            if sort_by == 'dipendente':
                order_by_clause = " ORDER BY d.nome"
                if order == 'desc':
                    order_by_clause += " DESC"
            elif sort_by == 'corso':
                order_by_clause = " ORDER BY c.titolo"
                if order == 'desc':
                    order_by_clause += " DESC"
            elif sort_by == 'data_completamento':
                order_by_clause = " ORDER BY p.data_completamento"
                if order == 'desc':
                    order_by_clause += " DESC"

        full_query = sql_query + where_clause + order_by_clause + ";"

        print("------------------------------------------------")
        print(f"DEBUG: Query finale: {full_query}")
        print(f"DEBUG: Valori finali: {values}")
        print("------------------------------------------------")

        try:
            cursor.execute(full_query, tuple(values))  # Esegui con una tupla
            partecipazioni = cursor.fetchall()
            print(f"DEBUG: Risultati: {partecipazioni}")
        except mysql.connector.Error as err:
            print(f"Errore database (partecipazioni): {err}")
            flash(f"Errore database (partecipazioni): {err}", 'danger')

        # Recupera tutti i dipendenti per il filtro
        cursor_dipendenti = db.cursor(dictionary=True)
        try:
            cursor_dipendenti.execute("SELECT id_dipendente, nome, cognome FROM dipendenti ORDER BY nome, cognome;")
            tutti_dipendenti = cursor_dipendenti.fetchall()
        except mysql.connector.Error as err:
            print(f"Errore database (dipendenti): {err}")
            flash(f"Errore database (dipendenti): {err}", 'danger')
        finally:
            cursor_dipendenti.close()

        # Recupera tutti i corsi per il filtro
        cursor_corsi = db.cursor(dictionary=True)
        try:
            cursor_corsi.execute("SELECT id_corso, titolo FROM corsi_formazione ORDER BY titolo;")
            tutti_corsi = cursor_corsi.fetchall()
        except mysql.connector.Error as err:
            print(f"Errore database (corsi): {err}")
            flash(f"Errore database (corsi): {err}", 'danger')
        finally:
            cursor_corsi.close()

        db.close()

        if export:
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID Partecipazione', 'Nome Dipendente', 'Cognome Dipendente', 'Titolo Corso',
                             'Data Completamento', 'Certificato Allegato', 'Data Scadenza Certificazione',
                             'Costo Sostenuto', 'Note'])
            for partecipazione in partecipazioni:
                writer.writerow([partecipazione['id_partecipazione'], partecipazione['nome_dipendente'],
                                 partecipazione['cognome_dipendente'], partecipazione['titolo_corso'],
                                 partecipazione.get('data_completamento', ''),
                                 partecipazione.get('certificato_allegato', ''),
                                 partecipazione.get('data_scadenza_certificazione', ''),
                                 partecipazione.get('costo_sostenuto', ''),
                                 partecipazione.get('note', '')])
            csv_output = output.getvalue()
            return Response(csv_output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=partecipazioni.csv'})

        return render_template('lista_partecipazioni.html', partecipazioni=partecipazioni, query=query, sort=sort_by, order=order,
                                 tutti_dipendenti=tutti_dipendenti, tutti_corsi=tutti_corsi,
                                 filtro_dipendente=filtro_dipendente, filtro_corso=filtro_corso, crediti=crediti)  # Corretto: filtro_dipendente
    else:
        return "Impossibile connettersi al database per visualizzare le partecipazioni."

@app.route('/elimina_dipendente/<int:id_dipendente>')
def elimina_dipendente(id_dipendente):
    db = get_db()
    if db:
        cursor = db.cursor()
        elimina_partecipazioni = request.args.get('elimina_partecipazioni') == 'true'

        try:
            if elimina_partecipazioni:
                # Elimina prima le partecipazioni
                cursor.execute("DELETE FROM partecipazioni WHERE id_dipendente = %s", (id_dipendente,))
                db.commit()
                flash("Partecipazioni del dipendente eliminate.", 'info')

            # Poi elimina il dipendente
            cursor.execute("DELETE FROM dipendenti WHERE id_dipendente = %s", (id_dipendente,))
            db.commit()
            flash("Dipendente eliminato con successo.", 'success')

        except mysql.connector.Error as err:
            db.rollback()
            flash(f"Errore durante l'eliminazione: {err}", 'danger')
        finally:
            cursor.close()
            db.close()
        return redirect(url_for('lista_dipendenti'))
    else:
        return "Impossibile connettersi al database per eliminare il dipendente."

@app.route('/elimina_corso/<int:id_corso>')
def elimina_corso(id_corso):
    elimina_partecipazioni = request.args.get('elimina_partecipazioni') == 'true'
    db = get_db()
    if db:
        cursor = db.cursor()
        try:
            if elimina_partecipazioni:
                cursor.execute("DELETE FROM partecipazioni WHERE id_corso = %s", (id_corso,))
                db.commit()
                flash('Corso e partecipazioni associate eliminate con successo.', 'success')
            else:
                flash('Corso eliminato con successo.', 'success')
            query = "DELETE FROM corsi_formazione WHERE id_corso = %s"
            cursor.execute(query, (id_corso,))
            db.commit()

        except mysql.connector.Error as e:
            db.rollback()
            flash(f'Errore durante l\'eliminazione del corso: {e}', 'danger')
        finally:
            cursor.close()
            db.close()
        return redirect(url_for('lista_corsi'))
    else:
        flash('Impossibile connettersi al database per eliminare il corso.', 'danger')
        return redirect(url_for('lista_corsi'))

@app.route('/elimina_partecipazione/<int:id_partecipazione>')
def elimina_partecipazione(id_partecipazione):
    db = get_db()
    if db:
        cursor = db.cursor()
        query = "DELETE FROM partecipazioni WHERE id_partecipazione = %s"
        cursor.execute(query, (id_partecipazione,))
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('lista_partecipazioni'))
    else:
        return "Impossibile connettersi al database per eliminare la partecipazione."


@app.route('/modifica_dipendente/<int:id_dipendente>', methods=['GET', 'POST'])
def modifica_dipendente(id_dipendente):
    errore = None
    db = get_db()
    cursor = db.cursor(dictionary=True) if db else None
    dipendente = None

    if db and cursor:
        if request.method == 'POST':
            nome = request.form['nome']
            cognome = request.form['cognome']

            if not nome:
                errore = 'Il nome è obbligatorio.'
            elif not cognome:
                errore = 'Il cognome è obbligatorio.'
            else:
                query = "UPDATE dipendenti SET nome = %s, cognome = %s WHERE id_dipendente = %s"
                values = (nome, cognome, id_dipendente)
                cursor.execute(query, values)
                db.commit()
                cursor.close()
                db.close()
                return redirect(url_for('lista_dipendenti'))
        else: # Metodo GET: mostra il form precompilato
            cursor.execute("SELECT id_dipendente, nome, cognome FROM dipendenti WHERE id_dipendente = %s", (id_dipendente,))
            dipendente = cursor.fetchone()
            cursor.close()
            db.close()
            if not dipendente:
                return "Dipendente non trovato."

        return render_template('modifica_dipendente.html', dipendente=dipendente, errore=errore)
    else:
        return "Impossibile connettersi al database."

@app.route('/modifica_corso/<int:id_corso>', methods=['GET', 'POST'])
def modifica_corso(id_corso):
    errore = None
    db = get_db()
    cursor = db.cursor(dictionary=True) if db else None
    corso = None

    if db and cursor:
        if request.method == 'POST':
            titolo = request.form['titolo']
            ore_str = request.form['ore']
            minuti_str = request.form['minuti']
            ente_erogatore = request.form['ente_erogatore']
            descrizione = request.form.get('descrizione')
            tipologia = request.form.get('tipologia')
            data_inizio = request.form.get('data_inizio') or None  # Se vuoto, imposta a None
            data_fine = request.form.get('data_fine') or None    # Se vuoto, imposta a None
            costo_str = request.form.get('costo') or None      # Se vuoto, imposta a None

            if not titolo:
                errore = 'Il titolo del corso è obbligatorio.'
            elif not ore_str:
                errore = 'Le ore sono obbligatorie.'
            elif not minuti_str:
                errore = 'I minuti sono obbligatori.'
            elif not ente_erogatore:
                errore = 'L\'ente erogatore è obbligatorio.'
            else:
                try:
                    ore = int(ore_str)
                    minuti = int(minuti_str)
                    if minuti < 0 or minuti > 59:
                        errore = 'I minuti devono essere compresi tra 0 e 59.'

                    durata_minuti = ore * 60 + minuti
                    costo = float(costo_str) if costo_str else None

                    if not errore:
                        query = """
                        UPDATE corsi_formazione
                        SET titolo = %s,
                            numero_ore = %s,
                            ente_erogatore = %s,
                            descrizione = %s,
                            tipologia = %s,
                            data_inizio = %s,
                            data_fine = %s,
                            costo = %s,
                            durata_minuti = %s
                        WHERE id_corso = %s
                        """
                        numero_ore_float = durata_minuti / 60.0 if durata_minuti is not None else None
                        values = (titolo, numero_ore_float, ente_erogatore, descrizione, tipologia, data_inizio, data_fine, costo, durata_minuti, id_corso)
                        cursor.execute(query, values)
                        db.commit()
                        cursor.close()
                        db.close()
                        return redirect(url_for('lista_corsi'))
                except ValueError:
                    errore = 'Le ore e i minuti devono essere numeri interi validi.'
                except Exception as e:
                    errore = f'Si è verificato un errore: {e}'
        else: # Metodo GET: mostra il form precompilato
            cursor.execute("SELECT id_corso, titolo, numero_ore, ente_erogatore, descrizione, tipologia, data_inizio, data_fine, costo, durata_minuti, FLOOR(durata_minuti / 60) AS ore, durata_minuti MOD 60 AS minuti FROM corsi_formazione WHERE id_corso = %s", (id_corso,))
            corso = cursor.fetchone()

        if corso:
            return render_template('modifica_corso.html', corso=corso, errore=errore)
        else:
            return "Corso non trovato."
    else:
        return "Impossibile connettersi al database."

@app.route('/modifica_partecipazione/<int:id_partecipazione>', methods=['GET', 'POST'])
def modifica_partecipazione(id_partecipazione):
    db = get_db()
    cursor = db.cursor(dictionary=True) if db else None
    partecipazione = None
    dipendenti = None
    corsi = None
    errore = None

    if db and cursor:
        # Recupera l'elenco dei dipendenti e dei corsi per il form
        cursor.execute("SELECT id_dipendente, nome, cognome FROM dipendenti ORDER BY nome, cognome;")
        dipendenti = cursor.fetchall()
        cursor.execute("SELECT id_corso, titolo FROM corsi_formazione ORDER BY titolo;")
        corsi = cursor.fetchall()

        if request.method == 'POST':
            id_dipendente = request.form['id_dipendente']
            id_corso = request.form['id_corso']
            data_completamento_str = request.form['data_completamento'] or None
            data_scadenza_certificazione_str = request.form.get('data_scadenza_certificazione') or None
            costo_sostenuto_str = request.form.get('costo_sostenuto') or None
            note = request.form.get('note') or None
            certificato_allegato_attuale = request.form.get('certificato_allegato') or None
            certificato_allegato_filename = certificato_allegato_attuale

            if 'certificato_allegato_file' in request.files:
                file = request.files['certificato_allegato_file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    certificato_allegato_filename = filename
                    # Potresti voler eliminare il vecchio file qui se lo desideri

            try:
                data_completamento = datetime.strptime(data_completamento_str, '%Y-%m-%d').date() if data_completamento_str else None
                data_scadenza_certificazione = datetime.strptime(data_scadenza_certificazione_str, '%Y-%m-%d').date() if data_scadenza_certificazione_str else None
                costo_sostenuto = float(costo_sostenuto_str) if costo_sostenuto_str else None

                query = """
                UPDATE partecipazioni
                SET id_dipendente = %s,
                    id_corso = %s,
                    data_completamento = %s,
                    certificato_allegato = %s,
                    data_scadenza_certificazione = %s,
                    costo_sostenuto = %s,
                    note = %s
                WHERE id_partecipazione = %s
                """
                values = (id_dipendente, id_corso, data_completamento, certificato_allegato_filename,
                          data_scadenza_certificazione, costo_sostenuto, note, id_partecipazione)
                cursor.execute(query, values)
                db.commit()
                cursor.close()
                db.close()
                return redirect(url_for('lista_partecipazioni'))
            except ValueError:
                errore = 'Formato della data non valido (AAAA-MM-GG).'
            except Exception as e:
                errore = f'Si è verificato un errore durante l\'aggiornamento: {e}'
        else: # Metodo GET: mostra il form precompilato
            query = "SELECT * FROM partecipazioni WHERE id_partecipazione = %s"
            cursor.execute(query, (id_partecipazione,))
            partecipazione = cursor.fetchone()
            cursor.close()
            db.close()
            if partecipazione:
                return render_template('modifica_partecipazione.html', partecipazione=partecipazione, dipendenti=dipendenti, corsi=corsi, errore=errore)
            else:
                return "Partecipazione non trovata."
    else:
        return "Impossibile connettersi al database."

@app.route('/salva_modifica_partecipazione/<int:id_partecipazione>', methods=['POST'])
def salva_modifica_partecipazione(id_partecipazione):
    errore = None
    db = get_db()
    cursor = None
    try:
        if db:
            cursor = db.cursor()
            id_dipendente = request.form['id_dipendente']
            id_corso = request.form['id_corso']
            data_completamento_str = request.form['data_completamento']
            data_scadenza_certificazione_str = request.form.get('data_scadenza_certificazione')
            costo_sostenuto_str = request.form.get('costo_sostenuto')
            note = request.form.get('note')
            certificato_allegato_attuale = request.form.get('certificato_allegato')
            certificato_allegato_filename = certificato_allegato_attuale  # Inizializza con il nome del file esistente

            if 'certificato_allegato_file' in request.files:
                file = request.files['certificato_allegato_file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    certificato_allegato_filename = filename
                    # Potresti voler eliminare il vecchio file qui se lo desideri

            try:
                data_completamento = datetime.strptime(data_completamento_str, '%Y-%m-%d').date() if data_completamento_str else None
                data_scadenza_certificazione = datetime.strptime(data_scadenza_certificazione_str, '%Y-%m-%d').date() if data_scadenza_certificazione_str else None
                costo_sostenuto = float(costo_sostenuto_str) if costo_sostenuto_str else None

                query = """
                UPDATE partecipazioni
                SET id_dipendente = %s,
                    id_corso = %s,
                    data_completamento = %s,
                    certificato_allegato = %s,
                    data_scadenza_certificazione = %s,
                    costo_sostenuto = %s,
                    note = %s
                WHERE id_partecipazione = %s
                """
                values = (id_dipendente, id_corso, data_completamento, certificato_allegato_filename,
                          data_scadenza_certificazione, costo_sostenuto, note, id_partecipazione)
                cursor.execute(query, values)
                db.commit()
                return redirect(url_for('lista_partecipazioni'))
            except ValueError:
                errore = 'Formato della data non valido (AAAA-MM-GG).'
            except Exception as e:
                errore = f'Si è verificato un errore durante l\'aggiornamento: {e}'
        else:
            errore = "Impossibile connettersi al database."
    except mysql.connector.Error as err:
        errore = f"Errore database: {err}"
    finally:
        if db and db.is_connected():
            if cursor:
                cursor.close()
            db.close()
    # Se c'è un errore, re-renderizza il form di modifica con il messaggio di errore
    db = get_db()
    partecipazione = None
    cursor_err = None
    try:
        if db:
            cursor_err = db.cursor(dictionary=True)
            cursor_err.execute("SELECT * FROM partecipazioni WHERE id_partecipazione = %s", (id_partecipazione,))
            partecipazione = cursor_err.fetchone()
    finally:
        if db and db.is_connected():
            if cursor_err:
                cursor_err.close()
            db.close()
    return render_template('modifica_partecipazione.html', partecipazione=partecipazione, dipendenti=dipendenti, corsi=corsi, errore=errore)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)