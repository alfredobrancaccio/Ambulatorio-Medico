class AmbulatorioREPL:
    def __init__(self, db):
        self.db = db

    # ── tabelle ───────────────────────────────────────────────────────────────

    def cmd_pazienti(self, args):
        print("ID", "Nome", "Cognome")
        for p in self.db.query("SELECT id, nome, cognome FROM pazienti ORDER BY cognome, nome"):
            print(p["id"], p["nome"], p["cognome"])

    def cmd_medici(self, args):
        print("ID", "Nome", "Cognome", "Reparto")
        for m in self.db.query("SELECT id, nome, cognome, reparto FROM medici ORDER BY cognome, nome"):
            print(m["id"], m["nome"], m["cognome"], m["reparto"])

    def cmd_esami(self, args):
        print("ID", "Nome", "Reparto")
        for e in self.db.query("SELECT id, nome, reparto FROM esami ORDER BY reparto, nome"):
            print(e["id"], e["nome"], e["reparto"])

    def cmd_appuntamenti(self, args):
        print("ID", "Paziente", "Medico", "Esame", "Data")
        righe = self.db.query("""
            SELECT a.id, a.data,
                   p.nome || ' ' || p.cognome AS paziente,
                   m.nome || ' ' || m.cognome AS medico,
                   e.nome AS esame
            FROM appuntamenti a
            JOIN pazienti p ON p.id = a.paziente_id
            JOIN medici   m ON m.id = a.medico_id
            JOIN esami    e ON e.id = a.esame_id
            ORDER BY a.data DESC, a.id
        """)
        for a in righe:
            print(a["id"], a["paziente"], a["medico"], a["esame"], a["data"])

    def cmd_referti(self, args):
        righe = self.db.query("""
            SELECT r.id, r.data_rilascio,
                   p.nome || ' ' || p.cognome AS paziente,
                   e.nome AS esame
            FROM referti r
            JOIN appuntamenti a ON a.id = r.appuntamento_id
            JOIN pazienti     p ON p.id = a.paziente_id
            JOIN esami        e ON e.id = a.esame_id
            ORDER BY r.data_rilascio DESC, r.id
        """)
        if not righe:
            print("Nessun referto presente.")
            return
        print("ID", "Data rilascio", "Paziente", "Esame")
        for r in righe:
            print(r["id"], r["data_rilascio"], r["paziente"], r["esame"])

    def cmd_prescrizioni(self, args):
        righe = self.db.query("""
            SELECT pr.id, pr.farmaco, pr.dose, pr.data_emissione,
                   m.nome || ' ' || m.cognome AS medico,
                   p.nome || ' ' || p.cognome AS paziente
            FROM prescrizioni pr
            JOIN medici   m ON m.id = pr.medico_id
            JOIN pazienti p ON p.id = pr.paziente_id
            ORDER BY pr.data_emissione DESC, pr.id
        """)
        if not righe:
            print("Nessuna prescrizione presente.")
            return
        print("ID", "Medico", "Paziente", "Farmaco", "Dose", "Data")
        for pr in righe:
            print(pr["id"], pr["medico"], pr["paziente"],
                  pr["farmaco"], pr["dose"], pr["data_emissione"])

    # ── mutazioni ─────────────────────────────────────────────────────────────

    def cmd_nuovo_paziente(self, args):
        if len(args) != 2:
            print("[ERRORE] Uso: nuovo-paziente <Nome> <Cognome>")
            return
        nome, cognome = args
        nid = self.db.execute(
            "INSERT INTO pazienti (nome, cognome) VALUES (?, ?) RETURNING id",
            (nome, cognome),
        )
        print(f"[OK] Paziente aggiunto con ID {nid}.")

    def cmd_nuovo_appuntamento(self, args):
        if len(args) != 4:
            print("[ERRORE] Uso: nuovo-appuntamento <medico_id> <paziente_id> <data> <esame_id>")
            return
        try:
            medico_id   = int(args[0])
            paziente_id = int(args[1])
            data        = args[2]
            esame_id    = int(args[3])
        except ValueError:
            print("[ERRORE] Gli ID devono essere numeri interi.")
            return

        medico = self.db.query_one("SELECT * FROM medici WHERE id = ?", (medico_id,))
        if not medico:
            print(f"[ERRORE] Medico con ID {medico_id} non trovato.")
            return
        if not self.db.query_one("SELECT id FROM pazienti WHERE id = ?", (paziente_id,)):
            print(f"[ERRORE] Paziente con ID {paziente_id} non trovato.")
            return
        esame = self.db.query_one("SELECT * FROM esami WHERE id = ?", (esame_id,))
        if not esame:
            print(f"[ERRORE] Esame con ID {esame_id} non trovato.")
            return
        if esame["reparto"] != medico["reparto"]:
            print(
                f"[ERRORE] L'esame '{esame['nome']}' ({esame['reparto']}) "
                f"non appartiene al reparto del medico "
                f"'{medico['nome']} {medico['cognome']}' ({medico['reparto']})."
            )
            return

        nid = self.db.execute(
            "INSERT INTO appuntamenti (paziente_id, medico_id, esame_id, data)"
            " VALUES (?, ?, ?, ?) RETURNING id",
            (paziente_id, medico_id, esame_id, data),
        )
        print(f"[OK] Appuntamento aggiunto con ID {nid}.")

    def cmd_nuovo_referto(self, args):
        if len(args) != 2:
            print("[ERRORE] Uso: nuovo-referto <data_rilascio> <appuntamento_id>")
            return
        data_rilascio = args[0]
        try:
            appuntamento_id = int(args[1])
        except ValueError:
            print("[ERRORE] L'ID appuntamento deve essere un numero intero.")
            return
        if not self.db.query_one("SELECT id FROM appuntamenti WHERE id = ?", (appuntamento_id,)):
            print(f"[ERRORE] Appuntamento con ID {appuntamento_id} non trovato.")
            return
        nid = self.db.execute(
            "INSERT INTO referti (data_rilascio, appuntamento_id) VALUES (?, ?) RETURNING id",
            (data_rilascio, appuntamento_id),
        )
        print(f"[OK] Referto aggiunto con ID {nid}.")

    def cmd_nuova_prescrizione(self, args):
        if len(args) != 5:
            print("[ERRORE] Uso: nuova-prescrizione <medico_id> <paziente_id> <farmaco> <dose> <data>")
            return
        try:
            medico_id   = int(args[0])
            paziente_id = int(args[1])
        except ValueError:
            print("[ERRORE] Gli ID devono essere numeri interi.")
            return
        farmaco, dose, data_emissione = args[2], args[3], args[4]
        if not self.db.query_one("SELECT id FROM medici WHERE id = ?", (medico_id,)):
            print(f"[ERRORE] Medico con ID {medico_id} non trovato.")
            return
        if not self.db.query_one("SELECT id FROM pazienti WHERE id = ?", (paziente_id,)):
            print(f"[ERRORE] Paziente con ID {paziente_id} non trovato.")
            return
        nid = self.db.execute(
            "INSERT INTO prescrizioni (medico_id, paziente_id, farmaco, dose, data_emissione)"
            " VALUES (?, ?, ?, ?, ?) RETURNING id",
            (medico_id, paziente_id, farmaco, dose, data_emissione),
        )
        print(f"[OK] Prescrizione aggiunta con ID {nid}.")

    # ── help ──────────────────────────────────────────────────────────────────

    def cmd_help(self, args):
        righe = [
            ("pazienti",                                              "Elenca tutti i pazienti"),
            ("medici",                                                "Elenca tutti i medici"),
            ("esami",                                                 "Elenca tutti gli esami"),
            ("appuntamenti",                                          "Elenca tutti gli appuntamenti"),
            ("referti",                                               "Elenca tutti i referti"),
            ("prescrizioni",                                          "Elenca tutte le prescrizioni"),
            ("nuovo-paziente <Nome> <Cognome>",                       "Aggiunge un paziente"),
            ("nuovo-appuntamento <med_id> <paz_id> <data> <esame_id>","Aggiunge un appuntamento"),
            ("nuovo-referto <data_rilascio> <appuntamento_id>",       "Aggiunge un referto"),
            ("nuova-prescrizione <med_id> <paz_id> <farmaco> <dose> <data>",
                                                                      "Aggiunge una prescrizione"),
            ("help",                                                   "Mostra questo messaggio"),
            ("esci",                                                   "Esce dal programma"),
        ]
        for cmd, desc in righe:
            print(f"  {cmd}: {desc}")

    # ── REPL ──────────────────────────────────────────────────────────────────

    def esegui(self):
        print("=== Gestionale Ambulatorio Medico ===")
        print("Digita 'help' per vedere i comandi disponibili.")

        comandi = {
            "pazienti":            self.cmd_pazienti,
            "medici":              self.cmd_medici,
            "esami":               self.cmd_esami,
            "appuntamenti":        self.cmd_appuntamenti,
            "referti":             self.cmd_referti,
            "prescrizioni":        self.cmd_prescrizioni,
            "nuovo-paziente":      self.cmd_nuovo_paziente,
            "nuovo-appuntamento":  self.cmd_nuovo_appuntamento,
            "nuovo-referto":       self.cmd_nuovo_referto,
            "nuova-prescrizione":  self.cmd_nuova_prescrizione,
            "help":                self.cmd_help,
        }

        while True:
            try:
                line = input("ambulatorio> ").strip()
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
