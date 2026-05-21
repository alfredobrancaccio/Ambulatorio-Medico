import os
from flask import Flask, render_template, request, redirect, url_for, g, flash
from app_db import AmbulatorioDatabase, INTEGRITY_ERRORS

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-ambulatorio")

# ── DB per richiesta ──────────────────────────────────────────────────────────

def get_db():
    if "db" not in g:
        g.db = AmbulatorioDatabase().connect()
    return g.db

@app.teardown_appcontext
def chiudi_db(exc):
    db = g.pop("db", None)
    if db:
        db._conn.close()

# ── SQL riutilizzabili ────────────────────────────────────────────────────────

_SQL_MEDICO_FULL = """
    SELECT m.id, m.nome, m.cognome, m.reparto_id, r.nome AS reparto
    FROM medici m JOIN reparti r ON r.id = m.reparto_id
"""

_SQL_VISITA_FULL = """
    SELECT v.id, v.paziente_id, v.medico_id, v.esame_id, v.data, v.note,
           p.nome || ' ' || p.cognome AS paziente,
           m.nome || ' ' || m.cognome AS medico,
           e.nome AS esame,
           r.nome AS reparto
    FROM visite v
    JOIN pazienti p ON p.id = v.paziente_id
    JOIN medici   m ON m.id = v.medico_id
    JOIN esami    e ON e.id = v.esame_id
    JOIN reparti  r ON r.id = e.reparto_id
"""

_SQL_REFERTI_FULL = """
    SELECT rf.id, rf.visita_id, rf.data_rilascio, rf.contenuto,
           p.nome || ' ' || p.cognome AS paziente,
           e.nome AS esame
    FROM referti rf
    JOIN visite   v ON v.id = rf.visita_id
    JOIN pazienti p ON p.id = v.paziente_id
    JOIN esami    e ON e.id = v.esame_id
"""

_SQL_PRESCRIZIONI_FULL = """
    SELECT pr.id, pr.medico_id, pr.paziente_id,
           pr.farmaco, pr.dose, pr.data_emissione,
           m.nome || ' ' || m.cognome AS medico,
           p.nome || ' ' || p.cognome AS paziente
    FROM prescrizioni pr
    JOIN medici   m ON m.id = pr.medico_id
    JOIN pazienti p ON p.id = pr.paziente_id
"""

def _valida_visita(db, medico_id, paziente_id, esame_id):
    medico = db.query_one(_SQL_MEDICO_FULL + " WHERE m.id = ?", (medico_id,))
    if not medico:
        return f"Medico con ID {medico_id} non trovato."
    if not db.query_one("SELECT id FROM pazienti WHERE id = ?", (paziente_id,)):
        return f"Paziente con ID {paziente_id} non trovato."
    esame = db.query_one(
        "SELECT id, nome, reparto_id FROM esami WHERE id = ?", (esame_id,)
    )
    if not esame:
        return f"Esame con ID {esame_id} non trovato."
    if esame["reparto_id"] != medico["reparto_id"]:
        return (
            f"L'esame '{esame['nome']}' non appartiene al reparto"
            f" del medico '{medico['nome']} {medico['cognome']}' ({medico['reparto']})."
        )
    return None

# ── HOME ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

# ══════════════════════════════════════════════════════════════════════════════
# SEGRETERIA
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/segreteria")
def seg_dashboard():
    db = get_db()
    def n(sql):
        return db.query_one(sql)["COUNT(*)"]
    stats = {
        "pazienti":    n("SELECT COUNT(*) FROM pazienti"),
        "reparti":     n("SELECT COUNT(*) FROM reparti"),
        "medici":      n("SELECT COUNT(*) FROM medici"),
        "esami":       n("SELECT COUNT(*) FROM esami"),
        "visite":      n("SELECT COUNT(*) FROM visite"),
        "referti":     n("SELECT COUNT(*) FROM referti"),
        "prescrizioni":n("SELECT COUNT(*) FROM prescrizioni"),
    }
    return render_template("seg_dashboard.html", stats=stats)

# ── pazienti ──────────────────────────────────────────────────────────────────

@app.route("/segreteria/pazienti")
def seg_pazienti_list():
    righe = get_db().query(
        "SELECT id, nome, cognome, data_nascita, codice_fiscale"
        " FROM pazienti ORDER BY cognome, nome"
    )
    return render_template("seg_pazienti_list.html", pazienti=righe)

