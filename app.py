import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from init_db import init_db


app = Flask(__name__)
app.secret_key = "superstarkespasswort"

def get_db(db):
    conn = sqlite3.connect(f"{db}.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/", methods=["GET"])
def landing():
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    conn = get_db("user")

    if request.method == "POST":
        name = request.form["user"].rstrip().lstrip()
        password = request.form["password1"]
        repeated_password = request.form["password2"]
        user = conn.execute("SELECT * FROM user WHERE name = ?", (name,)).fetchone()
        
        if user is None:
            if not password:
                return render_template("login.html", fehler="Bitte Passwort eingeben!", name=name)
    
            if password != repeated_password:
                return render_template("register.html", fehler="Passwörter stimmen nicht überein!", name=name)
            
            conn.execute("""
                INSERT INTO user (name, password)
                VALUES (?, ?)          
            """, (name, generate_password_hash(password)))

            conn.commit()
            conn.close()
            session["name"] = name
            return redirect(url_for("index"))
        else:
            return render_template("register.html", name=name, fehler="Name bereits vergeben")
    
    return render_template("register.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    conn = get_db("user")
    if request.method == "POST":
        name = request.form["user"].rstrip().lstrip()
        password = request.form["password"]

        if not password:
            return render_template("login.html", fehler="Bitte Passwort eingeben!", name=name)

        user = conn.execute("SELECT * FROM user WHERE name = ?", (name,)).fetchone()
        
        if check_password_hash(user["password"], password):
            conn.close()
            session["name"] = name
            return redirect(url_for("index"))
        else:
            conn.close()
            return render_template("login.html", fehler="Falsches Passwort!", name=name)

    conn.close()
    return render_template("login.html")

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("landing"))

@app.route("/index")
def index():
    if "name" not in session:
        return redirect(url_for("login"))
    
    conn = get_db("schulden")
    eintraege = conn.execute("SELECT * FROM schulden WHERE bezahlt = 0").fetchall()
    conn.close()
    return render_template("index.html", eintraege=eintraege)

@app.route("/add", methods=["POST", "GET"])
def add():
    if check_admin():
        conn = get_db("schulden")
        eintraege = conn.execute("""
            SELECT *
            FROM schulden
        """).fetchall()
        conn.close()
    else:
        conn = get_db("schulden")
        eintraege = conn.execute("""
            SELECT *
            FROM schulden
            WHERE schuldner = ?
        """, (session["name"],)).fetchall()
        conn.close()

    if request.method == "POST":
        schuldner = request.form["schuldner"]
        glaeubiger = request.form["glaeubiger"]
        betrag = float(request.form["betrag"])
        datum = request.form["datum"]
        dringlichkeit = int(request.form["dringlichkeit"])
        bezahlt = 0

        if not (schuldner or glaeubiger or betrag or datum or dringlichkeit):
            return render_template("formular.html", eintraege=eintraege, fehler="Bitte alle Felder ausfüllen!")
        
        if betrag < 0:
            return render_template("fornular.html", eintraege=eintraege, fehler="Betrag kann nicht negativ sein!")
        
        if (dringlichkeit < 1) or (dringlichkeit > 5):
            return render_template("formular.html", eintraege=eintraege, fehler="Dringlichkeit muss zwischen 1 und 5 liegen!")
        
        if (schuldner or glaeubiger) != session["name"]:
            return render_template("formular.html", eintraege=eintraege, fehler="Schuldner oder Gläubiger muss deinen Namen enthalten!")

        conn = get_db("schulden")
        conn.execute("""
            INSERT INTO schulden (schuldner, glaeubiger, betrag, datum, dringlichkeit, bezahlt)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (schuldner, glaeubiger, betrag, datum, dringlichkeit, bezahlt))

        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    return render_template("formular.html", eintraege=eintraege)

@app.route("/bezahlen/<int:id>", methods=["GET"])
def bezahlen(id):
    conn = get_db("schulden")
    conn.execute("UPDATE schulden SET bezahlt = 1 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("add"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = get_db("schulden")
        
    eintraege = conn.execute("""
        SELECT schuldner, glaeubiger, betrag, datum, dringlichkeit, id
        FROM schulden 
        WHERE id = ?
    """, (id,)).fetchone()
    conn.close()

    if request.method == "POST":
        glaeubiger = request.form["glaeubiger"]
        betrag = float(request.form["betrag"])
        datum = request.form["datum"]
        dringlichkeit = int(request.form["dringlichkeit"])

        if (eintraege["schuldner"] != session["name"]) and not check_admin():
            return render_template("formular.html", eintraege=eintraege, fehler="Schuldner entspricht nicht dem Nutzer!")

        if not glaeubiger or betrag or datum or dringlichkeit:
            return render_template("formular.html", eintraege=eintraege, fehler="Bitte alle Felder ausfüllen!")
        
        if betrag < 0:
            return render_template("fornular.html", eintraege=eintraege, fehler="Betrag kann nicht negativ sein!")
        
        if (dringlichkeit < 1) or (dringlichkeit > 5):
            return render_template("formular.html", eintraege=eintraege, fehler="Dringlichkeit muss zwischen 1 und 5 liegen!")

        conn.execute("""
            UPDATE schulden 
            SET glaeubiger = ?, betrag = ?, datum = ?, dringlichkeit = ?
            WHERE id = ?
        """, (glaeubiger, betrag, datum, dringlichkeit, id,)).fetchone()
        conn.commit()
        conn.close()
        return redirect(url_for("add"))
    
    return render_template("edit.html", eintraege=eintraege)

def check_admin():
    conn = get_db("user")

    admin_status = conn.execute("""
        SELECT is_admin
        FROM user
        WHERE name = ?
    """, (session["name"],)).fetchone()
    conn.close()

    return admin_status["is_admin"]

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    conn = get_db("schulden")
    current_lb = request.args.get("type", "schuldner")

    if current_lb == "schuldner":
        eintraege = conn.execute("""
            SELECT schuldner, SUM(betrag) as gesamtbetrag
            FROM schulden
            GROUP BY schuldner
            ORDER BY gesamtbetrag DESC
        """).fetchall()
        grouped_by = "Schuldner"
    else:
        eintraege = conn.execute("""
            SELECT glaeubiger, SUM(betrag) as gesamtbetrag
            FROM schulden
            GROUP BY glaeubiger
            ORDER BY gesamtbetrag DESC
        """).fetchall()
        grouped_by = "Gläubiger"

    conn.close()
    return render_template("leaderboard.html", eintraege=eintraege, grouped_by=grouped_by, current_lb=current_lb)

init_db()

if __name__ == "__main__":
    app.run(debug=True)