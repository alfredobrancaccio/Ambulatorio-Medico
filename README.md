# 🏥 Ambulatorio Medico

Sistema gestionale per ambulatori medici sviluppato in Python. Permette di gestire pazienti, medici, reparti, visite, referti e prescrizioni tramite due interfacce: una **web** (Flask) e una **REPL** da terminale.

---

## Funzionalità

Il sistema è organizzato attorno a tre ruoli principali:

**Segreteria** — gestione completa dell'anagrafica e delle operazioni amministrative:
- Pazienti (inserimento, modifica, eliminazione)
- Reparti e medici
- Esami (associati a un reparto)
- Visite (con validazione reparto medico/esame)
- Referti e prescrizioni

**Medico** — vista personalizzata per ogni medico:
- Riepilogo delle proprie visite e prescrizioni
- Creazione di nuovi referti e prescrizioni

**Paziente** — consultazione della propria cartella clinica:
- Storico visite, referti e prescrizioni ricevute

---

## Struttura del progetto

```
Ambulatorio-Medico/
├── main.py           # Entry point: avvia modalità web o REPL
├── app_db.py         # Livello database (connessione, query, inizializzazione)
├── app_web.py        # Applicazione Flask con tutte le route
├── app_repl.py       # Interfaccia interattiva da terminale
├── schema.sql        # Definizione delle tabelle
├── seed.sql          # Dati di esempio
├── templates/        # Template HTML (Jinja2)
└── requirements.txt  # Dipendenze Python
```

---

## Schema del database

Il database PostgreSQL contiene le seguenti tabelle:

| Tabella        | Descrizione                                      |
|----------------|--------------------------------------------------|
| `pazienti`     | Anagrafica dei pazienti (CF univoco)             |
| `reparti`      | Reparti dell'ambulatorio                         |
| `medici`       | Medici, ciascuno associato a un reparto          |
| `esami`        | Tipi di esame, ciascuno associato a un reparto   |
| `visite`       | Visite (paziente + medico + esame + data)        |
| `referti`      | Referti collegati a una visita                   |
| `prescrizioni` | Prescrizioni emesse da un medico per un paziente |

> **Regola di integrità:** un medico può prescrivere solo esami del proprio reparto.

---

## Requisiti

- Python 3.10+
- PostgreSQL
- Dipendenze Python (vedere `requirements.txt`):
  - `Flask >= 3.0, < 4`
  - `psycopg[binary] >= 3.1, < 4`

---

## Installazione e avvio

### 1. Clona la repository

```bash
git clone https://github.com/blumaggy-hub/Ambulatorio-Medico.git
cd Ambulatorio-Medico
```

### 2. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 3. Configura il database

Assicurati di avere PostgreSQL attivo e accessibile, quindi imposta la variabile d'ambiente per la connessione:

```bash
export DATABASE_URL="postgresql://utente:password@localhost/ambulatorio"
```

### 4. Avvia l'applicazione

**Modalità web (Flask):**

```bash
python main.py --web
```

L'app sarà disponibile su `http://127.0.0.1:5000`.

**Modalità terminale (REPL):**

```bash
python main.py
```

**Reset del database** (ricrea le tabelle e ricarica i dati seed):

```bash
python main.py --reset
# oppure con interfaccia web
python main.py --web --reset
```

---

## Variabili d'ambiente

| Variabile      | Descrizione                                         | Default                      |
|----------------|-----------------------------------------------------|------------------------------|
| `DATABASE_URL` | URL di connessione PostgreSQL                       | *(obbligatoria)*             |
| `SECRET_KEY`   | Chiave segreta per le sessioni Flask                | `dev-secret-ambulatorio`     |

---

## Route principali (interfaccia web)

| Percorso                        | Descrizione                          |
|---------------------------------|--------------------------------------|
| `/`                             | Homepage                             |
| `/segreteria`                   | Dashboard segreteria con statistiche |
| `/segreteria/pazienti`          | Gestione pazienti                    |
| `/segreteria/medici`            | Gestione medici                      |
| `/segreteria/reparti`           | Gestione reparti                     |
| `/segreteria/esami`             | Gestione esami                       |
| `/segreteria/visite`            | Gestione visite                      |
| `/segreteria/referti`           | Gestione referti                     |
| `/segreteria/prescrizioni`      | Gestione prescrizioni                |
| `/medico`                       | Selezione medico                     |
| `/medico/<id>`                  | Dashboard medico                     |
| `/paziente`                     | Selezione paziente                   |
| `/paziente/<id>`                | Cartella clinica del paziente        |

---

## Tecnologie utilizzate

- **Python** — linguaggio principale
- **Flask** — framework web
- **PostgreSQL** — database relazionale
- **psycopg3** — driver PostgreSQL per Python
- **Jinja2** — template engine HTML (incluso in Flask)
- **SQL** — schema e query native (nessun ORM)