@app.route("/segreteria/pazienti/nuovo", methods=["GET", "POST"])
def seg_pazienti_nuovo():
    if request.method == "POST":
        nome           = request.form["nome"].strip()
        cognome        = request.form["cognome"].strip()
        data_nascita   = request.form.get("data_nascita", "").strip() or None
        codice_fiscale = request.form.get("codice_fiscale", "").strip() or None
        if not nome or not cognome:
            flash("[ERRORE] Nome e cognome sono obbligatori.")
        else:
            try:
                nid = get_db().execute(
                    "INSERT INTO pazienti (nome, cognome, data_nascita, codice_fiscale)"
                    " VALUES (?, ?, ?, ?) RETURNING id",
                    (nome, cognome, data_nascita, codice_fiscale),
                )
                flash(f"[OK] Paziente aggiunto con ID {nid}.")
                return redirect(url_for("seg_pazienti_list"))
            except INTEGRITY_ERRORS:
                flash("[ERRORE] Codice fiscale già presente.")
    return render_template("seg_pazienti_form.html", paziente=None)

@app.route("/segreteria/pazienti/<int:id>/modifica", methods=["GET", "POST"])
def seg_pazienti_modifica(id):
    db      = get_db()
    paziente = db.query_one("SELECT * FROM pazienti WHERE id = ?", (id,))
    if paziente is None:
        flash("[ERRORE] Paziente non trovato.")
        return redirect(url_for("seg_pazienti_list"))
    if request.method == "POST":
        nome           = request.form["nome"].strip()
        cognome        = request.form["cognome"].strip()
        data_nascita   = request.form.get("data_nascita", "").strip() or None
        codice_fiscale = request.form.get("codice_fiscale", "").strip() or None
        if not nome or not cognome:
            flash("[ERRORE] Nome e cognome sono obbligatori.")
        else:
            try:
                db.execute(
                    "UPDATE pazienti SET nome=?, cognome=?, data_nascita=?, codice_fiscale=?"
                    " WHERE id=?",
                    (nome, cognome, data_nascita, codice_fiscale, id),
                )
                flash("[OK] Paziente aggiornato.")
                return redirect(url_for("seg_pazienti_list"))
            except INTEGRITY_ERRORS:
                flash("[ERRORE] Codice fiscale già presente.")
    return render_template("seg_pazienti_form.html", paziente=paziente)

@app.route("/segreteria/pazienti/<int:id>/elimina", methods=["POST"])
def seg_pazienti_elimina(id):
    try:
        get_db().execute("DELETE FROM pazienti WHERE id = ?", (id,))
        flash("[OK] Paziente eliminato.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare il paziente.")
    return redirect(url_for("seg_pazienti_list"))

# ── reparti ───────────────────────────────────────────────────────────────────

@app.route("/segreteria/reparti")
def seg_reparti_list():
    return render_template("seg_reparti_list.html",
                           reparti=get_db().query("SELECT id, nome FROM reparti ORDER BY nome"))

@app.route("/segreteria/reparti/nuovo", methods=["GET", "POST"])
def seg_reparti_nuovo():
    if request.method == "POST":
        nome = request.form["nome"].strip()
        if not nome:
            flash("[ERRORE] Il nome è obbligatorio.")
        else:
            try:
                nid = get_db().execute(
                    "INSERT INTO reparti (nome) VALUES (?) RETURNING id", (nome,)
                )
                flash(f"[OK] Reparto aggiunto con ID {nid}.")
                return redirect(url_for("seg_reparti_list"))
            except INTEGRITY_ERRORS:
                flash("[ERRORE] Reparto già esistente.")
    return render_template("seg_reparti_form.html", reparto=None)

@app.route("/segreteria/reparti/<int:id>/modifica", methods=["GET", "POST"])
def seg_reparti_modifica(id):
    db      = get_db()
    reparto = db.query_one("SELECT * FROM reparti WHERE id = ?", (id,))
    if reparto is None:
        flash("[ERRORE] Reparto non trovato.")
        return redirect(url_for("seg_reparti_list"))
    if request.method == "POST":
        nome = request.form["nome"].strip()
        if not nome:
            flash("[ERRORE] Il nome è obbligatorio.")
        else:
            try:
                db.execute("UPDATE reparti SET nome = ? WHERE id = ?", (nome, id))
                flash("[OK] Reparto aggiornato.")
                return redirect(url_for("seg_reparti_list"))
            except INTEGRITY_ERRORS:
                flash("[ERRORE] Reparto già esistente.")
    return render_template("seg_reparti_form.html", reparto=reparto)

