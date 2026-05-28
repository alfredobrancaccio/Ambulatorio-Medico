import app_db

_SQL_MEDICO_FULL = """
    SELECT m.id, m.nome, m.cognome, m.reparto_id, r.nome AS reparto
    FROM medici m JOIN reparti r ON r.id = m.reparto_id
"""

_SQL_VISITA_FULL = """
    SELECT v.id, v.data, v.note,
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


# ── SEGRETERIA ────────────────────────────────────────────────────────────────

class SegretariaREPL:
    def __init__(self):
        pass

    def cmd_pazienti(self, args):
        righe = app_db.query(
            "SELECT id, nome, cognome, data_nascita, codice_fiscale"
            " FROM pazienti ORDER BY cognome, nome"
        )
        print("ID", "Nome", "Cognome", "Nascita", "CF")
        for p in righe:
            print(p["id"], p["nome"], p["cognome"],
                  p["data_nascita"] or "-", p["codice_fiscale"] or "-")

    def cmd_reparti(self, args):
        righe = app_db.query("SELECT id, nome FROM reparti ORDER BY nome")
        print("ID", "Reparto")
        for r in righe:
            print(r["id"], r["nome"])

    def cmd_medici(self, args):
        righe = app_db.query(_SQL_MEDICO_FULL + " ORDER BY m.cognome, m.nome")
        print("ID", "Nome", "Cognome", "Reparto")
        for m in righe:
            print(m["id"], m["nome"], m["cognome"], m["reparto"])

    def cmd_esami(self, args):
        righe = app_db.query("""
            SELECT e.id, e.nome, r.nome AS reparto
            FROM esami e JOIN reparti r ON r.id = e.reparto_id
            ORDER BY r.nome, e.nome
        """)
        print("ID", "Esame", "Reparto")
        for e in righe:
            print(e["id"], e["nome"], e["reparto"])

    def cmd_visite(self, args):
        righe = app_db.query(_SQL_VISITA_FULL + " ORDER BY v.data DESC, v.id")
        if not righe:
            print("Nessuna visita.")
            return
        print("ID", "Paziente", "Medico", "Esame", "Data")
        for v in righe:
            print(v["id"], v["paziente"], v["medico"], v["esame"], v["data"])

    def cmd_referti(self, args):
        righe = app_db.query("""
            SELECT rf.id, rf.data_rilascio, rf.contenuto,
                   p.nome || ' ' || p.cognome AS paziente,
                   e.nome AS esame
            FROM referti rf
            JOIN visite   v ON v.id  = rf.visita_id
            JOIN pazienti p ON p.id  = v.paziente_id
            JOIN esami    e ON e.id  = v.esame_id
            ORDER BY rf.data_rilascio DESC, rf.id
        """)
        if not righe:
            print("Nessun referto.")
            return
        print("ID", "Data", "Paziente", "Esame", "Contenuto")
        for r in righe:
            print(r["id"], r["data_rilascio"], r["paziente"],
                  r["esame"], (r["contenuto"] or "-")[:40])

    def cmd_prescrizioni(self, args):
        righe = app_db.query("""
            SELECT pr.id, pr.farmaco, pr.dose, pr.data_emissione,
                   m.nome || ' ' || m.cognome AS medico,
                   p.nome || ' ' || p.cognome AS paziente
            FROM prescrizioni pr
            JOIN medici   m ON m.id = pr.medico_id
            JOIN pazienti p ON p.id = pr.paziente_id
            ORDER BY pr.data_emissione DESC, pr.id
        """)
        if not righe:
            print("Nessuna prescrizione.")
            return
        print("ID", "Medico", "Paziente", "Farmaco", "Dose", "Data")
        for pr in righe:
            print(pr["id"], pr["medico"], pr["paziente"],
                  pr["farmaco"], pr["dose"], pr["data_emissione"])

    def cmd_statistiche(self, args):
        def n(sql):
            return app_db.query_one(sql)["COUNT(*)"]
        print("Pazienti:     ", n("SELECT COUNT(*) FROM pazienti"))
        print("Reparti:      ", n("SELECT COUNT(*) FROM reparti"))
        print("Medici:       ", n("SELECT COUNT(*) FROM medici"))
        print("Esami:        ", n("SELECT COUNT(*) FROM esami"))
        print("Visite:       ", n("SELECT COUNT(*) FROM visite"))
        print("Referti:      ", n("SELECT COUNT(*) FROM referti"))
        print("Prescrizioni: ", n("SELECT COUNT(*) FROM prescrizioni"))

    def cmd_nuovo_paziente(self, args):
        if len(args) < 2:
            print("[ERRORE] Uso: nuovo-paziente <Nome> <Cognome> [<data_nascita> <codice_fiscale>]")
            return
        nome, cognome = args[0], args[1]
        data_nascita   = args[2] if len(args) > 2 else None
        codice_fiscale = args[3] if len(args) > 3 else None
        nid = app_db.execute(
            "INSERT INTO pazienti (nome, cognome, data_nascita, codice_fiscale)"
            " VALUES (?, ?, ?, ?)",
            (nome, cognome, data_nascita, codice_fiscale),
        )
        print(f"[OK] Paziente aggiunto con ID {nid}.")

    def cmd_nuovo_reparto(self, args):
        if len(args) != 1:
            print("[ERRORE] Uso: nuovo-reparto <Nome>")
            return
        nid = app_db.execute(
            "INSERT INTO reparti (nome) VALUES (?)", (args[0],)
        )
        print(f"[OK] Reparto aggiunto con ID {nid}.")

    def cmd_nuovo_medico(self, args):
        if len(args) != 3:
            print("[ERRORE] Uso: nuovo-medico <Nome> <Cognome> <reparto_id>")
            return
        nome, cognome = args[0], args[1]
        try:
            reparto_id = int(args[2])
        except ValueError:
            print("[ERRORE] reparto_id deve essere un numero intero.")
            return
        if not app_db.query_one("SELECT id FROM reparti WHERE id = ?", (reparto_id,)):
            print(f"[ERRORE] Reparto con ID {reparto_id} non trovato.")
            return
        nid = app_db.execute(
            "INSERT INTO medici (nome, cognome, reparto_id) VALUES (?, ?, ?)",
            (nome, cognome, reparto_id),
        )
        print(f"[OK] Medico aggiunto con ID {nid}.")

    def cmd_nuovo_esame(self, args):
        if len(args) != 2:
            print("[ERRORE] Uso: nuovo-esame <Nome> <reparto_id>")
            return
        nome = args[0]
        try:
            reparto_id = int(args[1])
        except ValueError:
            print("[ERRORE] reparto_id deve essere un numero intero.")
            return
        if not app_db.query_one("SELECT id FROM reparti WHERE id = ?", (reparto_id,)):
            print(f"[ERRORE] Reparto con ID {reparto_id} non trovato.")
            return
        nid = app_db.execute(
            "INSERT INTO esami (nome, reparto_id) VALUES (?, ?)",
            (nome, reparto_id),
        )
        print(f"[OK] Esame aggiunto con ID {nid}.")

    def cmd_nuova_visita(self, args):
        if len(args) != 4:
            print("[ERRORE] Uso: nuova-visita <paziente_id> <medico_id> <esame_id> <data>")
            return
        try:
            paziente_id = int(args[0])
            medico_id   = int(args[1])
            esame_id    = int(args[2])
        except ValueError:
            print("[ERRORE] Gli ID devono essere numeri interi.")
            return
        data = args[3]
        if not app_db.query_one("SELECT id FROM pazienti WHERE id = ?", (paziente_id,)):
            print(f"[ERRORE] Paziente con ID {paziente_id} non trovato.")
            return
        medico = app_db.query_one("SELECT reparto_id FROM medici WHERE id = ?", (medico_id,))
        if not medico:
            print(f"[ERRORE] Medico con ID {medico_id} non trovato.")
            return
        esame = app_db.query_one("SELECT nome, reparto_id FROM esami WHERE id = ?", (esame_id,))
        if not esame:
            print(f"[ERRORE] Esame con ID {esame_id} non trovato.")
            return
        if esame["reparto_id"] != medico["reparto_id"]:
            print("[ERRORE] L'esame non appartiene al reparto del medico.")
            return
        nid = app_db.execute(
            "INSERT INTO visite (paziente_id, medico_id, esame_id, data)"
            " VALUES (?, ?, ?, ?)",
            (paziente_id, medico_id, esame_id, data),
        )
        print(f"[OK] Visita aggiunta con ID {nid}.")

    def cmd_help(self, args):
        righe = [
            ("pazienti",                                          "Elenca i pazienti"),
            ("reparti",                                           "Elenca i reparti"),
            ("medici",                                            "Elenca i medici"),
            ("esami",                                             "Elenca gli esami"),
            ("visite",                                            "Elenca le visite"),
            ("referti",                                           "Elenca i referti"),
            ("prescrizioni",                                      "Elenca le prescrizioni"),
            ("statistiche",                                       "Contatori generali"),
            ("nuovo-paziente <Nome> <Cognome> [<data> <CF>]",    "Aggiunge un paziente"),
            ("nuovo-reparto <Nome>",                              "Aggiunge un reparto"),
            ("nuovo-medico <Nome> <Cognome> <reparto_id>",       "Aggiunge un medico"),
            ("nuovo-esame <Nome> <reparto_id>",                   "Aggiunge un esame"),
            ("nuova-visita <paz_id> <med_id> <esame_id> <data>", "Prenota una visita"),
            ("help",                                              "Mostra questo messaggio"),
            ("esci",                                              "Esce dal programma"),
        ]
        for cmd, desc in righe:
            print(f"  {cmd}: {desc}")

    def esegui(self):
        print("[Segreteria] Digita 'help' per i comandi.")
        comandi = {
            "pazienti":       self.cmd_pazienti,
            "reparti":        self.cmd_reparti,
            "medici":         self.cmd_medici,
            "esami":          self.cmd_esami,
            "visite":         self.cmd_visite,
            "referti":        self.cmd_referti,
            "prescrizioni":   self.cmd_prescrizioni,
            "statistiche":    self.cmd_statistiche,
            "nuovo-paziente": self.cmd_nuovo_paziente,
            "nuovo-reparto":  self.cmd_nuovo_reparto,
            "nuovo-medico":   self.cmd_nuovo_medico,
            "nuovo-esame":    self.cmd_nuovo_esame,
            "nuova-visita":   self.cmd_nuova_visita,
            "help":           self.cmd_help,
        }
        while True:
            try:
                line = input("segreteria> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nArrivederci.")
                return
            if not line:
                continue
            parti = line.split()
            cmd, args = parti[0], parti[1:]
            if cmd == "esci":
                print("Arrivederci.")
                return
            handler = comandi.get(cmd)
            if handler:
                handler(args)
            else:
                print(f"[ERRORE] Comando '{cmd}' non riconosciuto. Digita 'help'.")


# ── MEDICO ────────────────────────────────────────────────────────────────────

class MedicoREPL:
    def __init__(self, medico):
        self.medico = medico

    def cmd_visite(self, args):
        righe = app_db.query(
            _SQL_VISITA_FULL + " WHERE v.medico_id = ? ORDER BY v.data DESC",
            (self.medico["id"],),
        )
        if not righe:
            print("Nessuna visita.")
            return
        print("ID", "Paziente", "Esame", "Data", "Note")
        for v in righe:
            print(v["id"], v["paziente"], v["esame"], v["data"], v["note"] or "-")

    def cmd_nuovo_referto(self, args):
        if len(args) < 2:
            print("[ERRORE] Uso: nuovo-referto <visita_id> <data_rilascio> [<contenuto>]")
            return
        try:
            visita_id = int(args[0])
        except ValueError:
            print("[ERRORE] visita_id deve essere un numero intero.")
            return
        data_rilascio = args[1]
        contenuto     = " ".join(args[2:]) if len(args) > 2 else None
        visita = app_db.query_one(
            "SELECT id, medico_id FROM visite WHERE id = ?", (visita_id,)
        )
        if not visita:
            print(f"[ERRORE] Visita con ID {visita_id} non trovata.")
            return
        if visita["medico_id"] != self.medico["id"]:
            print("[ERRORE] Questa visita non è assegnata a te.")
            return
        nid = app_db.execute(
            "INSERT INTO referti (visita_id, data_rilascio, contenuto)"
            " VALUES (?, ?, ?)",
            (visita_id, data_rilascio, contenuto),
        )
        print(f"[OK] Referto aggiunto con ID {nid}.")

    def cmd_nuova_prescrizione(self, args):
        if len(args) < 4:
            print("[ERRORE] Uso: nuova-prescrizione <paziente_id> <farmaco> <dose> <data>")
            return
        try:
            paziente_id = int(args[0])
        except ValueError:
            print("[ERRORE] paziente_id deve essere un numero intero.")
            return
        farmaco, dose, data_emissione = args[1], args[2], args[3]
        if not app_db.query_one("SELECT id FROM pazienti WHERE id = ?", (paziente_id,)):
            print(f"[ERRORE] Paziente con ID {paziente_id} non trovato.")
            return
        nid = app_db.execute(
            "INSERT INTO prescrizioni"
            " (medico_id, paziente_id, farmaco, dose, data_emissione)"
            " VALUES (?, ?, ?, ?, ?)",
            (self.medico["id"], paziente_id, farmaco, dose, data_emissione),
        )
        print(f"[OK] Prescrizione aggiunta con ID {nid}.")

    def cmd_statistiche(self, args):
        mid = self.medico["id"]
        nv  = app_db.query_one("SELECT COUNT(*) FROM visite WHERE medico_id = ?", (mid,))["COUNT(*)"]
        nr  = app_db.query_one(
            "SELECT COUNT(*) FROM referti rf"
            " JOIN visite v ON v.id = rf.visita_id WHERE v.medico_id = ?", (mid,)
        )["COUNT(*)"]
        np_ = app_db.query_one(
            "SELECT COUNT(*) FROM prescrizioni WHERE medico_id = ?", (mid,)
        )["COUNT(*)"]
        print(f"Visite:         {nv}")
        print(f"Referti emessi: {nr}")
        print(f"Prescrizioni:   {np_}")

    def cmd_help(self, args):
        righe = [
            ("visite",                                               "Le mie visite"),
            ("nuovo-referto <vis_id> <data> [<contenuto>]",         "Aggiunge un referto"),
            ("nuova-prescrizione <paz_id> <farmaco> <dose> <data>", "Aggiunge una prescrizione"),
            ("statistiche",                                          "Le mie statistiche"),
            ("help",                                                 "Mostra questo messaggio"),
            ("esci",                                                 "Esce dal programma"),
        ]
        for cmd, desc in righe:
            print(f"  {cmd}: {desc}")

    def esegui(self):
        print(f"[Medico] Dr. {self.medico['nome']} {self.medico['cognome']}"
              f" — {self.medico['reparto']}")
        print("Digita 'help' per i comandi.")
        comandi = {
            "visite":             self.cmd_visite,
            "nuovo-referto":      self.cmd_nuovo_referto,
            "nuova-prescrizione": self.cmd_nuova_prescrizione,
            "statistiche":        self.cmd_statistiche,
            "help":               self.cmd_help,
        }
        while True:
            try:
                line = input("medico> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nArrivederci.")
                return
            if not line:
                continue
            parti = line.split()
            cmd, args = parti[0], parti[1:]
            if cmd == "esci":
                print("Arrivederci.")
                return
            handler = comandi.get(cmd)
            if handler:
                handler(args)
            else:
                print(f"[ERRORE] Comando '{cmd}' non riconosciuto. Digita 'help'.")


# ── PAZIENTE ──────────────────────────────────────────────────────────────────

class PazienteREPL:
    def __init__(self, paziente):
        self.paziente = paziente

    def cmd_visite(self, args):
        righe = app_db.query(
            _SQL_VISITA_FULL + " WHERE v.paziente_id = ? ORDER BY v.data DESC",
            (self.paziente["id"],),
        )
        if not righe:
            print("Nessuna visita.")
            return
        print("ID", "Medico", "Esame", "Reparto", "Data")
        for v in righe:
            print(v["id"], v["medico"], v["esame"], v["reparto"], v["data"])

    def cmd_referti(self, args):
        righe = app_db.query("""
            SELECT rf.id, rf.data_rilascio, rf.contenuto,
                   e.nome AS esame,
                   m.nome || ' ' || m.cognome AS medico
            FROM referti rf
            JOIN visite   v ON v.id = rf.visita_id
            JOIN esami    e ON e.id = v.esame_id
            JOIN medici   m ON m.id = v.medico_id
            WHERE v.paziente_id = ?
            ORDER BY rf.data_rilascio DESC
        """, (self.paziente["id"],))
        if not righe:
            print("Nessun referto.")
            return
        print("ID", "Data", "Esame", "Medico", "Contenuto")
        for r in righe:
            print(r["id"], r["data_rilascio"], r["esame"],
                  r["medico"], (r["contenuto"] or "-")[:40])

    def cmd_prescrizioni(self, args):
        righe = app_db.query("""
            SELECT pr.id, pr.farmaco, pr.dose, pr.data_emissione,
                   m.nome || ' ' || m.cognome AS medico
            FROM prescrizioni pr
            JOIN medici m ON m.id = pr.medico_id
            WHERE pr.paziente_id = ?
            ORDER BY pr.data_emissione DESC
        """, (self.paziente["id"],))
        if not righe:
            print("Nessuna prescrizione.")
            return
        print("ID", "Farmaco", "Dose", "Data", "Medico")
        for pr in righe:
            print(pr["id"], pr["farmaco"], pr["dose"],
                  pr["data_emissione"], pr["medico"])

    def cmd_help(self, args):
        righe = [
            ("visite",       "Le mie visite"),
            ("referti",      "I miei referti"),
            ("prescrizioni", "Le mie prescrizioni"),
            ("help",         "Mostra questo messaggio"),
            ("esci",         "Esce dal programma"),
        ]
        for cmd, desc in righe:
            print(f"  {cmd}: {desc}")

    def esegui(self):
        print(f"[Paziente] {self.paziente['nome']} {self.paziente['cognome']}")
        print("Digita 'help' per i comandi.")
        comandi = {
            "visite":       self.cmd_visite,
            "referti":      self.cmd_referti,
            "prescrizioni": self.cmd_prescrizioni,
            "help":         self.cmd_help,
        }
        while True:
            try:
                line = input("paziente> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nArrivederci.")
                return
            if not line:
                continue
            parti = line.split()
            cmd, args = parti[0], parti[1:]
            if cmd == "esci":
                print("Arrivederci.")
                return
            handler = comandi.get(cmd)
            if handler:
                handler(args)
            else:
                print(f"[ERRORE] Comando '{cmd}' non riconosciuto. Digita 'help'.")


# ── DISPATCHER ────────────────────────────────────────────────────────────────

class AmbulatorioREPL:
    def __init__(self):
        pass

    def _seleziona_medico(self):
        medici = app_db.query(_SQL_MEDICO_FULL + " ORDER BY m.cognome, m.nome")
        print("\nMedici disponibili:")
        for m in medici:
            print(f"  [{m['id']}] Dr. {m['nome']} {m['cognome']} — {m['reparto']}")
        while True:
            try:
                raw = input("ID medico> ").strip()
            except (EOFError, KeyboardInterrupt):
                return None
            try:
                mid = int(raw)
            except ValueError:
                print("[ERRORE] Inserisci un numero intero.")
                continue
            m = app_db.query_one(_SQL_MEDICO_FULL + " WHERE m.id = ?", (mid,))
            if m:
                return m
            print(f"[ERRORE] Medico con ID {mid} non trovato.")

    def _seleziona_paziente(self):
        pazienti = app_db.query(
            "SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome"
        )
        print("\nPazienti disponibili:")
        for p in pazienti:
            print(f"  [{p['id']}] {p['nome']} {p['cognome']}")
        while True:
            try:
                raw = input("ID paziente> ").strip()
            except (EOFError, KeyboardInterrupt):
                return None
            try:
                pid = int(raw)
            except ValueError:
                print("[ERRORE] Inserisci un numero intero.")
                continue
            p = app_db.query_one(
                "SELECT id, nome, cognome FROM pazienti WHERE id = ?", (pid,)
            )
            if p:
                return p
            print(f"[ERRORE] Paziente con ID {pid} non trovato.")

    def esegui(self):
        print("=== Gestionale Ambulatorio Medico ===")
        print()
        print("Seleziona ruolo:")
        print("  1. Segreteria")
        print("  2. Medico")
        print("  3. Paziente")
        while True:
            try:
                scelta = input("ruolo> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nArrivederci.")
                return
            if scelta in ("1", "segreteria"):
                SegretariaREPL().esegui()
                return
            if scelta in ("2", "medico"):
                medico = self._seleziona_medico()
                if medico:
                    MedicoREPL(medico).esegui()
                return
            if scelta in ("3", "paziente"):
                paziente = self._seleziona_paziente()
                if paziente:
                    PazienteREPL(paziente).esegui()
                return
            if scelta in ("esci", "q"):
                print("Arrivederci.")
                return
            print("[ERRORE] Digita 1, 2 o 3.")
