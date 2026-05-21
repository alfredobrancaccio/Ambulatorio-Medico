import os
from flask import Flask, render_template, request, redirect, url_for, g, flash
from app_db import AmbulatorioDatabase, INTEGRITY_ERRORS

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-ambulatorio")


def get_db():
    if "db" not in g:
        g.db = AmbulatorioDatabase().connect()
    return g.db


@app.teardown_appcontext
def chiudi_db(exc):
    db = g.pop("db", None)
    if db:
        db._conn.close()


def _valida_appuntamento(db, medico_id, paziente_id, esame_id):
    medico = db.query_one("SELECT * FROM medici WHERE id = ?", (medico_id,))
    if not medico:
        return f"Medico con ID {medico_id} non trovato."
    if not db.query_one("SELECT id FROM pazienti WHERE id = ?", (paziente_id,)):
        return f"Paziente con ID {paziente_id} non trovato."
    esame = db.query_one("SELECT * FROM esami WHERE id = ?", (esame_id,))
    if not esame:
        return f"Esame con ID {esame_id} non trovato."
    if esame["reparto"] != medico["reparto"]:
        return (
            f"L'esame '{esame['nome']}' ({esame['reparto']}) non appartiene "
            f"al reparto del medico '{medico['nome']} {medico['cognome']}' ({medico['reparto']})."
        )
    return None


# ── HOME ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("pazienti_list"))


# ── PAZIENTI ──────────────────────────────────────────────────────────────────

@app.route("/pazienti")
def pazienti_list():
    return render_template("pazienti_list.html",
                           pazienti=get_db().query(
                               "SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome"))


@app.route("/pazienti/nuovo", methods=["GET", "POST"])
def pazienti_nuovo():
    if request.method == "POST":
        nome    = request.form["nome"].strip()
        cognome = request.form["cognome"].strip()
        if not nome or not cognome:
            flash("[ERRORE] Nome e cognome sono obbligatori.")
        else:
            nid = get_db().execute(
                "INSERT INTO pazienti (nome, cognome) VALUES (?, ?) RETURNING id",
                (nome, cognome),
            )
            flash(f"[OK] Paziente aggiunto con ID {nid}.")
            return redirect(url_for("pazienti_list"))
    return render_template("pazienti_form.html", paziente=None)


@app.route("/pazienti/<int:id>/modifica", methods=["GET", "POST"])
def pazienti_modifica(id):
    db      = get_db()
    paziente = db.query_one("SELECT * FROM pazienti WHERE id = ?", (id,))
    if paziente is None:
        flash("[ERRORE] Paziente non trovato.")
        return redirect(url_for("pazienti_list"))
    if request.method == "POST":
        nome    = request.form["nome"].strip()
        cognome = request.form["cognome"].strip()
        if not nome or not cognome:
            flash("[ERRORE] Nome e cognome sono obbligatori.")
        else:
            db.execute("UPDATE pazienti SET nome = ?, cognome = ? WHERE id = ?",
                       (nome, cognome, id))
            flash("[OK] Paziente aggiornato.")
            return redirect(url_for("pazienti_list"))
    return render_template("pazienti_form.html", paziente=paziente)


@app.route("/pazienti/<int:id>/elimina", methods=["POST"])
def pazienti_elimina(id):
    try:
        get_db().execute("DELETE FROM pazienti WHERE id = ?", (id,))
        flash("[OK] Paziente eliminato.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare il paziente.")
    return redirect(url_for("pazienti_list"))


@app.route("/pazienti/<int:id>/dashboard")
def dashboard_paziente(id):
    db       = get_db()
    paziente = db.query_one("SELECT * FROM pazienti WHERE id = ?", (id,))
    if paziente is None:
        flash("[ERRORE] Paziente non trovato.")
        return redirect(url_for("pazienti_list"))
    appuntamenti = db.query("""
        SELECT a.id, a.data,
               m.nome || ' ' || m.cognome AS medico,
               e.nome AS esame
        FROM appuntamenti a
        JOIN medici m ON m.id = a.medico_id
        JOIN esami  e ON e.id = a.esame_id
        WHERE a.paziente_id = ?
        ORDER BY a.data DESC
    """, (id,))
    referti = db.query("""
        SELECT r.id, r.data_rilascio, e.nome AS esame
        FROM referti r
        JOIN appuntamenti a ON a.id = r.appuntamento_id
        JOIN esami        e ON e.id = a.esame_id
        WHERE a.paziente_id = ?
        ORDER BY r.data_rilascio DESC
    """, (id,))
    prescrizioni = db.query("""
        SELECT pr.id, pr.farmaco, pr.dose, pr.data_emissione,
               m.nome || ' ' || m.cognome AS medico
        FROM prescrizioni pr
        JOIN medici m ON m.id = pr.medico_id
        WHERE pr.paziente_id = ?
        ORDER BY pr.data_emissione DESC
    """, (id,))
    return render_template("dashboard_paziente.html",
                           paziente=paziente,
                           appuntamenti=appuntamenti,
                           referti=referti,
                           prescrizioni=prescrizioni)


