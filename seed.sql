INSERT INTO reparti (id, nome) VALUES
    (1, 'Cardiologia'),
    (2, 'Dermatologia'),
    (3, 'Ginecologia'),
    (4, 'Endocrinologia'),
    (5, 'Medicina dello Sport'),
    (6, 'Trasfusionale')
ON CONFLICT (id) DO NOTHING;

INSERT INTO pazienti (id, nome, cognome, data_nascita, codice_fiscale) VALUES
    (1, 'Luca',    'Rossi',    '1985-03-12', 'RSSLCU85C12H501A'),
    (2, 'Maria',   'Bianchi',  '1990-07-22', 'BNCMRA90L62H501B'),
    (3, 'Giulia',  'Conti',    '1978-11-05', 'CNTGLI78S45H501C'),
    (4, 'Roberto', 'Marini',   '1965-01-30', 'MRNRRT65A30H501D'),
    (5, 'Chiara',  'Esposito', '2000-09-14', 'SPSCHR00P54H501E'),
    (6, 'Antonio', 'Ferrara',  '1958-06-20', 'FRRNTN58H20H501F')
ON CONFLICT (id) DO NOTHING;

INSERT INTO medici (id, nome, cognome, reparto_id) VALUES
    (1, 'Andrea',   'Verdi',   1),
    (2, 'Sara',     'Neri',    2),
    (3, 'Paolo',    'Galli',   3),
    (4, 'Elena',    'Ferrari', 4),
    (5, 'Marco',    'Bruno',   5),
    (6, 'Federica', 'Mancini', 6)
ON CONFLICT (id) DO NOTHING;

INSERT INTO esami (id, nome, reparto_id) VALUES
    (1, 'Elettrocardiogramma', 1),
    (2, 'Visita dei nei',      2),
    (3, 'PAP test',            3),
    (4, 'Ecografia tiroidea',  4),
    (5, 'Idoneita sportiva',   5),
    (6, 'Curva glicemica',     6)
ON CONFLICT (id) DO NOTHING;

INSERT INTO visite (id, paziente_id, medico_id, esame_id, data, note) VALUES
    (1, 1, 1, 1, '2026-05-10', NULL),
    (2, 2, 2, 2, '2026-05-11', NULL),
    (3, 3, 3, 3, '2026-05-12', NULL),
    (4, 4, 4, 4, '2026-05-13', NULL),
    (5, 5, 5, 5, '2026-05-14', NULL),
    (6, 6, 6, 6, '2026-05-15', NULL)
ON CONFLICT (id) DO NOTHING;

INSERT INTO referti (id, visita_id, data_rilascio, contenuto) VALUES
    (1, 1, '2026-05-13', 'Ritmo sinusale regolare.'),
    (2, 2, '2026-05-14', 'Nessuna lesione sospetta.'),
    (3, 3, '2026-05-15', 'Esito negativo.'),
    (4, 4, '2026-05-20', 'Tiroide nei limiti.'),
    (5, 5, '2026-05-21', 'Idoneita concessa.'),
    (6, 6, '2026-05-22', 'Glicemia nella norma.')
ON CONFLICT (id) DO NOTHING;

INSERT INTO prescrizioni (id, medico_id, paziente_id, farmaco, dose, data_emissione) VALUES
    (1, 1, 1, 'Aspirina',   '100mg/die',        '2026-05-10'),
    (2, 2, 2, 'Cortisone',  '5mg 2x/die',       '2026-05-11'),
    (3, 3, 3, 'Ibuprofene', '400mg al bisogno', '2026-05-12'),
    (4, 4, 4, 'Metformina', '500mg/die',        '2026-05-13'),
    (5, 5, 5, 'Magnesio',   '300mg/die',        '2026-05-14'),
    (6, 6, 6, 'Eparina',    '5000UI/die',       '2026-05-15')
ON CONFLICT (id) DO NOTHING;
