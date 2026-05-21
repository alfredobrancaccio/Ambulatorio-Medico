INSERT INTO pazienti (id, nome, cognome) VALUES
    (1, 'Luca',    'Rossi'),
    (2, 'Maria',   'Bianchi'),
    (3, 'Giulia',  'Conti'),
    (4, 'Roberto', 'Marini'),
    (5, 'Chiara',  'Esposito'),
    (6, 'Antonio', 'Ferrara')
ON CONFLICT (id) DO NOTHING;

INSERT INTO medici (id, nome, cognome, reparto) VALUES
    (1, 'Andrea',   'Verdi',   'Cardiologia'),
    (2, 'Sara',     'Neri',    'Dermatologia'),
    (3, 'Paolo',    'Galli',   'Ginecologia'),
    (4, 'Elena',    'Ferrari', 'Endocrinologia'),
    (5, 'Marco',    'Bruno',   'Medicina dello Sport'),
    (6, 'Federica', 'Mancini', 'Trasfusionale')
ON CONFLICT (id) DO NOTHING;

INSERT INTO esami (id, nome, reparto) VALUES
    (1, 'Elettrocardiogramma', 'Cardiologia'),
    (2, 'Visita dei nei',      'Dermatologia'),
    (3, 'PAP test',            'Ginecologia'),
    (4, 'Curva glicemica',     'Trasfusionale'),
    (5, 'Idoneita sportiva',   'Medicina dello Sport'),
    (6, 'Ecografia tiroidea',  'Endocrinologia')
ON CONFLICT (id) DO NOTHING;

INSERT INTO appuntamenti (id, paziente_id, medico_id, esame_id, data) VALUES
    (1, 1, 1, 1, '2026-05-10'),
    (2, 2, 2, 2, '2026-05-11'),
    (3, 3, 3, 3, '2026-05-12'),
    (4, 4, 4, 6, '2026-05-13'),
    (5, 5, 5, 5, '2026-05-14'),
    (6, 6, 6, 4, '2026-05-15')
ON CONFLICT (id) DO NOTHING;

INSERT INTO referti (id, data_rilascio, appuntamento_id) VALUES
    (1, '2026-05-13', 1),
    (2, '2026-05-14', 2),
    (3, '2026-05-15', 3),
    (4, '2026-05-20', 4),
    (5, '2026-05-21', 5),
    (6, '2026-05-22', 6)
ON CONFLICT (id) DO NOTHING;

INSERT INTO prescrizioni (id, medico_id, paziente_id, farmaco, dose, data_emissione) VALUES
    (1, 1, 1, 'Aspirina',   '100mg/die',        '2026-05-10'),
    (2, 2, 2, 'Cortisone',  '5mg 2x/die',       '2026-05-11'),
    (3, 3, 3, 'Ibuprofene', '400mg al bisogno', '2026-05-12'),
    (4, 4, 4, 'Metformina', '500mg/die',        '2026-05-13'),
    (5, 5, 5, 'Magnesio',   '300mg/die',        '2026-05-14'),
    (6, 6, 6, 'Eparina',    '5000UI/die',       '2026-05-15')
ON CONFLICT (id) DO NOTHING;

SELECT setval('pazienti_id_seq',     (SELECT MAX(id) FROM pazienti));
SELECT setval('medici_id_seq',       (SELECT MAX(id) FROM medici));
SELECT setval('esami_id_seq',        (SELECT MAX(id) FROM esami));
SELECT setval('appuntamenti_id_seq', (SELECT MAX(id) FROM appuntamenti));
SELECT setval('referti_id_seq',      (SELECT MAX(id) FROM referti));
SELECT setval('prescrizioni_id_seq', (SELECT MAX(id) FROM prescrizioni));