# ── MEDICI ────────────────────────────────────────────────────────────────────

@app.route("/medici")
def medici_list():
    return render_template("medici_list.html",
                           medici=get_db().query(
                               "SELECT id, nome, cognome, reparto FROM medici ORDER BY cognome, nome"))


@app.route("/medici/nuovo", methods=["GET", "POST"])
def medici_nuovo():
    if request.method == "POST":
        nome    = request.form["nome"].strip()
        cognome = request.form["cognome"].strip()
        reparto = request.form["reparto"].strip()
        if not nome or not cognome or not reparto:
            flash("[ERRORE] Tutti i campi sono obbligatori.")
        else:
            nid = get_db().execute(
                "INSERT INTO medici (nome, cognome, reparto) VALUES (?, ?, ?) RETURNING id",
                (nome, cognome, reparto),
            )
            flash(f"[OK] Medico aggiunto con ID {nid}.")
            return redirect(url_for("medici_list"))
    return render_template("medici_form.html", medico=None)


@app.route("/medici/<int:id>/modifica", methods=["GET", "POST"])
def medici_modifica(id):
    db     = get_db()
    medico = db.query_one("SELECT * FROM medici WHERE id = ?", (id,))
    if medico is None:
        flash("[ERRORE] Medico non trovato.")
        return redirect(url_for("medici_list"))
    if request.method == "POST":
        nome    = request.form["nome"].strip()
        cognome = request.form["cognome"].strip()
        reparto = request.form["reparto"].strip()
        if not nome or not cognome or not reparto:
            flash("[ERRORE] Tutti i campi sono obbligatori.")
        else:
            db.execute(
                "UPDATE medici SET nome = ?, cognome = ?, reparto = ? WHERE id = ?",
                (nome, cognome, reparto, id),
            )
            flash("[OK] Medico aggiornato.")
            return redirect(url_for("medici_list"))
    return render_template("medici_form.html", medico=medico)


@app.route("/medici/<int:id>/elimina", methods=["POST"])
def medici_elimina(id):
    try:
        get_db().execute("DELETE FROM medici WHERE id = ?", (id,))
        flash("[OK] Medico eliminato.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare il medico.")
    return redirect(url_for("medici_list"))


@app.route("/medici/<int:id>/dashboard")
def dashboard_medico(id):
    db     = get_db()
    medico = db.query_one("SELECT * FROM medici WHERE id = ?", (id,))
    if medico is None:
        flash("[ERRORE] Medico non trovato.")
        return redirect(url_for("medici_list"))
    appuntamenti = db.query("""
        SELECT a.id, a.data,
               p.nome || ' ' || p.cognome AS paziente,
               e.nome AS esame
        FROM appuntamenti a
        JOIN pazienti p ON p.id = a.paziente_id
        JOIN esami    e ON e.id = a.esame_id
        WHERE a.medico_id = ?
        ORDER BY a.data DESC
    """, (id,))
    prescrizioni = db.query("""
        SELECT pr.id, pr.farmaco, pr.dose, pr.data_emissione,
               p.nome || ' ' || p.cognome AS paziente
        FROM prescrizioni pr
        JOIN pazienti p ON p.id = pr.paziente_id
        WHERE pr.medico_id = ?
        ORDER BY pr.data_emissione DESC
    """, (id,))
    return render_template("dashboard_medico.html",
                           medico=medico,
                           appuntamenti=appuntamenti,
                           prescrizioni=prescrizioni)


# ── ESAMI ─────────────────────────────────────────────────────────────────────

@app.route("/esami")
def esami_list():
    return render_template("esami_list.html",
                           esami=get_db().query(
                               "SELECT id, nome, reparto FROM esami ORDER BY reparto, nome"))


