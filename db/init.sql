CREATE TABLE IF NOT EXISTS tabela_catserv (
    id SERIAL PRIMARY KEY,
    exame VARCHAR(100) NOT NULL UNIQUE,
    codigo VARCHAR(20) NOT NULL,
    valor NUMERIC(10,2) NOT NULL,
    descricao TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO tabela_catserv (exame, codigo, valor, descricao) VALUES
    ('Hemograma', '01.01.001', 12.50, 'Hemograma completo'),
    ('Urocultura', '02.03.010', 35.00, 'Urocultura'),
    ('Glicemia', '03.02.005', 8.90, 'Glicemia em jejum'),
    ('Colesterol Total', '04.01.001', 15.00, 'Colesterol total'),
    ('Colesterol HDL', '04.01.002', 18.00, 'Colesterol HDL'),
    ('Triglicerideos', '04.02.001', 14.00, 'Triglicerideos'),
    ('Creatinina', '05.01.001', 10.00, 'Creatinina'),
    ('Urcia', '05.02.001', 10.00, 'Ureia'),
    ('TGO/AST', '06.01.001', 11.00, 'Transaminase glutâmico oxalacética'),
    ('TGP/ALT', '06.01.002', 11.00, 'Transaminase glutâmico pirúvica')
ON CONFLICT (exame) DO NOTHING;