@app.route("/segreteria/reparti/<int:id>/elimina", methods=["POST"])
def seg_reparti_elimina(id):
    try:
        get_db().execute("DELETE FROM reparti WHERE id = ?", (id,))
        flash("[OK] Reparto eliminato.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare: esistono medici o esami collegati.")
    return redirect(url_for("seg_reparti_list"))

# ── medici ────────────────────────────────────────────────────────────────────

@app.route("/segreteria/medici")
def seg_medici_list():
    return render_template("seg_medici_list.html",
                           medici=get_db().query(
                               _SQL_MEDICO_FULL + " ORDER BY m.cognome, m.nome"))

@app.route("/segreteria/medici/nuovo", methods=["GET", "POST"])
def seg_medici_nuovo():
    db = get_db()
    if request.method == "POST":
        nome       = request.form["nome"].strip()
        cognome    = request.form["cognome"].strip()
        reparto_id = request.form.get("reparto_id", "").strip()
        if not nome or not cognome or not reparto_id:
            flash("[ERRORE] Tutti i campi sono obbligatori.")
        else:
            nid = db.execute(
                "INSERT INTO medici (nome, cognome, reparto_id) VALUES (?, ?, ?) RETURNING id",
                (nome, cognome, int(reparto_id)),
            )
            flash(f"[OK] Medico aggiunto con ID {nid}.")
            return redirect(url_for("seg_medici_list"))
    return render_template("seg_medici_form.html", medico=None,
                           reparti=db.query("SELECT id, nome FROM reparti ORDER BY nome"))

@app.route("/segreteria/medici/<int:id>/modifica", methods=["GET", "POST"])
def seg_medici_modifica(id):
    db     = get_db()
    medico = db.query_one(_SQL_MEDICO_FULL + " WHERE m.id = ?", (id,))
    if medico is None:
        flash("[ERRORE] Medico non trovato.")
        return redirect(url_for("seg_medici_list"))
    if request.method == "POST":
        nome       = request.form["nome"].strip()
        cognome    = request.form["cognome"].strip()
        reparto_id = request.form.get("reparto_id", "").strip()
        if not nome or not cognome or not reparto_id:
            flash("[ERRORE] Tutti i campi sono obbligatori.")
        else:
            db.execute(
                "UPDATE medici SET nome=?, cognome=?, reparto_id=? WHERE id=?",
                (nome, cognome, int(reparto_id), id),
            )
            flash("[OK] Medico aggiornato.")
            return redirect(url_for("seg_medici_list"))
    return render_template("seg_medici_form.html", medico=medico,
                           reparti=db.query("SELECT id, nome FROM reparti ORDER BY nome"))

@app.route("/segreteria/medici/<int:id>/elimina", methods=["POST"])
def seg_medici_elimina(id):
    try:
        get_db().execute("DELETE FROM medici WHERE id = ?", (id,))
        flash("[OK] Medico eliminato.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare: esistono visite o prescrizioni collegate.")
    return redirect(url_for("seg_medici_list"))

# ── esami ─────────────────────────────────────────────────────────────────────

@app.route("/segreteria/esami")
def seg_esami_list():
    return render_template("seg_esami_list.html",
                           esami=get_db().query("""
                               SELECT e.id, e.nome, r.nome AS reparto, e.reparto_id
                               FROM esami e JOIN reparti r ON r.id = e.reparto_id
                               ORDER BY r.nome, e.nome
                           """))

@app.route("/segreteria/esami/nuovo", methods=["GET", "POST"])
def seg_esami_nuovo():
    db = get_db()
    if request.method == "POST":
        nome       = request.form["nome"].strip()
        reparto_id = request.form.get("reparto_id", "").strip()
        if not nome or not reparto_id:
            flash("[ERRORE] Tutti i campi sono obbligatori.")
        else:
            nid = db.execute(
                "INSERT INTO esami (nome, reparto_id) VALUES (?, ?) RETURNING id",
                (nome, int(reparto_id)),
            )
            flash(f"[OK] Esame aggiunto con ID {nid}.")
            return redirect(url_for("seg_esami_list"))
    return render_template("seg_esami_form.html", esame=None,
                           reparti=db.query("SELECT id, nome FROM reparti ORDER BY nome"))

