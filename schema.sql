CREATE TABLE IF NOT EXISTS pazienti (
    id             INTEGER PRIMARY KEY,
    nome           TEXT NOT NULL,
    cognome        TEXT NOT NULL,
    data_nascita   TEXT,
    codice_fiscale TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS reparti (
    id   INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS medici (
    id         INTEGER PRIMARY KEY,
    nome       TEXT NOT NULL,
    cognome    TEXT NOT NULL,
    reparto_id INTEGER NOT NULL REFERENCES reparti(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS esami (
    id         INTEGER PRIMARY KEY,
    nome       TEXT NOT NULL,
    reparto_id INTEGER NOT NULL REFERENCES reparti(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS visite (
    id          INTEGER PRIMARY KEY,
    paziente_id INTEGER NOT NULL REFERENCES pazienti(id) ON DELETE CASCADE,
    medico_id   INTEGER NOT NULL REFERENCES medici(id)   ON DELETE RESTRICT,
    esame_id    INTEGER NOT NULL REFERENCES esami(id)    ON DELETE RESTRICT,
    data        TEXT NOT NULL,
    note        TEXT
);

CREATE TABLE IF NOT EXISTS referti (
    id            INTEGER PRIMARY KEY,
    visita_id     INTEGER NOT NULL REFERENCES visite(id) ON DELETE CASCADE,
    data_rilascio TEXT NOT NULL,
    contenuto     TEXT
);

CREATE TABLE IF NOT EXISTS prescrizioni (
    id             INTEGER PRIMARY KEY,
    medico_id      INTEGER NOT NULL REFERENCES medici(id)   ON DELETE RESTRICT,
    paziente_id    INTEGER NOT NULL REFERENCES pazienti(id) ON DELETE CASCADE,
    farmaco        TEXT NOT NULL,
    dose           TEXT NOT NULL,
    data_emissione TEXT NOT NULL
);