@app.route("/esami/nuovo", methods=["GET", "POST"])
def esami_nuovo():
    if request.method == "POST":
        nome    = request.form["nome"].strip()
        reparto = request.form["reparto"].strip()
        if not nome or not reparto:
            flash("[ERRORE] Tutti i campi sono obbligatori.")
        else:
            nid = get_db().execute(
                "INSERT INTO esami (nome, reparto) VALUES (?, ?) RETURNING id",
                (nome, reparto),
            )
            flash(f"[OK] Esame aggiunto con ID {nid}.")
            return redirect(url_for("esami_list"))
    return render_template("esami_form.html", esame=None)


@app.route("/esami/<int:id>/modifica", methods=["GET", "POST"])
def esami_modifica(id):
    db    = get_db()
    esame = db.query_one("SELECT * FROM esami WHERE id = ?", (id,))
    if esame is None:
        flash("[ERRORE] Esame non trovato.")
        return redirect(url_for("esami_list"))
    if request.method == "POST":
        nome    = request.form["nome"].strip()
        reparto = request.form["reparto"].strip()
        if not nome or not reparto:
            flash("[ERRORE] Tutti i campi sono obbligatori.")
        else:
            db.execute("UPDATE esami SET nome = ?, reparto = ? WHERE id = ?",
                       (nome, reparto, id))
            flash("[OK] Esame aggiornato.")
            return redirect(url_for("esami_list"))
    return render_template("esami_form.html", esame=esame)


@app.route("/esami/<int:id>/elimina", methods=["POST"])
def esami_elimina(id):
    try:
        get_db().execute("DELETE FROM esami WHERE id = ?", (id,))
        flash("[OK] Esame eliminato.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare: esistono appuntamenti collegati.")
    return redirect(url_for("esami_list"))


# ── APPUNTAMENTI ──────────────────────────────────────────────────────────────

_SQL_APPUNTAMENTI = """
    SELECT a.id, a.paziente_id, a.medico_id, a.esame_id, a.data,
           p.nome || ' ' || p.cognome AS paziente,
           m.nome || ' ' || m.cognome AS medico,
           e.nome AS esame
    FROM appuntamenti a
    JOIN pazienti p ON p.id = a.paziente_id
    JOIN medici   m ON m.id = a.medico_id
    JOIN esami    e ON e.id = a.esame_id
"""


@app.route("/appuntamenti")
def appuntamenti_list():
    return render_template("appuntamenti_list.html",
                           appuntamenti=get_db().query(
                               _SQL_APPUNTAMENTI + " ORDER BY a.data DESC, a.id"))


@app.route("/appuntamenti/nuovo", methods=["GET", "POST"])
def appuntamenti_nuovo():
    db = get_db()
    if request.method == "POST":
        try:
            medico_id   = int(request.form["medico_id"])
            paziente_id = int(request.form["paziente_id"])
            esame_id    = int(request.form["esame_id"])
            data        = request.form["data"].strip()
        except (ValueError, KeyError):
            flash("[ERRORE] Dati del modulo non validi.")
        else:
            errore = _valida_appuntamento(db, medico_id, paziente_id, esame_id)
            if errore:
                flash(f"[ERRORE] {errore}")
            else:
                nid = db.execute(
                    "INSERT INTO appuntamenti (paziente_id, medico_id, esame_id, data)"
                    " VALUES (?, ?, ?, ?) RETURNING id",
                    (paziente_id, medico_id, esame_id, data),
                )
                flash(f"[OK] Appuntamento aggiunto con ID {nid}.")
                return redirect(url_for("appuntamenti_list"))
    return render_template("appuntamenti_form.html", appuntamento=None,
                           pazienti=db.query("SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome"),
                           medici=db.query("SELECT id, nome, cognome, reparto FROM medici ORDER BY cognome, nome"),
                           esami=db.query("SELECT id, nome, reparto FROM esami ORDER BY reparto, nome"))