@app.route("/segreteria/esami/<int:id>/modifica", methods=["GET", "POST"])
def seg_esami_modifica(id):
    db    = get_db()
    esame = db.query_one(
        "SELECT e.id, e.nome, e.reparto_id, r.nome AS reparto"
        " FROM esami e JOIN reparti r ON r.id = e.reparto_id WHERE e.id = ?", (id,)
    )
    if esame is None:
        flash("[ERRORE] Esame non trovato.")
        return redirect(url_for("seg_esami_list"))
    if request.method == "POST":
        nome       = request.form["nome"].strip()
        reparto_id = request.form.get("reparto_id", "").strip()
        if not nome or not reparto_id:
            flash("[ERRORE] Tutti i campi sono obbligatori.")
        else:
            db.execute("UPDATE esami SET nome=?, reparto_id=? WHERE id=?",
                       (nome, int(reparto_id), id))
            flash("[OK] Esame aggiornato.")
            return redirect(url_for("seg_esami_list"))
    return render_template("seg_esami_form.html", esame=esame,
                           reparti=db.query("SELECT id, nome FROM reparti ORDER BY nome"))

@app.route("/segreteria/esami/<int:id>/elimina", methods=["POST"])
def seg_esami_elimina(id):
    try:
        get_db().execute("DELETE FROM esami WHERE id = ?", (id,))
        flash("[OK] Esame eliminato.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare: esistono visite collegate.")
    return redirect(url_for("seg_esami_list"))

# ── visite ────────────────────────────────────────────────────────────────────

@app.route("/segreteria/visite")
def seg_visite_list():
    return render_template("seg_visite_list.html",
                           visite=get_db().query(
                               _SQL_VISITA_FULL + " ORDER BY v.data DESC, v.id"))

@app.route("/segreteria/visite/nuovo", methods=["GET", "POST"])
def seg_visite_nuovo():
    db = get_db()
    if request.method == "POST":
        try:
            paziente_id = int(request.form["paziente_id"])
            medico_id   = int(request.form["medico_id"])
            esame_id    = int(request.form["esame_id"])
            data        = request.form["data"].strip()
            note        = request.form.get("note", "").strip() or None
        except (ValueError, KeyError):
            flash("[ERRORE] Dati non validi.")
        else:
            errore = _valida_visita(db, medico_id, paziente_id, esame_id)
            if errore:
                flash(f"[ERRORE] {errore}")
            else:
                nid = db.execute(
                    "INSERT INTO visite (paziente_id, medico_id, esame_id, data, note)"
                    " VALUES (?, ?, ?, ?, ?) RETURNING id",
                    (paziente_id, medico_id, esame_id, data, note),
                )
                flash(f"[OK] Visita aggiunta con ID {nid}.")
                return redirect(url_for("seg_visite_list"))
    return render_template("seg_visite_form.html", visita=None,
                           pazienti=db.query("SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome"),
                           medici=db.query(_SQL_MEDICO_FULL + " ORDER BY m.cognome, m.nome"),
                           esami=db.query("SELECT e.id, e.nome, e.reparto_id FROM esami e ORDER BY e.nome"))

@app.route("/segreteria/visite/<int:id>/modifica", methods=["GET", "POST"])
def seg_visite_modifica(id):
    db     = get_db()
    visita = db.query_one(_SQL_VISITA_FULL + " WHERE v.id = ?", (id,))
    if visita is None:
        flash("[ERRORE] Visita non trovata.")
        return redirect(url_for("seg_visite_list"))
    if request.method == "POST":
        try:
            paziente_id = int(request.form["paziente_id"])
            medico_id   = int(request.form["medico_id"])
            esame_id    = int(request.form["esame_id"])
            data        = request.form["data"].strip()
            note        = request.form.get("note", "").strip() or None
        except (ValueError, KeyError):
            flash("[ERRORE] Dati non validi.")
        else:
            errore = _valida_visita(db, medico_id, paziente_id, esame_id)
            if errore:
                flash(f"[ERRORE] {errore}")
            else:
                db.execute(
                    "UPDATE visite SET paziente_id=?, medico_id=?, esame_id=?, data=?, note=?"
                    " WHERE id=?",
                    (paziente_id, medico_id, esame_id, data, note, id),
                )
                flash("[OK] Visita aggiornata.")
                return redirect(url_for("seg_visite_list"))
    return render_template("seg_visite_form.html", visita=visita,
                           pazienti=db.query("SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome"),
                           medici=db.query(_SQL_MEDICO_FULL + " ORDER BY m.cognome, m.nome"),
                           esami=db.query("SELECT e.id, e.nome, e.reparto_id FROM esami e ORDER BY e.nome"))

