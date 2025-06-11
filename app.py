from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
import os
import mariadb
from database import get_db_connection

app = Flask(__name__)
app.secret_key = "hemmelig_nøgle"
app.config["UPLOAD_FOLDER"] = "static/uploads"

# ----------------- LOGIN ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        cpr = request.form["cpr-nummer"]
        adgangskode = request.form["adgangskode"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, cpr_nummer FROM patient_users WHERE cpr_nummer = ? AND password = ?", (cpr, adgangskode))
        bruger = cursor.fetchone()
        conn.close()

        if bruger:
            session["bruger_id"] = bruger[0]
            session["cpr"] = bruger[1]
            return redirect("/dashboard")
        else:
            return "Forkert CPR eller adgangskode."
    return render_template("login.html")

# ----------------- DASHBOARD ------------------
@app.route("/dashboard")
def dashboard():
    if "bruger_id" not in session:
        return redirect("/login")
    return render_template("patient.html", navn="Patient", cpr=session["cpr"])

# ----------------- E-KONSULTATION ------------------
@app.route("/konsultation", methods=["GET", "POST"])
def konsultation():
    if "bruger_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        form = request.form
        filer = request.files
        conn = get_db_connection()
        cursor = conn.cursor()

        # Gem billede
        billede = filer["billede"]
        billede_navn = ""
        if billede and billede.filename != "":
            billede_navn = secure_filename(billede.filename)
            billede.save(os.path.join(app.config["UPLOAD_FOLDER"], billede_navn))

        # Områder (checkboxe)
        områder = form.getlist("områder")
        områder_bool = {
            "pande": "pande" in områder,
            "kinder": "kinder" in områder,
            "hage": "hage" in områder,
            "bryst": "bryst" in områder,
            "ryg": "ryg" in områder
        }

        cursor.execute("""
            INSERT INTO akne_konsultation (
                patient_id, status, kommentar1,
                bivirkninger, kommentar2,
                medicin, kommentar3,
                gener, kommentar4,
                symptomer, kommentar5,
                pande, kinder, hage, bryst, ryg, kommentar6,
                feedback, kommentar7,
                billede_navn
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["bruger_id"], form.get("status"), form.get("kommentar1"),
            form.get("bivirkninger"), form.get("kommentar2"),
            form.get("medicin"), form.get("kommentar3"),
            int(form.get("gener")), form.get("kommentar4"),
            form.get("symptomer"), form.get("kommentar5"),
            områder_bool["pande"], områder_bool["kinder"],
            områder_bool["hage"], områder_bool["bryst"], områder_bool["ryg"],
            form.get("kommentar6"), form.get("feedback"), form.get("kommentar7"),
            billede_navn
        ))

        conn.commit()
        conn.close()
        return "Tak for din besvarelse!"

    return render_template("uploade.html")

# ----------------- LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ----------------- START SERVER ------------------
if __name__ == "__main__":
    app.run(debug=True)
