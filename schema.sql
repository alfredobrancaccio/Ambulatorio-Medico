CREATE TABLE IF NOT EXISTS pazienti (
    id      SERIAL PRIMARY KEY,
    nome    TEXT NOT NULL,
    cognome TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS medici (
    id      SERIAL PRIMARY KEY,
    nome    TEXT NOT NULL,
    cognome TEXT NOT NULL,
    reparto TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS esami (
    id      SERIAL PRIMARY KEY,
    nome    TEXT NOT NULL,
    reparto TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS appuntamenti (
    id          SERIAL PRIMARY KEY,
    paziente_id INTEGER NOT NULL REFERENCES pazienti(id) ON DELETE CASCADE,
    medico_id   INTEGER NOT NULL REFERENCES medici(id)   ON DELETE CASCADE,
    esame_id    INTEGER NOT NULL REFERENCES esami(id)    ON DELETE CASCADE,
    data        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS referti (
    id              SERIAL PRIMARY KEY,
    data_rilascio   TEXT NOT NULL,
    appuntamento_id INTEGER NOT NULL REFERENCES appuntamenti(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS prescrizioni (
    id             SERIAL PRIMARY KEY,
    medico_id      INTEGER NOT NULL REFERENCES medici(id)   ON DELETE CASCADE,
    paziente_id    INTEGER NOT NULL REFERENCES pazienti(id) ON DELETE CASCADE,
    farmaco        TEXT NOT NULL,
    dose           TEXT NOT NULL,
    data_emissione TEXT NOT NULL
);