@app.route("/segreteria/visite/<int:id>/elimina", methods=["POST"])
def seg_visite_elimina(id):
    try:
        get_db().execute("DELETE FROM visite WHERE id = ?", (id,))
        flash("[OK] Visita eliminata.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare la visita.")
    return redirect(url_for("seg_visite_list"))

# ── referti ───────────────────────────────────────────────────────────────────

@app.route("/segreteria/referti")
def seg_referti_list():
    return render_template("seg_referti_list.html",
                           referti=get_db().query(
                               _SQL_REFERTI_FULL + " ORDER BY rf.data_rilascio DESC, rf.id"))

@app.route("/segreteria/referti/nuovo", methods=["GET", "POST"])
def seg_referti_nuovo():
    db = get_db()
    if request.method == "POST":
        try:
            visita_id     = int(request.form["visita_id"])
            data_rilascio = request.form["data_rilascio"].strip()
            contenuto     = request.form.get("contenuto", "").strip() or None
        except (ValueError, KeyError):
            flash("[ERRORE] Dati non validi.")
        else:
            if not db.query_one("SELECT id FROM visite WHERE id = ?", (visita_id,)):
                flash(f"[ERRORE] Visita con ID {visita_id} non trovata.")
            else:
                nid = db.execute(
                    "INSERT INTO referti (visita_id, data_rilascio, contenuto)"
                    " VALUES (?, ?, ?) RETURNING id",
                    (visita_id, data_rilascio, contenuto),
                )
                flash(f"[OK] Referto aggiunto con ID {nid}.")
                return redirect(url_for("seg_referti_list"))
    visite = db.query(
        _SQL_VISITA_FULL + " ORDER BY v.data DESC, v.id"
    )
    return render_template("seg_referti_form.html", referto=None, visite=visite)

@app.route("/segreteria/referti/<int:id>/modifica", methods=["GET", "POST"])
def seg_referti_modifica(id):
    db      = get_db()
    referto = db.query_one(_SQL_REFERTI_FULL + " WHERE rf.id = ?", (id,))
    if referto is None:
        flash("[ERRORE] Referto non trovato.")
        return redirect(url_for("seg_referti_list"))
    if request.method == "POST":
        try:
            visita_id     = int(request.form["visita_id"])
            data_rilascio = request.form["data_rilascio"].strip()
            contenuto     = request.form.get("contenuto", "").strip() or None
        except (ValueError, KeyError):
            flash("[ERRORE] Dati non validi.")
        else:
            db.execute(
                "UPDATE referti SET visita_id=?, data_rilascio=?, contenuto=? WHERE id=?",
                (visita_id, data_rilascio, contenuto, id),
            )
            flash("[OK] Referto aggiornato.")
            return redirect(url_for("seg_referti_list"))
    visite = db.query(_SQL_VISITA_FULL + " ORDER BY v.data DESC, v.id")
    return render_template("seg_referti_form.html", referto=referto, visite=visite)

@app.route("/segreteria/referti/<int:id>/elimina", methods=["POST"])
def seg_referti_elimina(id):
    try:
        get_db().execute("DELETE FROM referti WHERE id = ?", (id,))
        flash("[OK] Referto eliminato.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare il referto.")
    return redirect(url_for("seg_referti_list"))

# ── prescrizioni ──────────────────────────────────────────────────────────────

@app.route("/segreteria/prescrizioni")
def seg_prescrizioni_list():
    return render_template("seg_prescrizioni_list.html",
                           prescrizioni=get_db().query(
                               _SQL_PRESCRIZIONI_FULL +
                               " ORDER BY pr.data_emissione DESC, pr.id"))

