from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
import os
from werkzeug.utils import secure_filename
from database import get_db_connection
import subprocess  

app = Flask(__name__)
app.secret_key = 'hemmelig_nøgle'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#  Startside: Forside med login-valg
@app.route('/')
def home():
    return render_template('index_(forsider).html')

#  Login-sider
@app.route('/laege-login')
def laege_login():
    return render_template('FE_laege-login.html')

@app.route('/patient-login')
def patient_login():
    return render_template('patient-login.html')

#  Login-logik
@app.route('/login', methods=['POST'])
def login():
    cpr = request.form['cpr-nummer']
    password = request.form['adgangskode']

    # 👉 Læge-login (starter Tkinter-dashboard)
    if cpr == "04" and password == "dtu":
        subprocess.Popen(["python", "laege_dashboard_tkinter.py"])
        return redirect('/laege-dashboard')

    # 👉 Patient-login (fra database)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM patient_users WHERE cpr_nummer = %s AND password = %s", (cpr, password))
    bruger = cursor.fetchone()

    if bruger:
        session['user_id'] = bruger[0]
        return redirect('/menu')
    else:
        return "Login mislykkedes"

#  Læge-dashboard vises efter Tkinter start
@app.route('/laege-dashboard')
def laege_dashboard_gui():
    return "Tkinter-dashboard for læge åbnet!"

#  Patient-oprettelse
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

#  Patient-menu
@app.route('/menu')
def menu():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('patient-menu.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

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

#  Spørgeskema
@app.route('/sporgeskema', methods=['GET', 'POST'])
def sporgeskema():
    if request.method == 'GET':
        return render_template('sporgeskema.html')
    
    if 'user_id' not in session:
        return "Ikke logget ind"

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

    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/menu')

#  API-ruter til Tkinter-dashboard
@app.route('/api/konsultationer')
def api_konsultationer():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, symptomer, oprettet_tidspunkt FROM akne_konsultation ORDER BY oprettet_tidspunkt DESC")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

@app.route('/api/send-feedback', methods=['POST'])
def api_send_feedback():
    data = request.get_json()
    print("Feedback modtaget:", data.get("besked"))
    return "OK", 200

@app.route('/api/send-tidspunkt', methods=['POST'])
def api_send_tidspunkt():
    data = request.get_json()
    print("Tidspunkt foreslået:", data)
    return "OK", 200

#  App-start
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=60070)
