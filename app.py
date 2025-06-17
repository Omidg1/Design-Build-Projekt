from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
import os
from werkzeug.utils import secure_filename
from database import get_db_connection
from datetime import datetime
from flask import send_from_directory

SERVER_URL = "http://80.198.171.108:60070"
app = Flask(__name__)
app.secret_key = 'hemmelig_nøgle'  # udskift i produktion!
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ------------------ LOGIN & OPRET ------------------

@app.route('/')
def home():
    return render_template('patient-login.html')

@app.route('/login', methods=['POST'])
def login():
    cpr = request.form['cpr-nummer']
    password = request.form['adgangskode']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM patient_users WHERE cpr_nummer = %s AND password = %s", (cpr, password))
    bruger = cursor.fetchone()
    
    if bruger:
        session['user_id'] = bruger[0]
        return redirect('/menu')
    else:
        return "Login mislykkedes"

@app.route('/opret', methods=['GET', 'POST'])
def opret():
    if request.method == 'GET':
        return render_template('opret-bruger.html')

    cpr = request.form['cpr-nummer']
    adgangskode = request.form['adgangskode']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO patient_users (cpr_nummer, password) VALUES (%s, %s)", (cpr, adgangskode))
        conn.commit()
    except mysql.connector.Error as e:
        return f"Fejl: {e}"
    finally:
        cursor.close()
        conn.close()

    return redirect('/')

# ------------------ PATIENT MENU ------------------

@app.route('/menu')
def menu():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("""
        SELECT deadline
        FROM paakraevet_konsultation
        WHERE patient_id = %s AND besvaret = FALSE
        ORDER BY deadline ASC
    """, (session['user_id'],))
    krav = cursor.fetchall()
    if krav and "deadline" in krav:
        krav["deadline"] = krav["deadline"].strftime("%d-%m-%Y kl. %H:%M")


    cursor.close()
    conn.close()

    return render_template('patient-menu.html', krav=krav)

# ------------------ PATIENT FEEDBACK & OVERSIGT ------------------

@app.route('/feedback')
def feedback():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT kommentar7, oprettet_tidspunkt
        FROM akne_konsultation
        WHERE patient_id = %s AND kommentar7 IS NOT NULL AND kommentar7 != ''
        ORDER BY oprettet_tidspunkt DESC
    """, (session['user_id'],))

    feedbacks = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('feedback.html', feedbacks=feedbacks)



@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM akne_konsultation
        WHERE patient_id = %s
        ORDER BY oprettet_tidspunkt DESC
    """, (session['user_id'],))

    konsultationer = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('patient-dashboard.html', konsultationer=konsultationer)

# ------------------ SPØRGESKEMA ------------------

@app.route('/sporgeskema', methods=['GET', 'POST'])
def sporgeskema():
    if 'user_id' not in session:
        return "Ikke logget ind"

    if request.method == 'GET':
        return render_template('sporgeskema.html')

    data = request.form
    fil = request.files['billede']
    filnavn = None

    if fil and fil.filename:
        filnavn = secure_filename(fil.filename)
        fil.save(os.path.join(app.config['UPLOAD_FOLDER'], filnavn))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO akne_konsultation (
            patient_id, status, kommentar1, bivirkninger, kommentar2, medicin, kommentar3, 
            gener, kommentar4, symptomer, kommentar5,
            pande, kinder, hage, bryst, ryg, kommentar6,
            feedback, kommentar7, billede_navn
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        session['user_id'],
        data.get('status'), data.get('kommentar1'),
        data.get('bivirkninger'), data.get('kommentar2'),
        data.get('medicin'), data.get('kommentar3'),
        int(data.get('gener', 0)), data.get('kommentar4'),
        data.get('symptomer'), data.get('kommentar5'),
        'pande' in request.form.getlist('områder'),
        'kinder' in request.form.getlist('områder'),
        'hage' in request.form.getlist('områder'),
        'bryst' in request.form.getlist('områder'),
        'ryg' in request.form.getlist('områder'),
        data.get('kommentar6'),
        data.get('feedback'), data.get('kommentar7'),
        filnavn
    ))

    # Marker påkrævet konsultation som besvaret
    cursor.execute("""
        UPDATE paakraevet_konsultation
        SET besvaret = TRUE
        WHERE patient_id = %s AND besvaret = FALSE
        ORDER BY deadline ASC
        LIMIT 1
    """, (session['user_id'],))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/menu')

# ------------------ LÆGE API ------------------

@app.route("/api/send-tidspunkt", methods=["POST"])
def send_tidspunkt():
    data = request.get_json()
    dato = data.get("dato")
    tid = data.get("tid")
    deadline = f"{dato} {tid}"

    patient_id = data.get("patient_id")

    if not isinstance(patient_id, int):
        return "Ugyldigt patient_id", 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO paakraevet_konsultation (patient_id, deadline)
        VALUES (%s, %s)
    """, (patient_id, deadline))
    conn.commit()
    cursor.close()
    conn.close()
    return "OK", 200

@app.route("/api/patienter")
def hent_patienter():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, cpr_nummer FROM patient_users ORDER BY id ASC")
    patienter = cursor.fetchall()
    cursor.close()
    conn.close()
    return patienter  # Flask returnerer automatisk JSON

@app.route("/api/konsultationer/<int:patient_id>")
def hent_konsultationer_for_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            akne_konsultation.id AS konsultation_id,
            akne_konsultation.oprettet_tidspunkt,
            akne_konsultation.symptomer,
            akne_konsultation.status,
            akne_konsultation.medicin,
            akne_konsultation.bivirkninger,
            akne_konsultation.gener,
            akne_konsultation.billede_navn,
            paakraevet_konsultation.besvaret,
            patient_users.id AS patient_id,
            patient_users.cpr_nummer
        FROM akne_konsultation
        LEFT JOIN paakraevet_konsultation 
            ON akne_konsultation.patient_id = paakraevet_konsultation.patient_id
        JOIN patient_users
            ON akne_konsultation.patient_id = patient_users.id
        WHERE akne_konsultation.patient_id = %s
        ORDER BY akne_konsultation.oprettet_tidspunkt DESC
    """, (patient_id,))

    svar = cursor.fetchall()
    cursor.close()
    conn.close()

    for s in svar:
        if s["billede_navn"]:
            s["billede_url"] = f"/uploads/{s['billede_navn']}"

    return svar

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/api/send-feedback", methods=["POST"])
def send_feedback():
    data = request.get_json()
    besked = data.get("besked")
    patient_id = data.get("patient_id")

    if not besked or not patient_id:
        return "Ugyldige data", 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE akne_konsultation
            SET kommentar7 = %s
            WHERE patient_id = %s
            ORDER BY oprettet_tidspunkt DESC
            LIMIT 1
        """, (besked, patient_id))
        conn.commit()
    except mysql.connector.Error as e:
        return f"Databasefejl: {e}", 500
    finally:
        cursor.close()
        conn.close()

    return "Feedback modtaget", 200


# ------------------ SERVER ------------------

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=60070)