@app.route("/segreteria/prescrizioni/nuovo", methods=["GET", "POST"])
def seg_prescrizioni_nuovo():
    db = get_db()
    if request.method == "POST":
        try:
            medico_id   = int(request.form["medico_id"])
            paziente_id = int(request.form["paziente_id"])
            farmaco     = request.form["farmaco"].strip()
            dose        = request.form["dose"].strip()
            data        = request.form["data_emissione"].strip()
        except (ValueError, KeyError):
            flash("[ERRORE] Dati non validi.")
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
                return redirect(url_for("seg_prescrizioni_list"))
    return render_template("seg_prescrizioni_form.html", prescrizione=None,
                           medici=db.query(_SQL_MEDICO_FULL + " ORDER BY m.cognome, m.nome"),
                           pazienti=db.query("SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome"))

@app.route("/segreteria/prescrizioni/<int:id>/modifica", methods=["GET", "POST"])
def seg_prescrizioni_modifica(id):
    db           = get_db()
    prescrizione = db.query_one(_SQL_PRESCRIZIONI_FULL + " WHERE pr.id = ?", (id,))
    if prescrizione is None:
        flash("[ERRORE] Prescrizione non trovata.")
        return redirect(url_for("seg_prescrizioni_list"))
    if request.method == "POST":
        try:
            medico_id   = int(request.form["medico_id"])
            paziente_id = int(request.form["paziente_id"])
            farmaco     = request.form["farmaco"].strip()
            dose        = request.form["dose"].strip()
            data        = request.form["data_emissione"].strip()
        except (ValueError, KeyError):
            flash("[ERRORE] Dati non validi.")
        else:
            if not farmaco or not dose or not data:
                flash("[ERRORE] Tutti i campi sono obbligatori.")
            else:
                db.execute(
                    "UPDATE prescrizioni"
                    " SET medico_id=?, paziente_id=?, farmaco=?, dose=?, data_emissione=?"
                    " WHERE id=?",
                    (medico_id, paziente_id, farmaco, dose, data, id),
                )
                flash("[OK] Prescrizione aggiornata.")
                return redirect(url_for("seg_prescrizioni_list"))
    return render_template("seg_prescrizioni_form.html", prescrizione=prescrizione,
                           medici=db.query(_SQL_MEDICO_FULL + " ORDER BY m.cognome, m.nome"),
                           pazienti=db.query("SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome"))

@app.route("/segreteria/prescrizioni/<int:id>/elimina", methods=["POST"])
def seg_prescrizioni_elimina(id):
    try:
        get_db().execute("DELETE FROM prescrizioni WHERE id = ?", (id,))
        flash("[OK] Prescrizione eliminata.")
    except INTEGRITY_ERRORS:
        flash("[ERRORE] Impossibile eliminare la prescrizione.")
    return redirect(url_for("seg_prescrizioni_list"))

# ══════════════════════════════════════════════════════════════════════════════
# MEDICO
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/medico")
def med_select():
    medici = get_db().query(_SQL_MEDICO_FULL + " ORDER BY m.cognome, m.nome")
    return render_template("med_select.html", medici=medici)

@app.route("/medico/<int:id>")
def med_dashboard(id):
    db     = get_db()
    medico = db.query_one(_SQL_MEDICO_FULL + " WHERE m.id = ?", (id,))
    if medico is None:
        flash("[ERRORE] Medico non trovato.")
        return redirect(url_for("med_select"))
    visite = db.query(
        _SQL_VISITA_FULL + " WHERE v.medico_id = ? ORDER BY v.data DESC", (id,)
    )
    prescrizioni = db.query(
        _SQL_PRESCRIZIONI_FULL + " WHERE pr.medico_id = ? ORDER BY pr.data_emissione DESC",
        (id,),
    )
    pazienti_ids = {v["paziente_id"] for v in visite} | \
                   {pr["paziente_id"] for pr in prescrizioni}
    n_referti = db.query_one(
        "SELECT COUNT(*) FROM referti rf"
        " JOIN visite v ON v.id = rf.visita_id WHERE v.medico_id = ?", (id,)
    )["COUNT(*)"]
    return render_template("med_dashboard.html",
                           medico=medico,
                           visite=visite,
                           prescrizioni=prescrizioni,
                           n_referti=n_referti)

