# Gestionale Ambulatorio Medico

Applicazione Python per la gestione di un ambulatorio medico. Supporta due modalità di utilizzo: interfaccia web (Flask) e REPL da terminale.

## Requisiti

- Python 3.10+
- Flask (installabile tramite `requirements.txt`)

## Installazione

```bash
pip install -r requirements.txt
```

## Avvio

```bash
# REPL da terminale
python main.py

# Interfaccia web (http://127.0.0.1:5000)
python main.py --web

# Prima esecuzione: crea il database con i dati di esempio
python main.py --reset --web
```

> Il flag `--reset` va usato la prima volta per inizializzare il database. Le volte successive basta `python main.py --web`.

## Struttura dei file

```
├── main.py          # Punto di ingresso
├── app_db.py        # Accesso al database (SQLite)
├── app_web.py       # Applicazione Flask (routes e logica web)
├── app_repl.py      # Interfaccia REPL da terminale
├── schema.sql       # Definizione delle tabelle
├── seed.sql         # Dati iniziali di esempio
├── requirements.txt # Dipendenze Python
├── templates/       # Template HTML Jinja2
├── static/          # Foglio di stile CSS personalizzato (style.css)
└── runtime/         # Cartella creata automaticamente, contiene ambulatorio.db
```

## Schema del database

| Tabella | Descrizione |
|---|---|
| `pazienti` | Anagrafica pazienti (nome, cognome, data nascita, codice fiscale) |
| `reparti` | Reparti dell'ambulatorio |
| `medici` | Medici, ciascuno assegnato a un reparto |
| `esami` | Esami disponibili, ciascuno associato a un reparto |
| `visite` | Prenotazioni: paziente + medico + esame + data |
| `referti` | Referti collegati a una visita |
| `prescrizioni` | Farmaci prescritti da un medico a un paziente |

Ogni esame può essere eseguito solo da un medico dello stesso reparto. Questa regola è applicata sia lato server che nell'interfaccia web (filtro dinamico JS).

## Tre ruoli

### Segreteria (`/segreteria`)
Accesso completo in lettura e scrittura a tutte le entità: pazienti, reparti, medici, esami, visite, referti, prescrizioni. Dashboard con contatori globali.

### Medico (`/medico`)
Accesso al proprio profilo. Visualizza le proprie visite, può emettere referti per le visite assegnate e aggiungere prescrizioni.

### Paziente (`/paziente`)
Accesso in sola lettura al proprio storico: visite, referti e prescrizioni.

## Interfaccia web

L'interfaccia web è costruita con Flask e Jinja2 per il rendering dinamico dei template HTML. Lo stile grafico è realizzato con un foglio CSS personalizzato senza dipendenze esterne da framework come Bootstrap.

## Interfaccia REPL

```
=== Gestionale Ambulatorio Medico ===
Seleziona ruolo:
  1. Segreteria
  2. Medico
  3. Paziente
```

Ogni ruolo espone comandi testuali. Digita `help` per la lista dei comandi disponibili nel ruolo corrente.