@app.route("/appuntamenti/<int:id>/modifica", methods=["GET", "POST"])
def appuntamenti_modifica(id):
    db           = get_db()
    appuntamento = db.query_one(_SQL_APPUNTAMENTI + " WHERE a.id = ?", (id,))
    if appuntamento is None:
        flash("[ERRORE] Appuntamento non trovato.")
        return redirect(url_for("appuntamenti_list"))
    if request.method == "POST":
        try:
            medico_id   = int(request.form["medico_id"])
            paziente_id = int(request.form["paziente_id"])
            esame_id    = int(request.form["esame_id"])
            data        = request.form["data"].strip()
        except (ValueError, KeyError):
            flash("[ERRORE] Dati del modulo non validi.")
        else:
            errore = _valida_appuntamento(db, medico_id, paziente_id, esame_id)
            if errore:
                flash(f"[ERRORE] {errore}")
            else:
                db.execute(
                    "UPDATE appuntamenti"
                    " SET paziente_id = ?, medico_id = ?, esame_id = ?, data = ?"
                    " WHERE id = ?",
                    (paziente_id, medico_id, esame_id, data, id),
                )
                flash("[OK] Appuntamento aggiornato.")
                return redirect(url_for("appuntamenti_list"))
    return render_template("appuntamenti_form.html", appuntamento=appuntamento,
                           pazienti=db.query("SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome"),
                           medici=db.query("SELECT id, nome, cognome, reparto FROM medici ORDER BY cognome, nome"),
                           esami=db.query("SELECT id, nome, reparto FROM esami ORDER BY reparto, nome"))


@app.route("/appuntamenti/<int:id>/elimina", methods=["POST"])
def appuntamenti_elimina(id):
    try:
        get_db().execute("DELETE FROM appuntamenti WHERE id = ?", (id,))
        flash("[OK] Appuntamento eliminato.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare l'appuntamento.")
    return redirect(url_for("appuntamenti_list"))


# ── REFERTI ───────────────────────────────────────────────────────────────────

_SQL_REFERTI = """
    SELECT r.id, r.data_rilascio, r.appuntamento_id,
           p.nome || ' ' || p.cognome AS paziente,
           e.nome AS esame
    FROM referti r
    JOIN appuntamenti a ON a.id = r.appuntamento_id
    JOIN pazienti     p ON p.id = a.paziente_id
    JOIN esami        e ON e.id = a.esame_id
"""

_SQL_APP_PER_REFERTI = """
    SELECT a.id, a.data,
           p.nome || ' ' || p.cognome AS paziente,
           e.nome AS esame
    FROM appuntamenti a
    JOIN pazienti p ON p.id = a.paziente_id
    JOIN esami    e ON e.id = a.esame_id
    ORDER BY a.data DESC, a.id
"""


@app.route("/referti")
def referti_list():
    return render_template("referti_list.html",
                           referti=get_db().query(
                               _SQL_REFERTI + " ORDER BY r.data_rilascio DESC, r.id"))


@app.route("/referti/nuovo", methods=["GET", "POST"])
def referti_nuovo():
    db = get_db()
    if request.method == "POST":
        try:
            appuntamento_id = int(request.form["appuntamento_id"])
            data_rilascio   = request.form["data_rilascio"].strip()
        except (ValueError, KeyError):
            flash("[ERRORE] Dati del modulo non validi.")
        else:
            if not db.query_one("SELECT id FROM appuntamenti WHERE id = ?", (appuntamento_id,)):
                flash(f"[ERRORE] Appuntamento con ID {appuntamento_id} non trovato.")
            else:
                nid = db.execute(
                    "INSERT INTO referti (data_rilascio, appuntamento_id) VALUES (?, ?) RETURNING id",
                    (data_rilascio, appuntamento_id),
                )
                flash(f"[OK] Referto aggiunto con ID {nid}.")
                return redirect(url_for("referti_list"))
    return render_template("referti_form.html", referto=None,
                           appuntamenti=db.query(_SQL_APP_PER_REFERTI))


@app.route("/referti/<int:id>/modifica", methods=["GET", "POST"])
def referti_modifica(id):
    db      = get_db()
    referto = db.query_one(_SQL_REFERTI + " WHERE r.id = ?", (id,))
    if referto is None:
        flash("[ERRORE] Referto non trovato.")
        return redirect(url_for("referti_list"))
    if request.method == "POST":
        try:
            appuntamento_id = int(request.form["appuntamento_id"])
            data_rilascio   = request.form["data_rilascio"].strip()
        except (ValueError, KeyError):
            flash("[ERRORE] Dati del modulo non validi.")
        else:
            db.execute(
                "UPDATE referti SET data_rilascio = ?, appuntamento_id = ? WHERE id = ?",
                (data_rilascio, appuntamento_id, id),
            )
            flash("[OK] Referto aggiornato.")
            return redirect(url_for("referti_list"))
    return render_template("referti_form.html", referto=referto,
                           appuntamenti=db.query(_SQL_APP_PER_REFERTI))