@app.route("/medico/<int:mid>/nuovo-referto", methods=["GET", "POST"])
def med_nuovo_referto(mid):
    db     = get_db()
    medico = db.query_one(_SQL_MEDICO_FULL + " WHERE m.id = ?", (mid,))
    if medico is None:
        flash("[ERRORE] Medico non trovato.")
        return redirect(url_for("med_select"))
    if request.method == "POST":
        try:
            visita_id     = int(request.form["visita_id"])
            data_rilascio = request.form["data_rilascio"].strip()
            contenuto     = request.form.get("contenuto", "").strip() or None
        except (ValueError, KeyError):
            flash("[ERRORE] Dati non validi.")
        else:
            visita = db.query_one(
                "SELECT id, medico_id FROM visite WHERE id = ?", (visita_id,)
            )
            if not visita or visita["medico_id"] != mid:
                flash("[ERRORE] Visita non valida.")
            else:
                nid = db.execute(
                    "INSERT INTO referti (visita_id, data_rilascio, contenuto)"
                    " VALUES (?, ?, ?) RETURNING id",
                    (visita_id, data_rilascio, contenuto),
                )
                flash(f"[OK] Referto aggiunto con ID {nid}.")
                return redirect(url_for("med_dashboard", id=mid))
    visite = db.query(
        _SQL_VISITA_FULL + " WHERE v.medico_id = ? ORDER BY v.data DESC", (mid,)
    )
    return render_template("med_referto_form.html", medico=medico, visite=visite)

@app.route("/medico/<int:mid>/nuova-prescrizione", methods=["GET", "POST"])
def med_nuova_prescrizione(mid):
    db     = get_db()
    medico = db.query_one(_SQL_MEDICO_FULL + " WHERE m.id = ?", (mid,))
    if medico is None:
        flash("[ERRORE] Medico non trovato.")
        return redirect(url_for("med_select"))
    if request.method == "POST":
        try:
            paziente_id = int(request.form["paziente_id"])
            farmaco     = request.form["farmaco"].strip()
            dose        = request.form["dose"].strip()
            data        = request.form["data_emissione"].strip()
        except (ValueError, KeyError):
            flash("[ERRORE] Dati non validi.")
        else:
            if not farmaco or not dose or not data:
                flash("[ERRORE] Tutti i campi sono obbligatori.")
            else:
                nid = db.execute(
                    "INSERT INTO prescrizioni"
                    " (medico_id, paziente_id, farmaco, dose, data_emissione)"
                    " VALUES (?, ?, ?, ?, ?) RETURNING id",
                    (mid, paziente_id, farmaco, dose, data),
                )
                flash(f"[OK] Prescrizione aggiunta con ID {nid}.")
                return redirect(url_for("med_dashboard", id=mid))
    pazienti = db.query("SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome")
    return render_template("med_prescrizione_form.html", medico=medico, pazienti=pazienti)

# ══════════════════════════════════════════════════════════════════════════════
# PAZIENTE
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/paziente")
def paz_select():
    pazienti = get_db().query(
        "SELECT id, nome, cognome, data_nascita FROM pazienti ORDER BY cognome, nome"
    )
    return render_template("paz_select.html", pazienti=pazienti)

@app.route("/paziente/<int:id>")
def paz_dashboard(id):
    db      = get_db()
    paziente = db.query_one("SELECT * FROM pazienti WHERE id = ?", (id,))
    if paziente is None:
        flash("[ERRORE] Paziente non trovato.")
        return redirect(url_for("paz_select"))
    visite = db.query(
        _SQL_VISITA_FULL + " WHERE v.paziente_id = ? ORDER BY v.data DESC", (id,)
    )
    referti = db.query("""
        SELECT rf.id, rf.data_rilascio, rf.contenuto,
               e.nome AS esame,
               m.nome || ' ' || m.cognome AS medico
        FROM referti rf
        JOIN visite   v ON v.id = rf.visita_id
        JOIN esami    e ON e.id = v.esame_id
        JOIN medici   m ON m.id = v.medico_id
        WHERE v.paziente_id = ?
        ORDER BY rf.data_rilascio DESC
    """, (id,))
    prescrizioni = db.query("""
        SELECT pr.id, pr.farmaco, pr.dose, pr.data_emissione,
               m.nome || ' ' || m.cognome AS medico
        FROM prescrizioni pr
        JOIN medici m ON m.id = pr.medico_id
        WHERE pr.paziente_id = ?
        ORDER BY pr.data_emissione DESC
    """, (id,))
    return render_template("paz_dashboard.html",
                           paziente=paziente,
                           visite=visite,
                           referti=referti,
                           prescrizioni=prescrizioni)