@app.route("/referti/<int:id>/elimina", methods=["POST"])
def referti_elimina(id):
    try:
        get_db().execute("DELETE FROM referti WHERE id = ?", (id,))
        flash("[OK] Referto eliminato.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare il referto.")
    return redirect(url_for("referti_list"))


# ── PRESCRIZIONI ──────────────────────────────────────────────────────────────

_SQL_PRESCRIZIONI = """
    SELECT pr.id, pr.medico_id, pr.paziente_id,
           pr.farmaco, pr.dose, pr.data_emissione,
           m.nome || ' ' || m.cognome AS medico,
           p.nome || ' ' || p.cognome AS paziente
    FROM prescrizioni pr
    JOIN medici   m ON m.id = pr.medico_id
    JOIN pazienti p ON p.id = pr.paziente_id
"""


@app.route("/prescrizioni")
def prescrizioni_list():
    return render_template("prescrizioni_list.html",
                           prescrizioni=get_db().query(
                               _SQL_PRESCRIZIONI + " ORDER BY pr.data_emissione DESC, pr.id"))


@app.route("/prescrizioni/nuovo", methods=["GET", "POST"])
def prescrizioni_nuovo():
    db = get_db()
    if request.method == "POST":
        try:
            medico_id   = int(request.form["medico_id"])
            paziente_id = int(request.form["paziente_id"])
            farmaco     = request.form["farmaco"].strip()
            dose        = request.form["dose"].strip()
            data        = request.form["data_emissione"].strip()
        except (ValueError, KeyError):
            flash("[ERRORE] Dati del modulo non validi.")
        else:
            if not farmaco or not dose or not data:
                flash("[ERRORE] Tutti i campi sono obbligatori.")
            else:
                nid = db.execute(
                    "INSERT INTO prescrizioni"
                    " (medico_id, paziente_id, farmaco, dose, data_emissione)"
                    " VALUES (?, ?, ?, ?, ?) RETURNING id",
                    (medico_id, paziente_id, farmaco, dose, data),
                )
                flash(f"[OK] Prescrizione aggiunta con ID {nid}.")
                return redirect(url_for("prescrizioni_list"))
    return render_template("prescrizioni_form.html", prescrizione=None,
                           medici=db.query("SELECT id, nome, cognome, reparto FROM medici ORDER BY cognome, nome"),
                           pazienti=db.query("SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome"))


@app.route("/prescrizioni/<int:id>/modifica", methods=["GET", "POST"])
def prescrizioni_modifica(id):
    db           = get_db()
    prescrizione = db.query_one(_SQL_PRESCRIZIONI + " WHERE pr.id = ?", (id,))
    if prescrizione is None:
        flash("[ERRORE] Prescrizione non trovata.")
        return redirect(url_for("prescrizioni_list"))
    if request.method == "POST":
        try:
            medico_id   = int(request.form["medico_id"])
            paziente_id = int(request.form["paziente_id"])
            farmaco     = request.form["farmaco"].strip()
            dose        = request.form["dose"].strip()
            data        = request.form["data_emissione"].strip()
        except (ValueError, KeyError):
            flash("[ERRORE] Dati del modulo non validi.")
        else:
            if not farmaco or not dose or not data:
                flash("[ERRORE] Tutti i campi sono obbligatori.")
            else:
                db.execute(
                    "UPDATE prescrizioni"
                    " SET medico_id = ?, paziente_id = ?,"
                    "     farmaco = ?, dose = ?, data_emissione = ?"
                    " WHERE id = ?",
                    (medico_id, paziente_id, farmaco, dose, data, id),
                )
                flash("[OK] Prescrizione aggiornata.")
                return redirect(url_for("prescrizioni_list"))
    return render_template("prescrizioni_form.html", prescrizione=prescrizione,
                           medici=db.query("SELECT id, nome, cognome, reparto FROM medici ORDER BY cognome, nome"),
                           pazienti=db.query("SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome"))


@app.route("/prescrizioni/<int:id>/elimina", methods=["POST"])
def prescrizioni_elimina(id):
    try:
        get_db().execute("DELETE FROM prescrizioni WHERE id = ?", (id,))
        flash("[OK] Prescrizione eliminata.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare la prescrizione.")
    return redirect(url_for("prescrizioni_list"))
